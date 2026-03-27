<!--
Sync Impact Report
- Version change: 1.1.0 -> 1.1.1
- Modified principles:
	- I. Spec-Driven Delivery -> I. Spec-Driven Delivery (clarified scope and backfill rule)
	- V. Testable Increments -> V. Testable Increments (tightened testing requirement for behavior changes)
- Added sections: none
- Removed sections: none
- Templates requiring updates:
	- ✅ /home/nbourdeau/dev/strandsclaw/.specify/templates/plan-template.md (reviewed, aligned)
	- ✅ /home/nbourdeau/dev/strandsclaw/.specify/templates/spec-template.md (reviewed, aligned)
	- ✅ /home/nbourdeau/dev/strandsclaw/.specify/templates/tasks-template.md (reviewed, aligned)
	- ⚠ /home/nbourdeau/dev/strandsclaw/.specify/templates/commands/*.md (directory not present in this repository)
- Deferred items: none
-->

# StrandsClaw Constitution

## Core Principles

### I. Spec-Driven Delivery

All meaningful feature work MUST start with Spec Kit artifacts in `specs/`. Work MUST progress through constitution, specification, clarification, plan, tasks, analysis, and implementation in that order. Code-first changes are allowed only for trivial fixes or toolchain repairs and MUST be reflected back into specs before merge when they affect behavior.

### II. Domain-Driven Boundaries

Domain code MUST remain framework-agnostic and isolated from Strands, CLI parsing, filesystem access, and transport details. Application services coordinate use cases. Infrastructure owns adapters, plugins, persistence, and external integrations. Interfaces expose delivery surfaces and must not embed domain rules.

Every meaningful feature MUST name its bounded context, define the core domain language it introduces or extends, and document the invariants that protect business behavior. New aggregates, repositories, domain services, or domain events MUST be justified by the feature plan rather than added speculatively.

### III. Pure Python Runtime

The production codebase MUST remain pure Python and target Python 3.11 or newer. New runtime dependencies MUST be justified by a clear capability gap and recorded in project docs. Tooling may use external executables, but the runtime path for core features MUST remain Python-first.

### IV. Observable Agent Operations

Agent behavior MUST be inspectable through structured logging, explicit tool registration, and file-backed state with deterministic serialization. Hidden side effects, implicit persistence, and opaque cross-layer mutations are not acceptable.

### V. Testable Increments

Every implemented slice MUST be independently testable and aligned with a user-visible or operator-visible outcome. Any change that introduces or modifies domain logic, invariants, state transitions, or persistence behavior MUST include targeted tests before broader orchestration is expanded.

## Architecture Boundaries

The canonical source layout is `src/strandsclaw/`.

The repository starts with a minimal core under `bootstrap/`, `interfaces/`, `workspace/`, and `infrastructure/state`. Additional DDD-oriented modules are introduced only when an active feature needs them and the plan justifies the split.

When a feature requires richer separation, the following responsibilities apply:

- `domain/`: entities, value objects, domain services, and invariants
- `application/`: use-case orchestration and coordination across domain and infrastructure
- `infrastructure/`: Strands plugins, persistence, external integrations, and adapter implementations
- `interfaces/`: CLI and other delivery surfaces
- `agents/`: agent assembly when agent construction grows beyond interface wiring

The `skills/` directory is a runtime asset, not a Python package. The `specs/` directory is a product-development asset, not runtime state.

## Delivery Workflow

Use `uv` for dependency and environment management.
Use `uv run pytest` as the baseline quality gate.
When introducing a new bounded context or plugin, document the change in `AGENTS.md`, `.github/copilot-instructions.md`, and the active spec artifacts.
During specification, capture bounded context, ubiquitous language, invariants, and external boundaries before implementation planning.
During planning, map responsibilities across `domain`, `application`, `infrastructure`, and `interfaces`, and justify any new layers that will be added.
During task generation, organize work into independently testable vertical slices and keep business rules separate from adapters and delivery code.
Prefer minimal vertical slices over scaffolding every future phase at once.

## Governance

This constitution supersedes ad hoc local preferences for repository-wide decisions.
Amendments MUST be proposed in writing, include rationale and impact, and update the affected guidance files in the same change (`AGENTS.md`, `.github/copilot-instructions.md`, and relevant Spec Kit templates when applicable).
Versioning policy for this constitution follows semantic versioning:
- MAJOR: backward-incompatible governance or principle removals/redefinitions.
- MINOR: new principle or materially expanded mandatory guidance.
- PATCH: clarifications, wording fixes, and non-semantic refinements.
Compliance review expectations:
- Every plan MUST pass the Constitution Check before Phase 0 research and again after Phase 1 design.
- Code review and agent-driven changes MUST verify compliance with DDD boundaries, spec-driven workflow, observability expectations, and testable increments.
**Version**: 1.1.1 | **Ratified**: 2026-03-27 | **Last Amended**: 2026-03-27
