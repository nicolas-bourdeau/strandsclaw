# Data Model: Workspace Chat Agent

## WorkspaceRuntime

- Purpose: Represents resolved runtime context for one active workspace.
- Fields:
  - `workspace_root: str` (absolute canonical path)
  - `state_dir: str` (workspace-local state path)
  - `bootstrap_required: bool`
  - `asset_status: dict[str, bool]` for `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md`
  - `model_profile: ModelProfile`
- Validation Rules:
  - Must resolve exactly one active workspace before chat (INV-001).
  - `workspace_root` must exist after bootstrap path resolution.
- State Transitions:
  - `unresolved -> resolved`
  - `resolved -> bootstrapped` when required assets are materialized
  - `resolved/bootstrapped -> chat_ready` after prompt contract and session are loaded

## AssistantAssetSet

- Purpose: Defines minimum operable workspace assistant files.
- Fields:
  - `required_files: list[str]` fixed to `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md`
  - `missing_files: list[str]`
  - `created_files: list[str]`
- Validation Rules:
  - Bootstrap must create only missing files (INV-002).
  - Existing files must never be overwritten.
- State Transitions:
  - `incomplete -> complete` when all required files are present.

## ModelProfile

- Purpose: Holds runtime chat model defaults and override-ready configuration.
- Fields:
  - `provider: str` (default: `ollama`)
  - `model: str` (default: `qwen3.5:latest`)
  - `context_window: int` (default: `65536`)
- Validation Rules:
  - `context_window > 0`
  - `model` non-empty
- State Transitions:
  - `default_profile -> overridden_profile` via future setup/installation flow (out of scope for MVP implementation, in-scope as design compatibility).

## AssistantSession

- Purpose: Single persisted conversation state for a workspace.
- Fields:
  - `session_id: str` (stable single-session identity per workspace)
  - `messages: list[ChatMessage]`
  - `created_at: str` (ISO8601)
  - `updated_at: str` (ISO8601)
- Validation Rules:
  - At most one active session record per workspace (INV-004).
  - Message order is append-only for MVP.
- State Transitions:
  - `missing -> active`
  - `active -> active` on appended turn
  - `active(unreadable) -> archived + active(new)` (INV-005)

## ArchivedSessionRecord

- Purpose: Retains unreadable prior session payload for recovery/inspection.
- Fields:
  - `archived_from: str` (source session key/path)
  - `archived_at: str` (ISO8601)
  - `reason: str` (decode/validation failure reason)
  - `raw_payload: str | object | null`
- Validation Rules:
  - Archive must be created before replacement session is written (INV-005).
- State Transitions:
  - `none -> archived` when recovery path handles unreadable persisted session.

## ChatTurn

- Purpose: Represents one user input and one assistant output within active session.
- Fields:
  - `turn_id: str`
  - `user_prompt: str`
  - `assistant_response: str`
  - `referenced_files: list[FileReadEvent]`
  - `timestamp: str` (ISO8601)
- Validation Rules:
  - Prompt and response must be non-empty strings for successful turn recording.

## FileReadEvent

- Purpose: Captures attempted file read interaction for a turn.
- Fields:
  - `requested_path: str`
  - `resolved_path: str | null`
  - `status: str` (`allowed` | `denied` | `error`)
  - `reason: str | null`
  - `bytes_read: int | null`
- Validation Rules:
  - Allowed reads must resolve within workspace boundary (INV-003).
  - `bytes_read <= 65536` for allowed reads (FR-018).
  - Binary or non-readable files must be denied with clear reason.

## Relationships

- `WorkspaceRuntime` owns one active `AssistantSession`.
- `WorkspaceRuntime` includes one `AssistantAssetSet` and one `ModelProfile`.
- `AssistantSession` contains many `ChatTurn` entries.
- `ChatTurn` may reference zero or many `FileReadEvent` entries.
- `ArchivedSessionRecord` is linked to prior unreadable `AssistantSession` data for the same workspace.
