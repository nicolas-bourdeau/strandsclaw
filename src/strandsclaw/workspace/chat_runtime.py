"""Adapter-neutral workspace runtime seam.

Provides the transport-agnostic contract used by both the CLI and the ACP adapter
(and any future adapter) to prepare a workspace and execute a single chat turn.

Rules enforced here:
- Exactly one launch-bound workspace is active per process call.
- Bootstrap runs before the first turn if the workspace is missing or incomplete.
- File-scope refusals, model-unavailability outcomes, and session persistence
  are handled regardless of the calling transport.
- Business rules must not live in the CLI, ACP glue, or state adapters.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

from strandsclaw.bootstrap.init import BootstrapError, bootstrap_workspace
from strandsclaw.config import AppConfig
from strandsclaw.infrastructure.observability import RuntimeEventLogger
from strandsclaw.infrastructure.state.file_state_store import FileStateStore
from strandsclaw.infrastructure.state.session_store import AssistantSession, SessionStore
from strandsclaw.workspace.assistant_assets import get_missing_assistant_files, load_bootstrap_instructions, load_normal_turn_assets
from strandsclaw.workspace.file_tool import collect_file_context, register_workspace_file_read_tool
from strandsclaw.workspace.prompt_assembly import assemble_normal_turn_prompt


TurnStatus = Literal[
    "completed",
    "refused",
    "model_unavailable",
    "unsupported",
    "bootstrap_failed",
    "session_recovery_failed",
    "cancelled",
]


@dataclass
class WorkspaceRuntimeContext:
    """Resolved runtime context for one launch-bound workspace."""

    config: AppConfig
    logger: RuntimeEventLogger
    session_store: SessionStore
    session: AssistantSession


@dataclass
class TurnOutcome:
    """Transport-neutral result of a single runtime turn."""

    status: TurnStatus
    assistant_text: str
    stop_reason: str
    workspace_session_id: str
    diagnostics: dict[str, str] = field(default_factory=dict)
    completed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ModelUnavailableError(RuntimeError):
    """Raised when the configured model runtime cannot produce a response."""


def prepare_workspace(config: AppConfig) -> WorkspaceRuntimeContext:
    """Resolve workspace, run bootstrap if needed, load or create the shared session.

    Raises:
        BootstrapError: if workspace materialization fails unrecoverably.
    """
    logger = RuntimeEventLogger()
    registered_tool = register_workspace_file_read_tool()
    logger.emit("tool.registered", tool=asdict(registered_tool))

    bootstrap_required = (not config.workspace_root.exists()) or bool(
        get_missing_assistant_files(config.workspace_root)
    )

    try:
        created = bootstrap_workspace(config)
    except BootstrapError:
        raise

    logger.emit("workspace.bootstrap", created=[str(p) for p in created])
    if bootstrap_required:
        instructions = load_bootstrap_instructions(config.workspace_root)
        logger.emit(
            "workspace.bootstrap_instructions_loaded",
            has_instructions=bool(instructions.strip()),
        )

    state_store = FileStateStore(config.state_dir)
    session_store = SessionStore(state_store)
    session = session_store.load_or_create()
    logger.emit("session.loaded", message_count=len(session.messages))

    return WorkspaceRuntimeContext(
        config=config,
        logger=logger,
        session_store=session_store,
        session=session,
    )


def execute_turn(ctx: WorkspaceRuntimeContext, user_prompt: str) -> TurnOutcome:
    """Run one chat turn against the shared workspace runtime.

    Applies prompt assembly, file-scope enforcement, model call, and session
    persistence.  Returns a transport-neutral TurnOutcome regardless of transport.
    """
    config = ctx.config
    logger = ctx.logger
    session_store = ctx.session_store
    session = ctx.session

    assets = load_normal_turn_assets(config.workspace_root)
    file_context, file_result = collect_file_context(config.workspace_root, user_prompt)

    if file_result is not None and file_result.status != "allowed":
        response = file_result.reason or "Denied: file could not be read."
        logger.emit(
            "file.read_denied",
            requested_path=file_result.requested_path,
            reason=file_result.reason,
        )
        updated = session_store.append_turn(session, user_prompt, response)
        session_store.save(updated)
        ctx.session = updated
        logger.emit("session.saved", message_count=len(updated.messages))
        return TurnOutcome(
            status="refused",
            assistant_text=response,
            stop_reason="refusal",
            workspace_session_id=updated.session_id,
        )

    if file_result is not None:
        logger.emit(
            "file.read_allowed",
            requested_path=file_result.requested_path,
            resolved_path=file_result.resolved_path,
            bytes_read=file_result.bytes_read,
        )

    prompt = assemble_normal_turn_prompt(assets, user_prompt, file_context=file_context)

    try:
        response = _generate_with_ollama(config, prompt)
        logger.emit("chat.turn_succeeded")
        status: TurnStatus = "completed"
        stop_reason = "end_turn"
        diagnostics: dict[str, str] = {}
    except ModelUnavailableError as exc:
        response = f"Model unavailable: {exc}. Verify Ollama is running and the model is installed."
        logger.emit("chat.turn_model_unavailable", error=str(exc))
        status = "model_unavailable"
        stop_reason = "end_turn"
        diagnostics = {"model_error": str(exc)}

    updated = session_store.append_turn(session, user_prompt, response)
    session_store.save(updated)
    ctx.session = updated
    logger.emit("session.saved", message_count=len(updated.messages))

    return TurnOutcome(
        status=status,
        assistant_text=response,
        stop_reason=stop_reason,
        workspace_session_id=updated.session_id,
        diagnostics=diagnostics,
    )


def _generate_with_ollama(config: AppConfig, prompt: str) -> str:
    """Call local Ollama to generate a response.

    Raises:
        ModelUnavailableError: on network error, timeout, or empty response.
    """
    if config.model_profile.provider != "ollama":
        raise ModelUnavailableError(f"unsupported provider '{config.model_profile.provider}'")

    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(
            {
                "model": config.model_profile.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": config.model_profile.context_window},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - local ollama endpoint
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ModelUnavailableError(str(exc)) from exc

    message = str(payload.get("response", "")).strip()
    if not message:
        raise ModelUnavailableError("empty response from model runtime")
    return message
