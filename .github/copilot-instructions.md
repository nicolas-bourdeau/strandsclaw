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

## Security and Privacy
This is a public repository: do not commit secrets, API keys, tokens, passwords, private keys, or machine-specific absolute paths.
Use portable relative paths and environment variables for local configuration.
When editing config and docs, sanitize user-specific values before commit.
