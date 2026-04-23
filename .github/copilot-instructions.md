# Project Guidelines

Primary project guidance lives in `AGENTS.md`. Keep this file aligned with it and use it for Copilot-specific defaults.

## Architecture
StrandsClaw is a pure Python Strands project with a minimal core under `src/strandsclaw`.
Current focus areas are `interfaces`, `bootstrap`, `workspace`, and `infrastructure/state`.
Introduce additional architecture layers only when an active feature needs them.
The `workspace-template/` directory contains starter workspace assets, including default skills.
Runtime skills are read from the active workspace path, not from repo root.
The `specs/` directory contains Spec Kit feature artifacts and should drive implementation work.

## Build and Test
Use `uv sync` to install dependencies.
Use `uv run pytest` to run tests.
Use `uv run strandsclaw bootstrap` to initialize runtime directories and materialize workspace templates.

## Conventions
Keep runtime code lean and remove scaffolding not tied to current features.
Place durable file-backed state behavior in `src/strandsclaw/infrastructure/state`.
Use file-backed JSON state through the shared state store rather than ad hoc persistence.
Prefer spec-backed, incremental changes over broad scaffolding.
During `/speckit.specify`, define bounded context, ubiquitous language, invariants, and external boundaries.
During `/speckit.plan`, decide whether the feature stays within the minimal core or justifies `domain/` and `application/` layers.
During implementation, keep business rules out of CLI, Strands integration glue, and persistence adapters.
Only add DDD layers when the active feature requires them, and justify the addition in the plan and tasks artifacts.

## DDD Enforcement Checklist

For meaningful feature work, Copilot MUST verify and preserve the following:

1. `spec.md` names bounded context, ubiquitous language, invariants, and external boundaries.
2. `plan.md` includes an explicit decision on whether the feature stays in the minimal core or adds `domain/` and `application/`.
3. Business rules are not implemented in CLI glue, Strands integration glue, or persistence adapters.
4. Domain invariants are reflected in code paths that enforce or validate them.
5. Changes that alter domain logic, state transitions, or persistence behavior include targeted tests.

Copilot SHOULD block or revise proposals that introduce speculative DDD scaffolding or place domain behavior in infrastructure or interface modules.

## Security and Privacy
This is a public repository: do not commit secrets, API keys, tokens, passwords, private keys, or machine-specific absolute paths.
Use portable relative paths and environment variables for local configuration.
When editing config and docs, sanitize user-specific values before commit.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
