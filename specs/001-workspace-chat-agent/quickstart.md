# Quickstart: Workspace Chat Agent MVP

## Prerequisites

- Python 3.11+
- `uv` installed
- Local Ollama service running
- Ollama model `qwen3.5:latest` available locally

## Setup

```bash
cd /home/nbourdeau/dev/strandsclaw
uv sync
```

## Validate Baseline Commands

```bash
uv run strandsclaw show-config
uv run strandsclaw bootstrap
uv run strandsclaw list-skills
```

## Start Chat Runtime (Planned Command)

```bash
uv run strandsclaw chat --workspace-path /tmp/sc-workspace
```

Expected startup behavior:

- Resolves workspace path.
- If missing/empty, bootstraps required files:
  - `AGENTS.md`
  - `BOOTSTRAP.md`
  - `IDENTITY.md`
  - `SOUL.md`
- Restores existing single session when valid.
- Archives unreadable session and starts fresh replacement session.

## Smoke Tests

### 1. Existing workspace chat

```bash
uv run strandsclaw chat --workspace-path /tmp/sc-workspace
```

- Send prompt: `Summarize your role in this workspace.`
- Verify assistant responds and turn is persisted.

### 2. Missing workspace bootstrap

```bash
rm -rf /tmp/sc-new
uv run strandsclaw chat --workspace-path /tmp/sc-new
```

- Verify directory and required files are created automatically.
- Verify first chat response is returned without manual setup.

### 3. Session resume

- Restart command using same workspace.
- Verify prior conversation context is resumed.

### 4. File-scope allow

- Create `/tmp/sc-workspace/notes.txt` with text content <= 64 KB.
- Ask assistant to summarize `notes.txt`.
- Verify response incorporates file content.

### 5. File-scope deny

- Ask assistant to read `/etc/hosts` (outside workspace).
- Verify denial explains workspace boundary.

### 6. File-size/binary deny

- Ask assistant to read a binary file or text file >64 KB.
- Verify clear denial message.

## Test Suite

```bash
uv run pytest
```

Focus areas for this feature:

- bootstrap idempotency and non-overwrite behavior
- single-session persistence and archive recovery
- workspace boundary and read-policy enforcement
- chat command startup/resume behavior
