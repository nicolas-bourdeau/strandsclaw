# Contract: CLI Chat Runtime

## Scope

Defines operator-visible CLI behavior for starting and using the workspace assistant runtime for feature `001-workspace-chat-agent`.

## Command Surface

- Command: `strandsclaw chat`
- Shared option: `--workspace-path <path>`
- Behavior:
  - Resolves one active workspace.
  - Bootstraps missing assistant assets before first turn when needed.
  - Restores existing single session or safely recovers from unreadable session state.
  - Starts interactive chat loop and returns assistant responses.

## Inputs

- Operator prompt text from stdin/interactive terminal.
- Optional file read requests expressed in prompt intent and resolved by workspace-scoped file tool.

## Outputs

- Success:
  - Assistant response text for each accepted prompt.
  - Informational startup messages (workspace resolved, bootstrapped, session resumed/new).
- Error:
  - Actionable operator message when model runtime is unavailable.
  - Clear refusal text for denied file reads (outside workspace, binary, >64 KB, unreadable).

## Startup Guarantees

- `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md` exist after startup bootstrap path.
- Existing user-authored versions of these files are preserved (no overwrite).
- Prompt assembly on normal turns includes only `AGENTS.md`, `IDENTITY.md`, `SOUL.md`.
- `BOOTSTRAP.md` is used only in bootstrap flow.

## Error Contract

### Bootstrap failures

- Condition: workspace cannot be created or template asset copy fails.
- Contract: return non-zero exit and print actionable message with failing path and operation.

### Model runtime failures

- Condition: Ollama unavailable, model missing, or generation call fails.
- Contract: keep session state intact and print actionable recovery hints.

### File read refusals

- Outside workspace boundary: `Denied: requested path is outside the active workspace boundary.`
- Oversize file: `Denied: file exceeds 64 KB limit.`
- Binary file: `Denied: binary files are not supported in this MVP.`
- Permission/read failure: `Denied: file could not be read.`

## Exit Behavior

- `0`: normal command completion.
- non-zero: startup/runtime failure before usable chat flow.
