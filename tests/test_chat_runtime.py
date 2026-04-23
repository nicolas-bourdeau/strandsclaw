from __future__ import annotations

from pathlib import Path

import pytest

from strandsclaw.bootstrap.init import BootstrapError
from strandsclaw.config import AppConfig, ModelProfile
from strandsclaw.interfaces import cli


def _seed_workspace(workspace_root: Path, template_root: Path) -> None:
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "AGENTS.md").write_text("# AGENTS\nBe helpful.", encoding="utf-8")
    (workspace_root / "BOOTSTRAP.md").write_text("# BOOTSTRAP\nInitialize carefully.", encoding="utf-8")
    (workspace_root / "IDENTITY.md").write_text("# IDENTITY\nYou are StrandsClaw.", encoding="utf-8")
    (workspace_root / "SOUL.md").write_text("# SOUL\nStay concise.", encoding="utf-8")

    for filename in ("AGENTS.md", "BOOTSTRAP.md", "IDENTITY.md", "SOUL.md"):
        (template_root / filename).parent.mkdir(parents=True, exist_ok=True)
        (template_root / filename).write_text(f"# {filename}\n", encoding="utf-8")

    (template_root / "skills" / "system").mkdir(parents=True, exist_ok=True)
    (template_root / "skills" / "system" / "SKILL.md").write_text("# System", encoding="utf-8")


def _make_config(tmp_path: Path) -> AppConfig:
    workspace_root = tmp_path / "workspace"
    template_root = tmp_path / "workspace-template"
    _seed_workspace(workspace_root, template_root)
    return AppConfig(
        repo_root=tmp_path,
        workspace_root=workspace_root,
        workspace_template_dir=template_root,
        skills_dir=workspace_root / "skills",
        state_dir=workspace_root / ".state",
        model_profile=ModelProfile(provider="ollama", model="qwen3.5:latest", context_window=65536),
    )


def test_chat_prompt_response_flow_and_session_persist(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "Acknowledged")

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "assistant> Acknowledged" in output

    state_path = config.state_dir / "assistant_session.json"
    assert state_path.exists()


def test_chat_resumes_existing_session_between_runs(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "ok")

    first = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])
    second = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "again"])

    assert first == 0
    assert second == 0

    state_store = cli.FileStateStore(config.state_dir)
    payload = state_store.read("assistant_session")
    assert len(payload["messages"]) == 4


def test_model_unavailable_returns_actionable_turn_error(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)

    def _raise(*_):
        raise cli.ModelUnavailableError("connection refused")

    monkeypatch.setattr(cli, "_generate_with_ollama", _raise)

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Model unavailable:" in output
    assert "Verify Ollama is running" in output


def test_chat_emits_structured_runtime_events(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    events: list[str] = []

    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "ok")

    original_emit = cli.RuntimeEventLogger.emit

    def _capture(self, event: str, **fields):
        events.append(event)
        return original_emit(self, event, **fields)

    monkeypatch.setattr(cli.RuntimeEventLogger, "emit", _capture)

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    assert "tool.registered" in events
    assert "workspace.bootstrap" in events
    assert "session.loaded" in events
    assert "chat.turn_succeeded" in events
    assert "session.saved" in events


def test_chat_bootstraps_missing_workspace_and_reports_it(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    if config.workspace_root.exists():
        for path in sorted(config.workspace_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        config.workspace_root.rmdir()

    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "ok")

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "workspace> bootstrapped" in output
    assert (config.workspace_root / "AGENTS.md").exists()
    assert (config.workspace_root / "BOOTSTRAP.md").exists()


def test_bootstrap_instructions_are_used_only_when_bootstrap_is_required(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    calls: list[str] = []

    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "ok")
    monkeypatch.setattr(
        cli,
        "load_bootstrap_instructions",
        lambda workspace_root: calls.append(str(workspace_root)) or "bootstrap notes",
    )

    first = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])
    second = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello again"])

    assert first == 0
    assert second == 0
    assert calls == []

    (config.workspace_root / "SOUL.md").unlink()
    third = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "repair"])

    assert third == 0
    assert calls == [str(config.workspace_root)]


def test_chat_reports_actionable_bootstrap_failure_and_exits_nonzero(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)

    def _raise(_config):
        raise BootstrapError("workspace creation failed for /tmp/example during mkdir: permission denied")

    monkeypatch.setattr(cli, "bootstrap_workspace", _raise)

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Bootstrap failed:" in output
    assert "permission denied" in output


def test_chat_includes_allowed_workspace_file_contents_in_prompt(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    (config.workspace_root / "notes.txt").write_text("important workspace note", encoding="utf-8")
    captured: dict[str, str] = {}

    monkeypatch.setattr(cli, "load_config", lambda **_: config)

    def _respond(_config, prompt: str) -> str:
        captured["prompt"] = prompt
        return "summary complete"

    monkeypatch.setattr(cli, "_generate_with_ollama", _respond)

    exit_code = cli.main([
        "--workspace-path",
        str(config.workspace_root),
        "chat",
        "--prompt",
        "Summarize notes.txt",
    ])

    assert exit_code == 0
    assert "important workspace note" in captured["prompt"]
    assert "assistant> summary complete" in capsys.readouterr().out


def test_chat_refuses_outside_boundary_file_read(tmp_path: Path, monkeypatch, capsys) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: pytest.fail("model should not be called"))

    exit_code = cli.main([
        "--workspace-path",
        str(config.workspace_root),
        "chat",
        "--prompt",
        "Read ../secret.txt",
    ])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Denied: requested path is outside the active workspace boundary." in output


def test_sc001_startup_from_missing_workspace_completes_under_60s(tmp_path: Path, monkeypatch, capsys) -> None:
    """SC-001: From an empty or missing workspace, the operator reaches the first assistant response
    in one start action and under 60 seconds, excluding external model download time."""
    import time

    # Use a workspace path that does not exist yet (empty/missing start state)
    workspace_root = tmp_path / "brand_new_workspace"
    template_root = tmp_path / "workspace-template"
    template_root.mkdir(parents=True, exist_ok=True)
    for filename in ("AGENTS.md", "BOOTSTRAP.md", "IDENTITY.md", "SOUL.md"):
        (template_root / filename).write_text(f"# {filename}\n", encoding="utf-8")
    (template_root / "skills" / "system").mkdir(parents=True, exist_ok=True)
    (template_root / "skills" / "system" / "SKILL.md").write_text("# System", encoding="utf-8")

    config = AppConfig(
        repo_root=tmp_path,
        workspace_root=workspace_root,
        workspace_template_dir=template_root,
        skills_dir=workspace_root / "skills",
        state_dir=workspace_root / ".state",
        model_profile=ModelProfile(provider="ollama", model="qwen3.5:latest", context_window=65536),
    )

    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    # Simulate model response with negligible latency (excludes external download time per SC-001)
    monkeypatch.setattr(cli, "_generate_with_ollama", lambda *_: "Hello from the assistant")

    start = time.monotonic()
    exit_code = cli.main(["--workspace-path", str(workspace_root), "chat", "--prompt", "hello"])
    elapsed = time.monotonic() - start

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "assistant> Hello from the assistant" in output
    # SC-001: must complete under 60 seconds (excluding external model download time)
    assert elapsed < 60.0, f"SC-001 violated: startup took {elapsed:.2f}s, limit is 60s"
