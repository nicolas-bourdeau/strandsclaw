<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles: placeholder template -> concrete project principles
- Added sections: Architecture Boundaries, Delivery Workflow
- Removed sections: none
- Templates requiring updates: ✅ `.github/copilot-instructions.md`, ⚠ `README.md` is aligned by prose rather than template mutation
- Deferred items: none
-->

# StrandsClaw Constitution

## Core Principles

### I. Spec-Driven Delivery

All meaningful feature work MUST start with Spec Kit artifacts in `specs/`. Work SHOULD progress through constitution, specification, clarification, plan, tasks, analysis, and implementation in that order. Code-first changes are allowed only for trivial fixes or toolchain repairs and MUST be reflected back into specs when they affect behavior.

### II. Domain-Driven Boundaries

Domain code MUST remain framework-agnostic and isolated from Strands, CLI parsing, filesystem access, and transport details. Application services coordinate use cases. Infrastructure owns adapters, plugins, persistence, and external integrations. Interfaces expose delivery surfaces and must not embed domain rules.

### III. Pure Python Runtime

The production codebase MUST remain pure Python and target Python 3.11 or newer. New runtime dependencies MUST be justified by a clear capability gap and recorded in project docs. Tooling may use external executables, but the runtime path for core features MUST remain Python-first.

### IV. Observable Agent Operations

Agent behavior MUST be inspectable through structured logging, explicit tool registration, and file-backed state with deterministic serialization. Hidden side effects, implicit persistence, and opaque cross-layer mutations are not acceptable.

### V. Testable Increments

Every implemented slice MUST be independently testable and aligned with a user-visible or operator-visible outcome. New modules SHOULD ship with targeted tests for domain logic, state handling, or construction paths before broader orchestration is expanded.

## Architecture Boundaries

The canonical source layout is `src/strandsclaw/` with the following responsibilities:

- `domain/`: entities, value objects, and rules
- `application/`: orchestration and use-case services
- `infrastructure/`: Strands plugins, persistence, and adapters
- `interfaces/`: CLI and external entry points
- `agents/`: agent classes and assembly

The `skills/` directory is a runtime asset, not a Python package. The `specs/` directory is a product-development asset, not runtime state.

## Delivery Workflow

Use `uv` for dependency and environment management.
Use `uv run pytest` as the baseline quality gate.
When introducing a new bounded context or plugin, document the change in `AGENTS.md`, `.github/copilot-instructions.md`, and the active spec artifacts.
Prefer minimal vertical slices over scaffolding every future phase at once.

## Governance

This constitution supersedes ad hoc local preferences for repository-wide decisions.
Changes to these principles require a documented rationale and an update to the affected guidance files.
Code review and agent-driven changes MUST verify compliance with DDD boundaries, spec-driven workflow, and testable increments.
**Version**: 1.0.0 | **Ratified**: 2026-03-27 | **Last Amended**: 2026-03-27 <!-- End of constitution -->
<!-- EOF -->
<!-- EOF-2 -->

