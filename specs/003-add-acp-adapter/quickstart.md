# Quickstart: ACP Adapter MVP

## Prerequisites

- Python 3.11+
- `uv` installed
- An ACP-capable client that can launch a local stdio agent
- Local model runtime optional for startup validation and required for a successful assistant response

## Setup

```bash
cd /path/to/strandsclaw
uv sync
```

## Launch the ACP Agent

```bash
uv run strandsclaw acp --workspace-path /tmp/sc-workspace
```

The ACP process is launch-bound to the workspace passed on startup. All ACP sessions created through that process share the same underlying StrandsClaw workspace session.

## Example ACP Client Configuration

Example `agent_servers` entry for an ACP-capable client:

```json
{
  "agent_servers": {
    "StrandsClaw ACP": {
      "type": "custom",
      "command": "uv",
      "args": [
        "run",
        "strandsclaw",
        "acp",
        "--workspace-path",
        "/tmp/sc-workspace"
      ]
    }
  }
}
```

## Expected Startup Behavior

- Resolves one launch-bound workspace before accepting ACP turns.
- Bootstraps missing assistant assets before first usable turn.
- Reuses the existing shared persisted workspace session when present.
- Advertises only the ACP capabilities supported by the MVP.
- Returns one final assistant response per supported prompt rather than streaming partial output.

## Smoke Tests

### 1. ACP startup and first prompt

- Launch the agent with `uv run strandsclaw acp --workspace-path /tmp/sc-workspace`.
- Connect from an ACP-capable client.
- Start a new session and send a text prompt such as `Summarize your role in this workspace.`
- Verify the client receives a normal assistant response and the workspace session persists under `.state/`.

### 2. Missing workspace bootstrap through ACP

- Remove `/tmp/sc-new-workspace` if it exists.
- Launch the ACP agent against `/tmp/sc-new-workspace`.
- Start a session and send the first prompt.
- Verify required assistant files are created before the first usable turn.

### 3. Reconnect and shared session reuse

- Start an ACP session, send a prompt, then disconnect the client.
- Reconnect with the same agent process or restart the process against the same workspace.
- Start a new ACP session.
- Verify the underlying shared workspace session resumes previous conversation state even if the ACP session ID changes.

### 4. Unsupported capability handling

- Inspect agent capabilities during initialization.
- Verify optional non-MVP features such as session listing, streaming, and attachments are not advertised.
- If the client attempts an unsupported operation anyway, verify the outcome is explicit and actionable.

### 5. Slash command functionality

- Launch the ACP agent: `uv run strandsclaw acp --workspace-path /tmp/sc-workspace`.
- Start a session and send `/list-skills`.
- Verify the response lists skills from the workspace.
- Send `/clear-history`.
- Verify the response confirms clearing and subsequent prompts start a fresh conversation.
- In a fresh workspace that fails bootstrap, start a session and verify only `/bootstrap` is advertised.
- Send `/bootstrap` and verify the response indicates successful initialization.

### 6. Model-unavailable turn behavior

- Stop the local model runtime.
- Launch the ACP agent and start a session.
- Send a prompt.
- Verify the turn completes with actionable recovery guidance and does not corrupt shared workspace session state.

## Test Suite

```bash
uv run pytest
```

Focus areas for this feature:

- adapter-neutral runtime extraction from the CLI path
- ACP initialization, capability advertisement, and prompt flow
- shared workspace session reuse across ACP sessions
- workspace bootstrap and file-scope behavior preservation
- actionable failure paths for unsupported operations and model outages
