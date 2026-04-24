"""StrandsClaw ACP agent implementation.

Implements the ACP Agent Protocol interface for the MVP:
- initialize: protocol version + minimal capability advertisement
- new_session: create a client-visible ACP session bound to the launch-bound workspace
- prompt: run a text turn through the adapter-neutral workspace runtime
- load_session / list_sessions: explicitly unsupported (not advertised)

Session mapping:
  All ACP sessions in one process share a single persisted workspace session.
  Multiple reconnects reuse the existing workspace conversation state.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from acp import PROTOCOL_VERSION
from acp.exceptions import RequestError
from acp.schema import (
    AgentCapabilities,
    Implementation,
    InitializeResponse,
    ListSessionsResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptResponse,
    TextContentBlock,
)

from strandsclaw.infrastructure.acp.mapping import (
    extract_text_prompt,
    has_non_text_blocks,
    map_outcome_stop_reason,
)
from strandsclaw.infrastructure.observability import RuntimeEventLogger
from strandsclaw.workspace.chat_runtime import WorkspaceRuntimeContext, execute_turn

_AGENT_NAME = "strandsclaw"
_AGENT_VERSION = "0.1.0"

_ERROR_UNSUPPORTED_LOAD_SESSION = -32601  # method not found
_ERROR_UNSUPPORTED_LIST_SESSIONS = -32601
_ERROR_UNSUPPORTED_CONTENT = -32602  # invalid params


class StrandsClawACPAgent:
    """ACP agent that wraps the StrandsClaw workspace runtime."""

    def __init__(self, ctx: WorkspaceRuntimeContext) -> None:
        self._ctx = ctx
        self._sessions: dict[str, dict[str, Any]] = {}
        self._conn: Any = None
        self._logger = RuntimeEventLogger()

    def set_connection(self, conn: Any) -> None:
        """Inject the AgentSideConnection for sending session_update notifications."""
        self._conn = conn

    def on_connect(self, conn: Any) -> None:
        """Called by AgentSideConnection when the connection is established."""
        self.set_connection(conn)

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Any = None,
        client_info: Any = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        """Return ACP protocol version and advertised capabilities."""
        self._logger.emit("acp.initialize", protocol_version=protocol_version)
        caps = AgentCapabilities(
            load_session=False,
        )
        return InitializeResponse(
            protocol_version=min(protocol_version, PROTOCOL_VERSION),
            agent_info=Implementation(name=_AGENT_NAME, version=_AGENT_VERSION),
            agent_capabilities=caps,
        )

    async def new_session(
        self,
        cwd: str,
        mcp_servers: Any = None,
        **kwargs: Any,
    ) -> NewSessionResponse:
        """Create a new ACP session bound to the launch-bound workspace session."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "protocol_session_id": session_id,
            "workspace_session_id": self._ctx.session.session_id,
            "cwd": cwd,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._logger.emit(
            "acp.session.new",
            session_id=session_id,
            workspace_session_id=self._ctx.session.session_id,
        )
        return NewSessionResponse(session_id=session_id)

    async def load_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: Any = None,
        **kwargs: Any,
    ) -> LoadSessionResponse | None:
        """Not supported in the MVP; raise an explicit error."""
        raise RequestError(
            code=_ERROR_UNSUPPORTED_LOAD_SESSION,
            message="session/load is not supported by this agent",
        )

    async def list_sessions(
        self,
        cursor: str | None = None,
        cwd: str | None = None,
        **kwargs: Any,
    ) -> ListSessionsResponse:
        """Not supported in the MVP; raise an explicit error."""
        raise RequestError(
            code=_ERROR_UNSUPPORTED_LIST_SESSIONS,
            message="session/list is not supported by this agent",
        )

    async def prompt(
        self,
        prompt: list[Any],
        session_id: str,
        message_id: str | None = None,
        **kwargs: Any,
    ) -> PromptResponse:
        """Run a text turn through the shared workspace runtime."""
        if session_id not in self._sessions:
            raise RequestError(
                code=-32602,
                message=f"unknown session_id: {session_id}",
            )

        # Reject non-text content blocks
        from acp.schema import PromptRequest
        mock_req = _PromptBlockList(prompt)
        if has_non_text_blocks(mock_req):
            raise RequestError(
                code=_ERROR_UNSUPPORTED_CONTENT,
                message="only text content blocks are supported in the MVP",
            )

        input_text = extract_text_prompt(mock_req)
        if not input_text:
            raise RequestError(
                code=_ERROR_UNSUPPORTED_CONTENT,
                message="prompt must contain at least one non-empty text block",
            )

        self._logger.emit("acp.prompt.start", session_id=session_id)

        outcome = execute_turn(self._ctx, input_text)

        self._logger.emit(
            "acp.prompt.complete",
            session_id=session_id,
            status=outcome.status,
        )

        # Send the final assistant message to the client as a session notification
        if self._conn is not None:
            from acp.helpers import update_agent_message_text
            await self._conn.session_update(
                session_id=session_id,
                update=update_agent_message_text(outcome.assistant_text),
            )

        stop_reason = map_outcome_stop_reason(outcome)
        return PromptResponse(stop_reason=stop_reason)

    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs: Any) -> None:
        raise RequestError(code=_ERROR_UNSUPPORTED_LOAD_SESSION, message="set_session_mode is not supported")

    async def set_session_model(self, model_id: str, session_id: str, **kwargs: Any) -> None:
        raise RequestError(code=_ERROR_UNSUPPORTED_LOAD_SESSION, message="set_session_model is not supported")

    async def set_config_option(self, config_id: str, session_id: str, value: Any, **kwargs: Any) -> None:
        raise RequestError(code=_ERROR_UNSUPPORTED_LOAD_SESSION, message="set_config_option is not supported")

    async def authenticate(self, method_id: str, **kwargs: Any) -> None:
        raise RequestError(code=_ERROR_UNSUPPORTED_LOAD_SESSION, message="authenticate is not supported")


class _PromptBlockList:
    """Minimal shim to make ACP mapping helpers work with raw block lists."""

    def __init__(self, prompt: list[Any]) -> None:
        self.prompt = prompt
