# StrandsClaw

StrandsClaw is a pure Python personal-assistant runtime for workspace-first automation. The current repository is intentionally minimal, with only foundational runtime pieces and no extra scaffolding layers.

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
```

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
