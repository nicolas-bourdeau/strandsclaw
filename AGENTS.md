# Project Guidelines

## Architecture

StrandsClaw is a pure Python Strands project with a deliberately minimal core under `src/strandsclaw`.
Current first-class areas are `interfaces`, `bootstrap`, `workspace`, and `infrastructure/state`.
Add additional layers (for example, full DDD segmentation) only when a concrete feature requires them.
The `workspace-template/` directory contains starter workspace assets, including default skills.
Runtime skills are resolved from the active workspace path (for example `.workspace/skills` in dev mode).
The top-level `specs/` directory is reserved for Spec Kit feature artifacts.

## Workflow

Use Spec Kit for meaningful feature work.
Create or update constitution, specification, clarification, plan, and tasks artifacts before large implementation changes.
Treat `project_plan.md` as background context, but let `specs/<feature>/` become the source of truth for active work.
When a change affects architecture or conventions, update this file, `.github/copilot-instructions.md`, and the relevant spec artifacts together.

## Build And Test

Use `uv sync` to install project dependencies.
Use `uv run pytest` for tests.
Use `uv run strandsclaw bootstrap` to create runtime directories and materialize `workspace-template/` assets.
Use `uv run strandsclaw list-skills` to confirm the local `skills/` catalog is discoverable.

## Conventions

Prefer explicit dataclasses or plain typed objects for configuration and data records.
Avoid adding framework-specific wrappers before they are needed.
Use JSON-serializable state in `.state/` through the file-backed store instead of ad hoc files.
When adding tools or hooks later, keep them isolated in infrastructure adapters.
When adding new default skills, place them in `workspace-template/skills/<skill-name>/SKILL.md`.

## Public Repo Hygiene

This repository is public: never commit secrets, tokens, passwords, API keys, private keys, or machine-specific absolute paths.
Prefer portable relative paths and environment-variable-driven configuration over user- or host-specific values.
Before creating PRs or releases, scan changed files for sensitive data patterns and remove anything unsafe.
