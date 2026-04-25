# Contract: Adapter Runtime Seam

## Scope

Defines the internal transport-neutral contract between StrandsClaw runtime behavior and any external protocol adapter.

## Intent

- Keep bootstrap, prompt assembly, file-scope policy, shared session persistence, and model error handling outside protocol-specific glue.
- Let ACP be the first client of the seam without forcing future adapters to depend on ACP request/response types.

## Core Operations

### Prepare Runtime

- Input:
  - `workspace_path: str`
- Output:
  - `WorkspaceRuntimeContext`
- Guarantees:
  - Resolves exactly one active workspace.
  - Bootstraps missing required assistant assets.
  - Loads or safely recovers the shared persisted workspace session.

### Open Protocol Session

- Input:
  - `protocol_session_id: str`
  - `client_info: dict[str, str] | None`
- Output:
  - `ProtocolSession`
- Guarantees:
  - Binds the protocol session to the already-prepared workspace runtime context.
  - Does not create a second persisted active session.

### Run Turn

- Input:
  - `AdapterTurnRequest`
- Output:
  - `TurnOutcome`
- Guarantees:
  - Applies the same prompt assembly, file-scope, bootstrap, and session append rules regardless of transport.
  - Produces transport-neutral statuses and diagnostics.
  - Preserves shared workspace session integrity on success, refusal, and recoverable model failure.

### Cancel Turn

- Input:
  - `protocol_session_id: str`
  - `turn_id: str | None`
- Output:
  - `TurnOutcome` with `status = cancelled` or a transport-neutral no-op result
- Guarantees:
  - Cancellation bookkeeping stays outside transport-specific message formatting.
  - No partial persistence write is committed for a cancelled turn.

### Reset Session

- Input:
  - `protocol_session_id: str`
- Output:
  - `AssistantSession` (new empty session)
- Guarantees:
  - Archives the current session with reason "manual reset" before creating a new one.
  - All future turns use the new session.
  - Useful for `/clear-history` and similar client-driven reset operations.

## Outcome Semantics

- `completed`: assistant text returned successfully.
- `refused`: the runtime intentionally denied the request, such as a file-scope violation.
- `model_unavailable`: the model runtime could not produce a response, but the workspace runtime stayed healthy.
- `unsupported`: the adapter submitted input outside the MVP capability set.
- `bootstrap_failed`: workspace initialization could not complete.
- `session_recovery_failed`: persisted session state could not be recovered safely.
- `cancelled`: the request was cancelled before final delivery.

## Invariants Enforced Through This Seam

- Exactly one launch-bound workspace is active per process.
- Shared workspace session persistence remains the single source of truth.
- Capability decisions stay outside workspace business rules.
- Future adapters may transform transport payloads freely, but they must call into this seam instead of duplicating core turn logic.

## Compatibility Notes

- ACP is the first adapter that will consume this seam.
- A future OpenAI-compatible endpoint should adapt HTTP request/response shapes into the same runtime contract rather than introducing transport-specific branches into core runtime code.
- Any future extension that requires different persistence semantics must revise this contract deliberately rather than bypassing it.
