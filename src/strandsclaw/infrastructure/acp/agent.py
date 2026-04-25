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

from strandsclaw.config import AppConfig
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


_BOOTSTRAP_COMMAND = "bootstrap"
_BOOTSTRAP_PROMPT_PREFIX = "/bootstrap"

_SLASH_COMMANDS = [
    ("bootstrap", "Initialize or re-initialize the StrandsClaw workspace"),
    ("list-skills", "List available skills in the workspace"),
    ("clear-history", "Clear the current conversation history"),
]


class StrandsClawACPAgent:
    """ACP agent that wraps the StrandsClaw workspace runtime.

    When ctx is None the agent starts in bootstrap-required mode: it advertises
    a /bootstrap slash command and attempts workspace setup when the user
    invokes it instead of silently refusing connections.
    """

    def __init__(
        self,
        ctx: WorkspaceRuntimeContext | None,
        config: AppConfig | None = None,
        log_sink: Any = None,
    ) -> None:
        self._ctx = ctx
        self._config = config
        self._sessions: dict[str, dict[str, Any]] = {}
        self._conn: Any = None
        self._logger = RuntimeEventLogger(sink=log_sink)

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
        workspace_session_id = self._ctx.session.session_id if self._ctx else None
        self._sessions[session_id] = {
            "protocol_session_id": session_id,
            "workspace_session_id": workspace_session_id,
            "cwd": cwd,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._logger.emit(
            "acp.session.new",
            session_id=session_id,
            workspace_session_id=workspace_session_id,
            bootstrap_required=(self._ctx is None),
        )

        if self._conn is not None:
            if self._ctx is None:
                await self._send_bootstrap_command(session_id)
            else:
                await self._send_workspace_commands(session_id)

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

        # Handle slash commands
        if self._ctx is not None:
            cmd_reply = await self._handle_slash_command(input_text, session_id)
            if cmd_reply is not None:
                if self._conn is not None:
                    from acp.helpers import update_agent_message_text
                    await self._conn.session_update(
                        session_id=session_id,
                        update=update_agent_message_text(cmd_reply),
                    )
                return PromptResponse(stop_reason="end_turn")

        # Handle /bootstrap command when workspace is not ready
        if self._ctx is None:
            if input_text.strip().lower().startswith(_BOOTSTRAP_PROMPT_PREFIX):
                reply = await self._handle_bootstrap(session_id)
            else:
                workspace_path = str(self._config.workspace_root) if self._config else "unknown"
                reply = (
                    f"Workspace at `{workspace_path}` is not initialized.\n"
                    "Use the `/bootstrap` command to set it up."
                )
            if self._conn is not None:
                from acp.helpers import update_agent_message_text
                await self._conn.session_update(
                    session_id=session_id,
                    update=update_agent_message_text(reply),
                )
            return PromptResponse(stop_reason="end_turn")

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

    async def _send_bootstrap_command(self, session_id: str) -> None:
        """Advertise the /bootstrap slash command to the client."""
        from acp.helpers import AvailableCommand, update_available_commands
        await self._conn.session_update(
            session_id=session_id,
            update=update_available_commands([
                AvailableCommand(
                    name=_BOOTSTRAP_COMMAND,
                    description="Initialize the StrandsClaw workspace",
                ),
            ]),
        )

    async def _send_workspace_commands(self, session_id: str) -> None:
        """Advertise standard slash commands when the workspace is ready."""
        from acp.helpers import AvailableCommand, update_available_commands
        await self._conn.session_update(
            session_id=session_id,
            update=update_available_commands([
                AvailableCommand(name=name, description=desc)
                for name, desc in _SLASH_COMMANDS
            ]),
        )

    async def _handle_slash_command(self, input_text: str, session_id: str) -> str | None:
        """Return a reply string if input_text is a recognized slash command, else None."""
        stripped = input_text.strip()
        if not stripped.startswith("/"):
            return None
        command = stripped[1:].split()[0].lower()

        if command == "bootstrap":
            return await self._handle_bootstrap(session_id)

        if command == "list-skills":
            from strandsclaw.workspace.skill_catalog import SkillCatalog
            catalog = SkillCatalog(self._ctx.config.skills_dir)
            skills = catalog.list_skills()
            if not skills:
                return "No skills found in the workspace."
            lines = [f"**{s['name']}** — {s['description']}" for s in skills]
            return "Available skills:\n" + "\n".join(f"- {l}" for l in lines)

        if command == "clear-history":
            new_session = self._ctx.session_store.reset()
            self._ctx.session = new_session
            self._logger.emit("acp.command.clear_history", session_id=session_id)
            return "Conversation history cleared."

        return None

    async def _handle_bootstrap(self, session_id: str) -> str:
        """Run workspace bootstrap and promote the agent to ready state."""
        from strandsclaw.bootstrap.init import BootstrapError, bootstrap_workspace
        from strandsclaw.workspace.chat_runtime import prepare_workspace

        self._logger.emit("acp.bootstrap.attempt", session_id=session_id)
        try:
            ctx = prepare_workspace(self._config)
        except BootstrapError as exc:
            self._logger.emit("acp.bootstrap.failed", session_id=session_id, error=str(exc))
            return f"Bootstrap failed: {exc}\nCheck that the path is accessible and try again."

        self._ctx = ctx
        # Update existing session to reference the real workspace session
        self._sessions[session_id]["workspace_session_id"] = ctx.session.session_id
        self._logger.emit(
            "acp.bootstrap.succeeded",
            session_id=session_id,
            workspace_root=str(self._config.workspace_root),
        )

        # Restore the full workspace command list
        if self._conn is not None:
            await self._send_workspace_commands(session_id)

        return f"Workspace initialized at `{self._config.workspace_root}`. You can start chatting now."


class _PromptBlockList:
    """Minimal shim to make ACP mapping helpers work with raw block lists."""

    def __init__(self, prompt: list[Any]) -> None:
        self.prompt = prompt
