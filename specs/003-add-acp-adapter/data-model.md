# Data Model: ACP Adapter

## WorkspaceRuntimeContext

- Purpose: Represents the resolved runtime context for one launch-bound workspace used by any protocol adapter.
- Fields:
  - `workspace_root: str` (absolute canonical workspace path)
  - `state_dir: str` (workspace-local state path)
  - `bootstrap_required: bool`
  - `asset_status: dict[str, bool]` for `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md`
  - `workspace_session_key: str` (existing shared persisted session identity)
  - `capability_policy: AdapterCapabilitySet`
- Validation Rules:
  - Must resolve exactly one active workspace before any ACP turn is accepted (INV-001).
  - `workspace_root` must remain stable for the lifetime of the ACP process.
  - Bootstrap may create only missing required assets.
- State Transitions:
  - `unresolved -> resolved`
  - `resolved -> bootstrapped` when missing assets are materialized
  - `resolved/bootstrapped -> ready` when shared session and runtime assets are available

## ProtocolSession

- Purpose: Represents one client-visible ACP session bound to the launch-bound workspace.
- Fields:
  - `protocol_session_id: str`
  - `client_info: str | None`
  - `transport: str` (initially `stdio`)
  - `workspace_root: str`
  - `workspace_session_id: str`
  - `created_at: str` (ISO8601)
  - `last_activity_at: str` (ISO8601)
- Validation Rules:
  - `protocol_session_id` must be unique per ACP client session.
  - All protocol sessions in one process must map to the same launch-bound workspace.
  - Mapping to the shared workspace session must not create a second persisted active session (INV-002, INV-005).
- State Transitions:
  - `new -> active`
  - `active -> cancelled`
  - `active -> closed`

## AdapterCapabilitySet

- Purpose: Defines the explicit client-visible ACP capabilities for one adapter release.
- Fields:
  - `supports_new_session: bool`
  - `supports_prompt: bool`
  - `supports_cancel: bool`
  - `supports_load_session: bool`
  - `supports_list_sessions: bool`
  - `supports_streaming: bool`
  - `supports_attachments: bool`
  - `supported_transports: list[str]`
- Validation Rules:
  - Advertised capabilities must match implemented behavior exactly (INV-003).
  - Unsupported capabilities must be omitted or explicitly rejected, never implied.
- State Transitions:
  - `draft -> advertised`
  - `advertised -> revised` only through a future protocol release

## AdapterTurnRequest

- Purpose: Represents one adapter-neutral request to run a user turn against the shared workspace runtime.
- Fields:
  - `protocol_session_id: str`
  - `workspace_root: str`
  - `input_text: str`
  - `content_kinds: list[str]`
  - `requested_at: str` (ISO8601)
- Validation Rules:
  - MVP accepts text content only.
  - The workspace must already be resolved for the protocol session.
  - Requests must execute through the shared runtime contract rather than protocol-specific business logic (INV-004).
- State Transitions:
  - `received -> validated`
  - `validated -> executing`
  - `executing -> completed | failed | cancelled`

## TurnOutcome

- Purpose: Captures the transport-neutral result of one runtime turn.
- Fields:
  - `status: str` (`completed`, `refused`, `model_unavailable`, `unsupported`, `bootstrap_failed`, `session_recovery_failed`, `cancelled`)
  - `assistant_text: str`
  - `stop_reason: str`
  - `workspace_session_id: str`
  - `diagnostics: dict[str, str]`
  - `completed_at: str` (ISO8601)
- Validation Rules:
  - A completed or recoverable failed turn must preserve a valid shared workspace session.
  - `assistant_text` must be renderable as a normal conversational message when `status` is `completed`, `refused`, or `model_unavailable`.
  - Diagnostics must be deterministic and safe for logs.
- State Transitions:
  - `pending -> completed`
  - `pending -> refused`
  - `pending -> model_unavailable`
  - `pending -> unsupported`
  - `pending -> cancelled`

## SharedWorkspaceSession

- Purpose: Represents the existing persisted StrandsClaw conversation state reused by ACP sessions.
- Fields:
  - `session_id: str`
  - `messages: list[dict[str, str]]`
  - `created_at: str`
  - `updated_at: str`
- Validation Rules:
  - Exactly one active shared workspace session exists per workspace.
  - Unreadable session payloads must still be archived before replacement.
  - ACP must reuse this state model rather than creating a parallel persisted session type.
- State Transitions:
  - `missing -> active`
  - `active -> active` on appended turns from ACP or other supported entrypoints
  - `active(unreadable) -> archived + active(new)`
