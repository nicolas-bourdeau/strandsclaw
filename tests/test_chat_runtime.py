from __future__ import annotations

from pathlib import Path

import pytest

from strandsclaw.bootstrap.init import BootstrapError
from strandsclaw.config import AppConfig, ModelProfile
from strandsclaw.interfaces import cli
from strandsclaw.workspace import chat_runtime


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
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "Acknowledged")

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "assistant> Acknowledged" in output

    state_path = config.state_dir / "assistant_session.json"
    assert state_path.exists()


def test_chat_resumes_existing_session_between_runs(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

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
        raise chat_runtime.ModelUnavailableError("connection refused")

    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", _raise)

    exit_code = cli.main(["--workspace-path", str(config.workspace_root), "chat", "--prompt", "hello"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Model unavailable:" in output
    assert "Verify Ollama is running" in output


def test_chat_emits_structured_runtime_events(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    events: list[str] = []

    monkeypatch.setattr(cli, "load_config", lambda **_: config)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

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
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

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
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")
    monkeypatch.setattr(
        chat_runtime,
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

    monkeypatch.setattr(chat_runtime, "bootstrap_workspace", _raise)

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

    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", _respond)

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
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: pytest.fail("model should not be called"))

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
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "Hello from the assistant")

    start = time.monotonic()
    exit_code = cli.main(["--workspace-path", str(workspace_root), "chat", "--prompt", "hello"])
    elapsed = time.monotonic() - start

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "assistant> Hello from the assistant" in output
    # SC-001: must complete under 60 seconds (excluding external model download time)
    assert elapsed < 60.0, f"SC-001 violated: startup took {elapsed:.2f}s, limit is 60s"


# ---------------------------------------------------------------------------
# Tests for the shared workspace runtime seam (chat_runtime module)
# These tests exercise the adapter-neutral contract directly rather than
# going through the CLI delivery surface.
# ---------------------------------------------------------------------------


def test_prepare_workspace_returns_context_with_session(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)

    assert ctx.config is config
    assert ctx.session_store is not None
    assert ctx.session is not None
    assert ctx.session.session_id == "default"
    assert ctx.logger is not None


def test_execute_turn_completed_outcome(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "runtime answer")

    ctx = chat_runtime.prepare_workspace(config)
    outcome = chat_runtime.execute_turn(ctx, "hello")

    assert outcome.status == "completed"
    assert outcome.assistant_text == "runtime answer"
    assert outcome.stop_reason == "end_turn"
    assert outcome.workspace_session_id == "default"


def test_execute_turn_model_unavailable_outcome(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)

    def _raise(*_):
        raise chat_runtime.ModelUnavailableError("timeout")

    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", _raise)

    ctx = chat_runtime.prepare_workspace(config)
    outcome = chat_runtime.execute_turn(ctx, "ping")

    assert outcome.status == "model_unavailable"
    assert "Model unavailable:" in outcome.assistant_text
    assert "timeout" in outcome.diagnostics.get("model_error", "")


def test_execute_turn_refused_for_outside_boundary_file(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: pytest.fail("should not call model"))

    ctx = chat_runtime.prepare_workspace(config)
    outcome = chat_runtime.execute_turn(ctx, "Read ../secret.txt")

    assert outcome.status == "refused"
    assert "Denied" in outcome.assistant_text


def test_execute_turn_persists_session(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

    ctx = chat_runtime.prepare_workspace(config)
    chat_runtime.execute_turn(ctx, "first")
    chat_runtime.execute_turn(ctx, "second")

    from strandsclaw.infrastructure.state.file_state_store import FileStateStore
    payload = FileStateStore(config.state_dir).read("assistant_session")
    assert payload is not None
    assert len(payload["messages"]) == 4


def test_execute_turn_session_is_shared_across_contexts(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

    ctx1 = chat_runtime.prepare_workspace(config)
    chat_runtime.execute_turn(ctx1, "turn one")

    ctx2 = chat_runtime.prepare_workspace(config)
    chat_runtime.execute_turn(ctx2, "turn two")

    from strandsclaw.infrastructure.state.file_state_store import FileStateStore
    payload = FileStateStore(config.state_dir).read("assistant_session")
    assert len(payload["messages"]) == 4


def test_prepare_workspace_raises_on_bootstrap_failure(tmp_path: Path, monkeypatch) -> None:
    config = _make_config(tmp_path)

    def _raise(_config):
        raise BootstrapError("cannot create directory: permission denied")

    monkeypatch.setattr(chat_runtime, "bootstrap_workspace", _raise)

    with pytest.raises(BootstrapError, match="permission denied"):
        chat_runtime.prepare_workspace(config)


# ---------------------------------------------------------------------------
# Phase 5 (T021): Adapter-runtime seam regression tests for future transport reuse
# ---------------------------------------------------------------------------


def test_chat_runtime_has_no_acp_imports() -> None:
    """chat_runtime must not import ACP or any adapter-specific module.

    This ensures the transport seam stays reusable for future non-ACP adapters.
    """
    import importlib
    import sys

    # Force a fresh module inspection without importing acp
    source = chat_runtime.__file__
    assert source is not None
    from pathlib import Path as _Path

    text = _Path(source).read_text(encoding="utf-8")
    assert "import acp" not in text, "chat_runtime must not import the acp package"
    assert "from acp" not in text, "chat_runtime must not import from the acp package"


def test_chat_runtime_has_no_cli_imports() -> None:
    """chat_runtime must not import from the CLI interface layer."""
    import importlib
    from pathlib import Path as _Path

    source = chat_runtime.__file__
    assert source is not None
    text = _Path(source).read_text(encoding="utf-8")
    assert "interfaces.cli" not in text, "chat_runtime must not import from interfaces.cli"
    assert "from strandsclaw.interfaces" not in text, "chat_runtime must not import from interfaces"


def test_prepare_workspace_returns_transport_neutral_context(tmp_path: Path, monkeypatch) -> None:
    """prepare_workspace returns WorkspaceRuntimeContext with no transport-specific fields."""
    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)

    # Must have the adapter-neutral fields
    assert hasattr(ctx, "config")
    assert hasattr(ctx, "logger")
    assert hasattr(ctx, "session_store")
    assert hasattr(ctx, "session")

    # Must NOT have transport-specific fields (acp, cli, etc.)
    assert not hasattr(ctx, "conn")
    assert not hasattr(ctx, "acp_connection")


def test_execute_turn_returns_transport_neutral_outcome(tmp_path: Path, monkeypatch) -> None:
    """execute_turn returns TurnOutcome with no transport-specific data."""
    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "response")
    ctx = chat_runtime.prepare_workspace(config)
    outcome = chat_runtime.execute_turn(ctx, "test turn")

    # Must have the neutral fields
    assert hasattr(outcome, "status")
    assert hasattr(outcome, "assistant_text")
    assert hasattr(outcome, "stop_reason")
    assert hasattr(outcome, "workspace_session_id")

    # No acp-specific fields
    assert not hasattr(outcome, "acp_session_id")
    assert not hasattr(outcome, "protocol_version")

