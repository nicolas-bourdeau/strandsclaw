# StrandsClaw

StrandsClaw is a pure Python personal-assistant runtime for workspace-first automation. The current repository is intentionally minimal, with only foundational runtime pieces and no extra scaffolding layers.

The current MVP includes a workspace assistant chat runtime that:

- bootstraps missing workspace assistant assets
- persists a single session per workspace
- uses local Ollama with `qwen3.5:latest` and a 64k context window by default
- stays available during model outages and returns actionable per-turn error messages
- supports explicit workspace-scoped file reads for text files up to 64 KB

## Stack

- Python 3.11
- `uv` for environment and dependency management
- `strands-agents`
- Spec Kit for requirements, planning, and task generation

## Project Layout

```text
src/strandsclaw/
├── bootstrap/        # Workspace initialization helpers
├── infrastructure/   # File-backed state store and low-level adapters
├── interfaces/       # CLI and external delivery surfaces
└── workspace/        # Workspace discovery and skill catalog utilities

workspace-template/
├── AGENTS.md         # Default assistant behavior contract
├── BOOTSTRAP.md      # Bootstrap-only startup guidance
├── IDENTITY.md       # Default assistant identity
├── SOUL.md           # Default local personality guidance
└── skills/           # Starter skills copied into active workspace during bootstrap

specs/                # Spec Kit feature artifacts (created per feature)
```

## Getting Started

```bash
make sync
make bootstrap
make test
```

## Common Commands

```bash
make help
make show-config
make list-skills
make run CMD=list-skills
make run CMD='show-config --workspace-path ~/.workspace-test'
uv run strandsclaw chat --workspace-path /tmp/sc-workspace --prompt 'Summarize AGENTS.md'
```

## Chat Runtime

`strandsclaw chat` resolves a workspace, bootstraps missing assistant assets, restores or creates a single persisted session, and executes a chat turn.

Default model profile:

- provider: `ollama`
- model: `qwen3.5:latest`
- context window: `65536`

Environment overrides:

- `STRANDSCLAW_MODEL_PROVIDER`
- `STRANDSCLAW_MODEL`
- `STRANDSCLAW_MODEL_CONTEXT_WINDOW`

Behavior notes:

- If the workspace is missing or incomplete, bootstrap creates only missing defaults and preserves existing user-authored files.
- `BOOTSTRAP.md` is loaded only during bootstrap startup handling, not during normal turns.
- If Ollama or the configured model is unavailable, startup still succeeds and each turn returns an actionable recovery message.
- File reads are limited to files inside the active workspace boundary, must be text, and must be no larger than 64 KB.

## Spec Kit Workflow

This repo is already initialized with Spec Kit for GitHub Copilot. Use the generated slash commands in order:

1. `/speckit.constitution`
2. `/speckit.specify`
3. `/speckit.clarify`
4. `/speckit.plan`
5. `/speckit.tasks`
6. `/speckit.analyze`
7. `/speckit.implement`

## Design Rules

- Keep only modules needed by active features.
- Add new layers only when a concrete feature requires them.
- Keep file-backed state logic in `infrastructure/state`.
- Keep default skills in `workspace-template/`; runtime reads from active workspace.
- Prefer small, spec-backed increments over broad scaffolding.
