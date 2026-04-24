# Implementation Plan: ACP Adapter

**Branch**: `003-add-acp-adapter` | **Date**: 2026-04-23 | **Spec**: `/home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/spec.md`
**Input**: Feature specification from `/home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/spec.md`

## Summary

Deliver the first standard protocol integration by exposing StrandsClaw as an ACP agent over stdio, extracting adapter-agnostic workspace turn handling from the current CLI path, reusing existing bootstrap/session/file-scope behavior, advertising only the ACP capabilities needed for basic chat turns, and explicitly deferring any OpenAI-compatible endpoint while preserving a reusable internal adapter-runtime contract for future protocols.

## Technical Context

**Language/Version**: Python >= 3.11  
**Primary Dependencies**: `strands-agents==1.33.0`, `agent-client-protocol`, `pyyaml>=6.0`  
**Storage**: Existing file-backed JSON state under workspace `.state/` via `FileStateStore` and `SessionStore`  
**Testing**: `pytest` via `uv run pytest`, plus ACP protocol smoke/contract tests over stdio  
**Target Platform**: Local Linux/macOS developer workstation launched by an ACP-capable client over stdio  
**Project Type**: Pure Python workspace assistant runtime with CLI and stdio protocol adapter  
**Performance Goals**: ACP initialization adds negligible overhead over current chat startup, and each supported turn returns one final response without streaming or duplicate persistence work  
**Constraints**: One launch-bound workspace per process; basic text chat turns only in MVP; advertise only supported ACP capabilities; multiple ACP sessions map to one shared persisted workspace session; stdio is the first transport; OpenAI-compatible endpoint is deferred  
**Scale/Scope**: Single local operator process, one active workspace per ACP process, a small number of concurrent ACP client sessions, and one shared persisted workspace session per workspace  
**Bounded Context**: Protocol Integration Surface  
**DDD Impact**: Stays in the current minimal core. The feature needs a reusable adapter-facing runtime contract, but not separate `domain/` or `application/` packages. The new seam can live in focused `workspace/` and `infrastructure/` modules without speculative DDD scaffolding.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Driven Delivery**: PASS. The spec defines the bounded context, ubiquitous language, invariants, external boundaries, and independently testable stories.
- **Domain-Driven Boundaries**: PASS. The plan keeps ACP transport glue out of workspace/bootstrap/session rules by introducing an adapter-neutral runtime contract.
- **Minimal Structure**: PASS. No `domain/`, `application/`, `agents/`, or repository abstractions are introduced; the feature extends existing minimal-core areas only.
- **Observable Operations**: PASS. ACP capability advertisement, session binding, bootstrap, turn execution, and persistence behavior remain explicit and testable through deterministic contracts and structured runtime events.
- **Testable Increments**: PASS. The feature can ship in vertical slices covering runtime extraction, ACP session startup, prompt handling, and unsupported-capability/error behavior.
- **Invariant Enforcement**: PASS. INV-001..INV-005 map to explicit launch-workspace resolution, shared-session binding, capability advertisement, runtime contract boundaries, and future-adapter compatibility decisions.
- **Layer Ownership**: PASS. Ownership is explicit across interface launch surfaces, workspace runtime policy, and infrastructure protocol/state adapters.

## Project Structure

### Documentation (this feature)

```text
specs/003-add-acp-adapter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── acp-agent-contract.md
│   └── adapter-runtime-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
src/strandsclaw/
├── bootstrap/
│   └── init.py                         # Existing workspace bootstrap rules
├── interfaces/
│   ├── cli.py                          # Existing CLI delivery surface
│   └── acp.py                          # ACP launch entrypoint / command wiring
├── workspace/
│   ├── chat_runtime.py                 # Adapter-neutral workspace preparation + turn contract
│   ├── assistant_assets.py             # Existing assistant asset loading
│   ├── file_tool.py                    # Existing workspace file-read behavior
│   ├── prompt_assembly.py              # Existing prompt assembly
│   └── file_scope.py                   # Existing workspace boundary enforcement
├── infrastructure/
│   ├── acp/
│   │   ├── agent.py                    # ACP SDK adapter, capability advertisement, session handlers
│   │   └── mapping.py                  # ACP message/session translation
│   ├── observability.py                # Existing structured runtime events
│   └── state/
│       ├── file_state_store.py
│       └── session_store.py            # Existing shared workspace session persistence
└── config.py                           # Existing workspace/model configuration

tests/
├── test_chat_runtime.py                # Shared runtime behavior after extraction
├── test_acp_agent.py                   # ACP adapter startup, capability, and prompt flow
├── test_session_store.py               # Shared persisted session behavior
└── test_file_scope.py                  # Shared workspace boundary behavior
```

