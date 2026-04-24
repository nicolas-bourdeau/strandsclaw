# Contract: ACP Agent Surface

## Scope

Defines the client-visible ACP behavior for the StrandsClaw ACP adapter MVP.

## Launch Surface

- Planned operator command: `strandsclaw acp`
- Shared option: `--workspace-path <path>`
- Transport: stdio
- Launch guarantee: the ACP process resolves exactly one active workspace for its entire lifetime.

## Initialization Contract

- The agent returns ACP protocol version and agent metadata during initialization.
- The agent advertises only the MVP session capability set required for a basic text chat agent.
- The MVP does not advertise optional capabilities for session listing, client-managed session loading, streaming output, attachments, or alternate transports.

## Session Contract

### `session/new`

- Creates a client-visible ACP session ID.
- Binds that ACP session to the launch-bound workspace and the existing shared StrandsClaw workspace session.
- Ensures workspace bootstrap/session preparation has completed before the first usable turn.
- Does not allow the client to switch workspaces inside the process.

### `session/prompt`

- Accepts text prompt content for the MVP.
- Rejects or explicitly marks unsupported non-text content as unsupported behavior.
- Executes the turn through the adapter-neutral workspace runtime contract.
- Emits one final assistant message suitable for normal client rendering, then completes the prompt with `stop_reason = end_turn`.

### `session/cancel`

- Supported as a best-effort cancellation surface for the MVP because ACP requires it.
- If cancellation arrives before response delivery, the agent should avoid emitting a final assistant message for that cancelled turn.
- The shared workspace session must remain valid whether cancellation succeeds or becomes a no-op.

## Persistence and Session Reuse

- Multiple ACP sessions for the same process/workspace map to one shared persisted workspace session.
- The ACP adapter does not create a parallel persisted session model for ACP session IDs.
- Reconnecting clients reuse the existing workspace conversation state through normal runtime session loading, even when the ACP session ID changes.

## Error Contract

### Bootstrap or unrecoverable session preparation failure

- Contract: return an actionable protocol-compliant failure outcome and do not accept turns for an unprepared workspace.

### Model runtime unavailable during prompt

- Contract: complete the turn with actionable assistant-facing recovery text and preserve shared workspace session integrity.

### Unsupported capability or payload

- Contract: do not advertise unsupported optional features. If a client still invokes them, return an explicit unsupported/method error rather than silent degradation.

### Workspace file-scope refusal

- Contract: preserve the same refusal behavior as the native runtime for outside-boundary, binary, oversized, or unreadable files.

## Compatibility Notes

- This contract is ACP-specific only at the transport edge.
- Core workspace turn behavior must flow through the shared adapter-runtime contract so future transports can reuse it without ACP model types.
- OpenAI-compatible endpoint support is explicitly out of scope for this contract version.
