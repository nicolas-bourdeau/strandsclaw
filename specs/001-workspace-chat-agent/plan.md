# Implementation Plan: Workspace Chat Agent

**Branch**: `001-workspace-chat-agent` | **Date**: 2026-03-27 | **Spec**: `/home/nbourdeau/dev/strandsclaw/specs/001-workspace-chat-agent/spec.md`
**Input**: Feature specification from `/home/nbourdeau/dev/strandsclaw/specs/001-workspace-chat-agent/spec.md`

## Summary

Deliver the first end-to-end workspace assistant runtime as a minimal CLI vertical slice: resolve workspace, bootstrap missing assistant assets, restore/create a single persisted session, assemble prompt context from workspace files, provide workspace-scoped read-file support, and generate chat responses through local Ollama (`qwen3.5:latest`, 64k context) while keeping the chat loop available and returning actionable per-turn errors if the model runtime is unavailable.

## Technical Context

**Language/Version**: Python >= 3.11  
**Primary Dependencies**: `strands-agents==1.33.0`, `pyyaml>=6.0`  
**Storage**: File-backed JSON state under workspace `.state/` using `FileStateStore`  
**Testing**: `pytest` via `uv run pytest`  
**Target Platform**: Local Linux/macOS developer workstation with local Ollama service  
**Project Type**: CLI runtime (pure Python package)  
**Performance Goals**: First response from empty/missing workspace in <60s excluding model download time (SC-001)  
**Constraints**: Single active session per workspace; read-file only inside workspace; text files only; max 64 KB per read; preserve user-authored files during bootstrap; startup must succeed even when Ollama/model access is unavailable  
**Scale/Scope**: Single local operator, one active workspace per process, one persisted session per workspace  
**Bounded Context**: Workspace Assistant Runtime  
**DDD Impact**: Remains in minimal core (`bootstrap`, `interfaces`, `workspace`, `infrastructure/state`). No new `domain/` or `application/` layer is justified for this MVP because invariants are narrow, explicit, and enforceable in focused service modules within existing areas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Driven Delivery**: PASS. Spec includes bounded context, ubiquitous language, invariants, user stories, and measurable criteria.
- **Domain-Driven Boundaries**: PASS. Plan keeps CLI as delivery-only, with bootstrap/session/file-scope policies in non-CLI modules.
- **Minimal Structure**: PASS. No speculative `domain/`, `application/`, `agents/`, or repository abstractions added.
- **Observable Operations**: PASS. Bootstrap output, state file changes, session archive events, file-read denials, and model-unavailable turn failures remain deterministic and inspectable.
- **Testable Increments**: PASS. Vertical slices align to startup/bootstrap, session continuity/recovery, and file-read boundary enforcement.
- **Invariant Enforcement**: PASS. INV-001..INV-005 each map to guards in workspace resolution, bootstrap merge policy, path confinement, single-session keys, and archive-on-recovery.
- **Layer Ownership**: PASS. Ownership is explicit across interface, workspace/bootstrap logic, and infrastructure state adapters.

## Project Structure

### Documentation (this feature)

```text
specs/001-workspace-chat-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-chat-contract.md
│   └── state-file-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
src/strandsclaw/
├── bootstrap/
│   └── init.py                         # Bootstrap materialization + bootstrap-time prompt use
├── interfaces/
│   └── cli.py                          # Start chat command and operator I/O loop
├── workspace/
│   ├── assistant_assets.py             # Load AGENTS/IDENTITY/SOUL contract files
│   ├── prompt_assembly.py              # Assemble normal-turn prompt context
│   ├── file_scope.py                   # Workspace boundary + 64 KB text read policy
│   └── skill_catalog.py
├── infrastructure/
│   └── state/
│       ├── file_state_store.py
│       └── session_store.py            # Single-session persist/load/archive behavior
└── config.py                           # Default model profile + override-ready config

tests/
├── test_bootstrap.py
├── test_chat_runtime.py
├── test_session_store.py
└── test_file_scope.py
```

**Structure Decision**: Keep the minimal core. This feature introduces runtime behavior, not a broad domain model requiring separate `domain/` and `application/` packages. Invariants are enforced by focused policy modules in `workspace/` and `infrastructure/state/`, while `interfaces/cli.py` only orchestrates user input/output and command routing.

## Layer Ownership Map

- **Interfaces**: CLI argument parsing, chat loop entrypoint, user-facing rendering of errors/responses, including recoverable model-unavailable turn failures.
- **Workspace**: Assistant asset contract, prompt assembly, workspace path confinement decisions for file reads.
- **Bootstrap**: Idempotent creation/materialization of required default assets without overwrites.
- **Infrastructure**: File-backed session persistence, JSON serialization, archive of unreadable session records.
- **Domain/Application**: Not introduced in this feature; complexity does not justify additional layers.

## Phase Plan

### Phase 0: Research

- Confirm Ollama model profile wiring through `strands-agents` for default provider/model/context.
- Define runtime behavior when Ollama/model access is unavailable after startup succeeds.
- Define robust file-scope policy for traversal/symlink escape prevention and binary detection.
- Define single-session recovery strategy for corrupted state with archive-before-recreate behavior.

### Phase 1: Design

- Define data model for workspace runtime, assistant session, archived record, chat turn, and model profile.
- Define CLI and state-file contracts for startup, resume/recovery, file-read policy errors, and per-turn model-unavailable errors.
- Create quickstart for operator validation across happy path and edge-case scenarios.

### Phase 2: Implementation Preview (for `/speckit.tasks`)

- Slice A (P1): chat start + single-session load/save + prompt assembly.
- Slice B (P2): missing/empty workspace bootstrap with non-overwrite asset materialization.
- Slice C (P3): workspace-scoped file read tool with 64 KB text-only limit and denial paths.
- Slice D: model/runtime outage handling that preserves startup/chat loop availability and returns actionable per-turn errors.

## Post-Design Constitution Check

- **Spec-Driven Delivery**: PASS. Design artifacts align to spec language and invariants.
- **Domain-Driven Boundaries**: PASS. No business logic placed in CLI parsing or raw state adapter methods.
- **Minimal Structure**: PASS. Additional layers still unjustified after design.
- **Observable Operations**: PASS. Contracted state files, deterministic bootstrap/session flows, and model-unavailable turn outcomes are documented.
- **Testable Increments**: PASS. Each slice has independent acceptance/testing path.
- **Invariant Enforcement**: PASS. Invariants mapped to explicit policies in data model/contracts.
- **Layer Ownership**: PASS. Ownership matrix preserved without cross-layer leakage.

## Complexity Tracking

No constitution violations requiring justification.