**Structure Decision**: Keep the minimal core. This feature adds a new delivery surface and a reusable adapter seam, not a rich business domain that justifies separate `domain/` or `application/` packages. The core rules remain operational and can be enforced by a focused workspace runtime module plus thin ACP translation in infrastructure/interface code.

## Layer Ownership Map

- **Interfaces**: Launch surfaces only. `interfaces/cli.py` remains operator-facing CLI entry, and `interfaces/acp.py` exposes the ACP process command without embedding workspace/session rules.
- **Workspace**: Owns adapter-neutral runtime behavior for workspace resolution, bootstrap-before-use, prompt assembly, file-scope enforcement, and turn execution.
- **Bootstrap**: Continues to own idempotent workspace materialization of required assistant assets.
- **Infrastructure**: Owns ACP SDK integration, session/message mapping, structured runtime events, and file-backed session persistence.
- **Domain/Application**: Not introduced in this feature; additional layers would be speculative because the new complexity is transport integration, not a new domain model.

## Phase Plan

### Phase 0: Research

- Confirm ACP MVP transport and dependency choice for a pure Python runtime.
- Define the minimum ACP capability set that satisfies basic chat turns without overstating support.
- Define how multiple ACP sessions map to the existing single shared workspace session.
- Define the adapter-runtime contract that future transports can reuse without carrying ACP-specific types into core runtime code.
- Define actionable error behavior for bootstrap failure, unreadable persisted session recovery, unsupported ACP operations, and model unavailability.

### Phase 1: Design

- Define data models for protocol sessions, shared workspace runtime context, advertised capability set, adapter turn requests, and turn outcomes.
- Define ACP-facing and internal adapter-runtime contracts, including explicit non-goals for streaming, attachments, and client-managed session persistence.
- Create a quickstart covering ACP launch, client connection, reconnect behavior, and failure-path validation.
- Update Copilot planning context to point at this feature plan.

### Phase 2: Implementation Preview (for `/speckit.tasks`)

- Slice A (P1): Extract adapter-neutral workspace preparation and turn execution out of the CLI path into a shared runtime module.
- Slice B (P1): Add ACP stdio launch surface, agent initialization, and minimum capability advertisement for supported session methods.
- Slice C (P2): Bind ACP protocol sessions to the existing shared workspace session while preserving bootstrap, file-scope, and persisted-session behavior.
- Slice D (P2): Add actionable ACP error mapping and explicit unsupported-capability handling for non-MVP protocol features.
- Slice E (P3): Harden the adapter-runtime contract and tests so future transports, including an OpenAI-compatible endpoint, can reuse the same core turn behavior without redesign.

## Post-Design Constitution Check

- **Spec-Driven Delivery**: PASS. The design artifacts align to the feature spec, clarify MVP boundaries, and preserve future-adapter expectations.
- **Domain-Driven Boundaries**: PASS. ACP transport responsibilities stay in delivery/infrastructure code, while runtime rules stay in adapter-neutral workspace modules.
- **Minimal Structure**: PASS. The design adds only a focused ACP adapter package and a shared runtime module; `domain/` and `application/` remain unjustified.
- **Observable Operations**: PASS. Capability advertisement, ACP session binding, model-unavailable outcomes, and persisted-session reuse are documented as deterministic, inspectable behavior.
- **Testable Increments**: PASS. Each implementation slice can be validated independently with unit and ACP contract tests.
- **Invariant Enforcement**: PASS. Every invariant is represented by a planned guard, policy, or capability decision in the design artifacts.
- **Layer Ownership**: PASS. Module ownership is explicit and avoids placing business rules in ACP glue or state adapters.

## Complexity Tracking

No constitution violations requiring justification.
