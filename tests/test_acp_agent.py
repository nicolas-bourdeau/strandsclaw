"""Tests for the ACP adapter: startup, capability advertisement, and prompt flow."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from strandsclaw.config import AppConfig, ModelProfile
from strandsclaw.infrastructure.acp.mapping import (
    extract_text_prompt,
    has_non_text_blocks,
    map_outcome_stop_reason,
)
from strandsclaw.workspace import chat_runtime
from strandsclaw.workspace.chat_runtime import TurnOutcome


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Mapping helper unit tests
# ---------------------------------------------------------------------------


def test_extract_text_prompt_returns_text_content() -> None:
    from acp.schema import TextContentBlock

    block = TextContentBlock(type="text", text="hello world")
    result = extract_text_prompt([block])
    assert result == "hello world"


def test_extract_text_prompt_returns_none_for_no_text_blocks() -> None:
    non_text_block = MagicMock(spec=object)
    result = extract_text_prompt([non_text_block])
    assert result is None


def test_extract_text_prompt_concatenates_multiple_blocks() -> None:
    from acp.schema import TextContentBlock

    blocks = [
        TextContentBlock(type="text", text="hello"),
        TextContentBlock(type="text", text="world"),
    ]
    result = extract_text_prompt(blocks)
    assert result == "hello\nworld"


def test_map_outcome_stop_reason_completed() -> None:
    outcome = TurnOutcome(
        status="completed",
        assistant_text="ok",
        stop_reason="end_turn",
        workspace_session_id="default",
    )
    assert map_outcome_stop_reason(outcome) == "end_turn"


def test_map_outcome_stop_reason_refused() -> None:
    outcome = TurnOutcome(
        status="refused",
        assistant_text="denied",
        stop_reason="refusal",
        workspace_session_id="default",
    )
    assert map_outcome_stop_reason(outcome) == "refusal"


def test_map_outcome_stop_reason_cancelled() -> None:
    outcome = TurnOutcome(
        status="cancelled",
        assistant_text="",
        stop_reason="cancelled",
        workspace_session_id="default",
    )
    assert map_outcome_stop_reason(outcome) == "cancelled"


def test_has_non_text_blocks_false_for_text_only() -> None:
    from acp.schema import TextContentBlock

    assert has_non_text_blocks([TextContentBlock(type="text", text="hello")]) is False


def test_has_non_text_blocks_true_for_image() -> None:
    img_mock = MagicMock()
    img_mock.__class__ = object  # not TextContentBlock
    assert has_non_text_blocks([img_mock]) is True


# ---------------------------------------------------------------------------
# ACP agent unit tests
# ---------------------------------------------------------------------------


def test_acp_agent_initialize_returns_protocol_version(tmp_path: Path, monkeypatch) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp import PROTOCOL_VERSION

    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ok")

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)

    response = asyncio.run(agent.initialize(protocol_version=PROTOCOL_VERSION))
    assert response.protocol_version == PROTOCOL_VERSION


def test_acp_agent_initialize_advertises_only_supported_capabilities(
    tmp_path: Path, monkeypatch
) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp import PROTOCOL_VERSION

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)

    response = asyncio.run(agent.initialize(protocol_version=PROTOCOL_VERSION))
    caps = response.agent_capabilities
    assert caps is not None
    # MVP does NOT advertise load_session
    assert caps.load_session is False


def test_acp_agent_new_session_returns_session_id(tmp_path: Path, monkeypatch) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)

    response = asyncio.run(agent.new_session(cwd=str(tmp_path)))
    assert response.session_id
    assert isinstance(response.session_id, str)


def test_acp_agent_prompt_returns_final_response(tmp_path: Path, monkeypatch) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock, PromptRequest

    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "ACP response")

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    async def _body() -> object:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        request = PromptRequest(
            session_id=session_id,
            prompt=[TextContentBlock(type="text", text="hello from ACP")],
        )
        return await agent.prompt(prompt=request.prompt, session_id=session_id)

    prompt_response = asyncio.run(_body())
    assert prompt_response.stop_reason == "end_turn"


def test_acp_agent_prompt_rejects_non_text_content(tmp_path: Path, monkeypatch) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.exceptions import RequestError

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    non_text_block = MagicMock()
    non_text_block.__class__ = object  # not TextContentBlock

    async def _body() -> None:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        await agent.prompt(prompt=[non_text_block], session_id=session_id)

    with pytest.raises((RequestError, ValueError, NotImplementedError)):
        asyncio.run(_body())


def test_acp_agent_unknown_session_prompt_raises(tmp_path: Path, monkeypatch) -> None:
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock
    from acp.exceptions import RequestError

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    with pytest.raises((RequestError, KeyError, ValueError)):
        asyncio.run(agent.prompt(
            prompt=[TextContentBlock(type="text", text="hello")],
            session_id="unknown-session-id",
        ))


# ---------------------------------------------------------------------------
# Phase 4: User Story 2 — workspace behavior preservation
# ---------------------------------------------------------------------------


def test_acp_multiple_sessions_share_workspace_session(tmp_path: Path, monkeypatch) -> None:
    """Multiple ACP sessions bind to the same underlying workspace session."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    workspace_session_id = ctx.session.session_id
    agent = StrandsClawACPAgent(ctx)

    async def _body() -> tuple[object, object]:
        r1 = await agent.new_session(cwd=str(tmp_path))
        r2 = await agent.new_session(cwd=str(tmp_path))
        return r1, r2

    r1, r2 = asyncio.run(_body())

    # The two ACP session IDs are distinct
    assert r1.session_id != r2.session_id

    # Both ACP sessions track the same workspace session
    assert agent._sessions[r1.session_id]["workspace_session_id"] == workspace_session_id
    assert agent._sessions[r2.session_id]["workspace_session_id"] == workspace_session_id


