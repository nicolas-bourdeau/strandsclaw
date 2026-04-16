# Contract: Session State Files

## Scope

Defines persisted state layout and recovery behavior for one active assistant session per workspace.

## Storage Location

- Base directory: `<workspace>/.state/`
- Active session file key: `assistant_session` (serialized via `FileStateStore` as JSON)
- Archive file key pattern: `assistant_session__archived__<timestamp>`

## Active Session Schema

```json
{
  "session_id": "default",
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "2026-03-27T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": "2026-03-27T12:00:01Z"
    }
  ],
  "created_at": "2026-03-27T12:00:00Z",
  "updated_at": "2026-03-27T12:00:01Z"
}
```

## Archive Session Schema

```json
{
  "archived_from": "assistant_session",
  "archived_at": "2026-03-27T12:05:00Z",
  "reason": "json decode error",
  "raw_payload": "..."
}
```

## Invariants Enforced

- Exactly one active session record per workspace.
- Recovery from unreadable active session must archive before replacement creation.
- Replacement session is initialized as valid empty session and becomes active immediately.

## Recovery Contract

1. Attempt to read and validate active session schema.
2. If unreadable/corrupt:
   - Persist archive record with reason and recoverable payload.
   - Create fresh valid active session record.
   - Continue startup without creating additional active session files.

## Compatibility Notes

- Contract is file-backed and deterministic for inspection/testing.
- Future schema additions must be backward-compatible or include migration logic.
