# StrandsClaw: Workspace-First Implementation Plan

## Purpose

Build a personal assistant platform similar to OpenClaw behavior, where the assistant acts on a user workspace with durable, file-based memory and operational docs.

This plan prioritizes workspace architecture first, then assistant behavior on top of that workspace contract.

## Core Product Model

StrandsClaw has two clearly separated parts:

- Software runtime: the Python application code in this repository.
- User workspace: a separate directory containing identity, memory, task context, and local operational notes.

During development, a repo-local `.workspace/` directory is used for convenience and is gitignored.
In normal usage, workspace defaults to an external location such as `~/strandsclaw`.

## Workspace Strategy

### Workspace Modes

- Dev mode: `<repo>/.workspace`
- User mode: `~/strandsclaw` (default target)

### Path Resolution Order

1. Explicit CLI argument (for example `--workspace-path /path`)
2. Environment variable (for example `STRANDSCLAW_WORKSPACE`)
3. Dev default when running from repository (`.workspace`)
4. User default (`~/strandsclaw`)

### Persistence Policy

- Workspace is the durable source for identity and memory files.
- Runtime state cache can remain in `.state/` for software concerns, but assistant continuity belongs in workspace memory files.
- Bootstrap is idempotent and does not overwrite existing user-edited files unless explicitly forced.

## Template Workspace (OpenClaw-Inspired)

The repository ships a template workspace skeleton that can be materialized into any target path.

### Proposed Template Layout

```text
workspace-template/
├── AGENTS.md
├── BOOT.md
├── BOOTSTRAP.md
├── IDENTITY.md
├── USER.md
├── TOOLS.md
├── SOUL.md
├── HEARTBEAT.md
├── MEMORY.md
└── memory/
    └── .gitkeep
```

Notes:

- `memory/YYYY-MM-DD.md` files are created at runtime.
- `MEMORY.md` is curated long-term memory.
- `TOOLS.md` stores local environment notes specific to the user machine.

## Current Baseline (Already Done)

- Python 3.11 project managed with `uv`
- DDD package scaffold under `src/strandsclaw`
- CLI entrypoint in `src/strandsclaw/interfaces/cli.py`
- Supervisor wiring in `src/strandsclaw/agents/supervisor.py`
- File-backed store in `src/strandsclaw/infrastructure/state/file_state_store.py`
- Plugin hooks/tools in `src/strandsclaw/infrastructure/plugins`
- Runtime skills in top-level `skills/`
- Commands via `Makefile` and `uv`

## Revised Technical Choices

### 1) Skills Integration

Use `strands.vended_plugins.skills.agent_skills.AgentSkills` with top-level `skills/`.

Reason:

- Matches installed API and current implementation.
- Avoids custom parallel skill systems.

### 2) Runtime and Tooling

Use `uv` for dependency and execution workflows. Keep application runtime pure Python.

Reason:

- Stable local and CI behavior.
- Aligned with Spec Kit and current repo conventions.

### 3) Architecture Boundaries

- Domain: no Strands, no filesystem, no CLI parsing
- Application: orchestrates use cases and workflows
- Infrastructure: Strands plugins, adapters, persistence, workspace IO
- Interfaces: CLI and command surfaces

Reason:

- Maintains clear boundaries and independent testability.

## Execution Roadmap

### Phase 0: Spec Kit Discipline

Goal:

- Ensure meaningful work is driven by `specs/<feature>/` artifacts.

Deliverables:

- Updated constitution and first feature artifacts for workspace bootstrap.

Exit Criteria:

- Non-trivial changes require spec/plan/tasks before implementation.

### Phase 1: Workspace Contract and Template

Goal:

- Define and implement workspace as a first-class product boundary.

Scope:

- Create `workspace-template/` with OpenClaw-inspired files.
- Add `.workspace/` to `.gitignore` for local development usage.
- Define path resolution and workspace config model.
- Add bootstrap command behavior for template materialization.

Exit Criteria:

- `bootstrap` can initialize a fresh workspace at a chosen path without clobbering user content.

### Phase 2: Assistant Startup and Memory Flow

Goal:

- Ensure startup behavior reads workspace context consistently.

Scope:

- Add startup rules for reading identity/user/memory files.
- Add daily memory file creation/update helpers.
- Keep long-term memory updates explicit and testable.

Exit Criteria:

- Assistant can restart and retain continuity from workspace files.

### Phase 3: Supervisor Hardening

Goal:

- Stabilize supervisor behavior now that workspace substrate exists.

Scope:

- Harden plugin wiring, error handling, and observability.
- Add focused tests around tool and hook failure paths.

Exit Criteria:

- Supervisor lifecycle is deterministic and observable.

### Phase 4: Feature Delivery Loop

Goal:

- Ship high-value assistant features in vertical slices.

Scope:

- For each feature: `/speckit.specify` -> `/speckit.clarify` -> `/speckit.plan` -> `/speckit.tasks` -> implementation.
- Prioritize user-visible behaviors over broad scaffolding.

Exit Criteria:

- At least one end-to-end user workflow operates fully in external workspace mode.

### Phase 5: Runtime Ops (Optional)

Goal:

- Introduce deployment/scheduling only when validated by use.

Scope:

- Optional Docker packaging.
- Optional scheduler and heartbeat automation.

Exit Criteria:

- Added only when it improves real operation, not preemptively.

## Success Metrics

- `make test` remains green as coverage grows.
- Workspace can be initialized in both `.workspace/` and `~/strandsclaw`.
- Workspace bootstrap is idempotent and non-destructive by default.
- Assistant continuity survives process restarts using workspace files.
- Feature work remains traceable to Spec Kit artifacts.

## Immediate Next Steps

1. Create first feature spec for workspace bootstrap and path resolution.
2. Generate plan/tasks for template materialization and idempotent file initialization.
3. Implement and test `.workspace` dev mode plus external workspace default behavior.