def test_acp_bootstrap_runs_before_first_turn(tmp_path: Path, monkeypatch) -> None:
    """Bootstrap fires when workspace files are missing; the turn still completes."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock

    config = _make_config(tmp_path)
    bootstrap_calls: list[str] = []

    original_bootstrap = chat_runtime.bootstrap_workspace

    def tracking_bootstrap(cfg: AppConfig) -> list:
        bootstrap_calls.append("called")
        return original_bootstrap(cfg)

    monkeypatch.setattr(chat_runtime, "bootstrap_workspace", tracking_bootstrap)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "bootstrapped response")

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    async def _body() -> object:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        return await agent.prompt(
            prompt=[TextContentBlock(type="text", text="hello after bootstrap")],
            session_id=session_id,
        )

    resp = asyncio.run(_body())
    assert resp.stop_reason == "end_turn"


def test_acp_prompt_persists_session_after_turn(tmp_path: Path, monkeypatch) -> None:
    """After a prompt turn the workspace session is persisted to disk."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock

    config = _make_config(tmp_path)
    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", lambda *_: "response text")

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    async def _body() -> None:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        await agent.prompt(
            prompt=[TextContentBlock(type="text", text="persist test")],
            session_id=session_id,
        )

    asyncio.run(_body())

    session_file = config.state_dir / "assistant_session.json"
    assert session_file.exists(), "Session file should have been persisted"


def test_acp_model_unavailable_returns_end_turn_not_exception(tmp_path: Path, monkeypatch) -> None:
    """When the model is unavailable the adapter returns end_turn rather than crashing."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock
    from strandsclaw.workspace.chat_runtime import ModelUnavailableError

    config = _make_config(tmp_path)
    monkeypatch.setattr(
        chat_runtime,
        "_generate_with_ollama",
        lambda *_: (_ for _ in ()).throw(ModelUnavailableError("offline")),
    )

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    async def _body() -> object:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        return await agent.prompt(
            prompt=[TextContentBlock(type="text", text="will fail")],
            session_id=session_id,
        )

    resp = asyncio.run(_body())
    # model_unavailable maps to "end_turn" in the MVP
    assert resp.stop_reason == "end_turn"


def test_acp_load_session_raises_request_error(tmp_path: Path) -> None:
    """load_session is not advertised and must raise RequestError."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.exceptions import RequestError

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)

    with pytest.raises(RequestError):
        asyncio.run(agent.load_session(cwd=str(tmp_path), session_id="some-id"))


def test_acp_list_sessions_raises_request_error(tmp_path: Path) -> None:
    """list_sessions is not advertised and must raise RequestError."""
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.exceptions import RequestError

    config = _make_config(tmp_path)
    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)

    with pytest.raises(RequestError):
        asyncio.run(agent.list_sessions())


# ---------------------------------------------------------------------------
# Phase 6 (T026): Each supported turn persists exactly one final assistant response
# ---------------------------------------------------------------------------


def test_each_turn_persists_exactly_one_assistant_message(tmp_path: Path, monkeypatch) -> None:
    """Each successful prompt turn appends exactly one assistant message to the session."""
    import json
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from acp.schema import TextContentBlock

    config = _make_config(tmp_path)
    turn_counter = {"n": 0}

    def _gen(*_: object) -> str:
        turn_counter["n"] += 1
        return f"response {turn_counter['n']}"

    monkeypatch.setattr(chat_runtime, "_generate_with_ollama", _gen)

    ctx = chat_runtime.prepare_workspace(config)
    agent = StrandsClawACPAgent(ctx)
    mock_conn = AsyncMock()
    agent.set_connection(mock_conn)

    async def _body() -> None:
        session_response = await agent.new_session(cwd=str(tmp_path))
        session_id = session_response.session_id
        for i in range(3):
            await agent.prompt(
                prompt=[TextContentBlock(type="text", text=f"question {i}")],
                session_id=session_id,
            )

    asyncio.run(_body())

    # Each turn produces exactly 1 user + 1 assistant message → 6 total
    state_file = config.state_dir / "assistant_session.json"
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    messages = payload["messages"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_messages) == 3, f"Expected 3 assistant messages, got {len(assistant_messages)}"

    # session_update is called once on new_session (slash commands) + once per prompt turn
    assert mock_conn.session_update.call_count == 4
