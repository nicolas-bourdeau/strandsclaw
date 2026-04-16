from __future__ import annotations

from pathlib import Path

from strandsclaw.config import AppConfig, ModelProfile
from strandsclaw.interfaces import cli


def _seed_workspace(workspace_root: Path, template_root: Path) -> None:
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "AGENTS.md").write_text("# AGENTS\nBe helpful.", encoding="utf-8")
    (workspace_root / "IDENTITY.md").write_text("# IDENTITY\nYou are StrandsClaw.", encoding="utf-8")
    (workspace_root / "SOUL.md").write_text("# SOUL\nStay concise.", encoding="utf-8")

    # Bootstrap currently copies from workspace template; keep template available.
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
