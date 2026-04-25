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
During specification, capture bounded context, ubiquitous language, invariants, and external boundaries for the feature.
During planning, decide whether the feature can stay within the minimal core or whether it justifies explicit `domain/` and `application/` layers.
During task generation and implementation, keep work organized as independently testable vertical slices.
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
Keep business rules out of CLI handlers, workspace bootstrapping, and persistence adapters.
Introduce `src/strandsclaw/domain` only when a feature needs explicit domain types, invariants, or services.
Introduce `src/strandsclaw/application` only when use-case orchestration becomes distinct from interface or infrastructure concerns.
Infrastructure may depend on domain types; domain code must not depend on infrastructure or interface modules.

## DDD Enforcement Checklist

For any meaningful feature, reviewers and AI agents MUST confirm all items below before merge:

1. Bounded context is named in `specs/<feature>/spec.md` and carried into `plan.md`.
2. Ubiquitous language terms are defined and used consistently in specs and code naming.
3. Domain invariants are explicit and mapped to validations or guards in implementation.
4. Business rules live in domain or application code, never in CLI handlers, workspace bootstrap, or state adapters.
5. If `domain/` or `application/` is introduced or expanded, the plan explains why minimal-core placement is insufficient.
6. State-changing behavior has targeted tests that validate invariants and transitions.

The following are forbidden without explicit plan justification:

- Anemic "domain" files that only mirror transport or persistence models.
- Feature logic embedded directly in `interfaces/`, `bootstrap/`, or `infrastructure/state/`.
- New repositories or services added because of anticipated future use instead of active requirements.

## Public Repo Hygiene

This repository is public: never commit secrets, tokens, passwords, API keys, private keys, or machine-specific absolute paths.
Prefer portable relative paths and environment-variable-driven configuration over user- or host-specific values.
Before creating PRs or releases, scan changed files for sensitive data patterns and remove anything unsafe.

## Active Technologies
- Python >= 3.11 + `strands-agents==1.33.0`, `agent-client-protocol`, `pyyaml>=6.0` (003-add-acp-adapter)
- Existing file-backed JSON state under workspace `.state/` via `FileStateStore` and `SessionStore` (003-add-acp-adapter)

## Recent Changes
- 003-add-acp-adapter: Added Python >= 3.11 + `strands-agents==1.33.0`, `agent-client-protocol`, `pyyaml>=6.0`
