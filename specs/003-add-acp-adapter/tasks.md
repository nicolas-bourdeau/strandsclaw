# Tasks: ACP Adapter

**Input**: Design documents from `/specs/003-add-acp-adapter/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Include targeted pytest coverage for runtime extraction, ACP startup/prompt flow, shared-session reuse, and adapter-seam invariants because the feature changes runtime behavior, persistence semantics, and protocol-visible contracts.

**Organization**: Tasks are grouped by user story so each slice stays independently testable while keeping the feature in the minimal core under `interfaces/`, `workspace/`, and `infrastructure/` only.

## Phase 1: Setup

**Purpose**: Add the ACP dependency and operator-facing command surface prerequisites needed before shared runtime extraction starts.

- [ ] T001 Add the `agent-client-protocol` dependency and ACP script wiring expectations in /home/nbourdeau/dev/strandsclaw/pyproject.toml
- [ ] T002 [P] Add the planned `strandsclaw acp --workspace-path` operator entrypoint documentation in /home/nbourdeau/dev/strandsclaw/README.md

---

## Phase 2: Foundational

**Purpose**: Establish the shared adapter-neutral runtime seam and invariants that block all user stories.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [ ] T003 Extract shared workspace runtime types and operations into /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py
- [ ] T004 [P] Create the ACP adapter package export surface in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/\_\_init\_\_.py
- [ ] T005 [P] Add transport-neutral ACP translation helpers in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/mapping.py
- [ ] T006 Add foundational runtime-seam and invariant regression coverage in /home/nbourdeau/dev/strandsclaw/tests/test_chat_runtime.py and /home/nbourdeau/dev/strandsclaw/tests/test_session_store.py
- [ ] T007 Refactor CLI chat flow to delegate bootstrap, session loading, and turn execution through /home/nbourdeau/dev/strandsclaw/src/strandsclaw/interfaces/cli.py and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py

**Checkpoint**: Foundation ready. The repo now has one shared runtime seam for launch-bound workspace resolution, shared workspace session semantics, and final turn outcomes.

---

## Phase 3: User Story 1 - Connect a Standard ACP Client (Priority: P1) 🎯 MVP

**Goal**: Let a standard ACP-capable client launch StrandsClaw over stdio, create a session for the launch-bound workspace, and receive one final completed response for a basic text prompt.

**Independent Test**: Launch `strandsclaw acp --workspace-path <workspace>` from an ACP-capable client, create a session, send a text prompt, and verify the client receives one normal final response without any client-specific glue.

### Tests for User Story 1

- [ ] T008 [US1] Add ACP startup, capability advertisement, and prompt contract tests in /home/nbourdeau/dev/strandsclaw/tests/test_acp_agent.py

### Implementation for User Story 1

- [ ] T009 [US1] Add ACP command routing for `strandsclaw acp --workspace-path` in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/interfaces/cli.py and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/interfaces/acp.py
- [ ] T010 [P] [US1] Implement ACP stdio agent initialization and `session/new` handling in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py
- [ ] T011 [P] [US1] Implement ACP text prompt and final response mapping in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/mapping.py
- [ ] T012 [US1] Route ACP `session/prompt` execution through /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py
- [ ] T013 [US1] Reject unsupported non-MVP ACP capabilities and non-text payloads explicitly in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py

**Checkpoint**: User Story 1 is complete when ACP discovery, session creation, and one final completed chat turn work through the launch-bound workspace.

---

## Phase 4: User Story 2 - Preserve Workspace Assistant Behavior Through the Adapter (Priority: P2)

**Goal**: Ensure ACP-served turns preserve bootstrap, shared workspace session reuse, disconnect safety, workspace-bound file rules, and actionable recovery behavior.

**Independent Test**: Connect through ACP to a prepared workspace, perform multiple turns, reconnect, disconnect during an in-flight turn, and confirm bootstrap, shared-session reuse, disconnect safety, and file-scope refusals behave the same as the native runtime.

### Tests for User Story 2

- [ ] T014 [US2] Add ACP bootstrap, reconnect, disconnect-safety, and shared workspace session reuse tests in /home/nbourdeau/dev/strandsclaw/tests/test_acp_agent.py
- [ ] T015 [P] [US2] Add unreadable-session archive-and-recovery coverage for ACP flows in /home/nbourdeau/dev/strandsclaw/tests/test_session_store.py
- [ ] T016 [P] [US2] Add structured ACP capability, session, and turn observability checks in /home/nbourdeau/dev/strandsclaw/tests/test_acp_agent.py

### Implementation for User Story 2

- [ ] T017 [US2] Preserve bootstrap-before-first-turn and shared workspace session loading in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py
- [ ] T018 [US2] Bind multiple ACP protocol sessions to the single persisted workspace session in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py
- [ ] T019 [US2] Preserve file-scope refusals, disconnect safety, and actionable model, bootstrap, and session-recovery outcomes in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/mapping.py
- [ ] T020 [US2] Emit structured ACP capability, session, and turn runtime events in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py

**Checkpoint**: User Story 2 is complete when ACP behaves like the native runtime for bootstrap, shared-session continuity, and workspace safety.

---

## Phase 5: User Story 3 - Extend the Integration Surface Safely (Priority: P3)

**Goal**: Keep ACP-specific transport glue isolated so future adapters can reuse the same minimal-core runtime seam without adding `domain/` or `application/` layers.

**Independent Test**: Review the adapter runtime contract and regression tests to confirm future transports can call the same workspace runtime operations without ACP-specific business logic leaking into the core.

### Tests for User Story 3

- [ ] T021 [US3] Add adapter-runtime seam regression tests for future transport reuse in /home/nbourdeau/dev/strandsclaw/tests/test_chat_runtime.py

### Implementation for User Story 3

- [ ] T022 [US3] Finalize transport-neutral runtime request, outcome, and disconnect semantics in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/workspace/chat_runtime.py
- [ ] T023 [US3] Keep ACP transport glue isolated from core runtime rules in /home/nbourdeau/dev/strandsclaw/src/strandsclaw/interfaces/acp.py, /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/agent.py, and /home/nbourdeau/dev/strandsclaw/src/strandsclaw/infrastructure/acp/mapping.py

**Checkpoint**: User Story 3 is complete when the ACP adapter proves the reusable seam without broadening scope beyond ACP, launch-bound workspace semantics, basic chat turns, final completed responses, and the shared single workspace session model.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story documentation and validation after all desired user stories are complete.

- [ ] T024 [P] Update deferred OpenAI-compatible scope and reusable seam wording in /home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/quickstart.md and /home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/contracts/adapter-runtime-contract.md
- [ ] T025 Validate operator-facing ACP usage and capability documentation against ACP contract responses and quickstart examples in /home/nbourdeau/dev/strandsclaw/README.md and /home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/contracts/acp-agent-contract.md
- [ ] T026 Validate ACP startup timing on the local quickstart baseline and confirm that each supported turn persists exactly one final assistant response in /home/nbourdeau/dev/strandsclaw/specs/003-add-acp-adapter/quickstart.md and /home/nbourdeau/dev/strandsclaw/tests/test_acp_agent.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** starts immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all user stories.
- **Phase 3: User Story 1** depends on Phase 2 and delivers the MVP ACP path.
- **Phase 4: User Story 2** depends on Phase 2 and the ACP launch surface from User Story 1.
- **Phase 5: User Story 3** depends on Phase 2 and should build on the shared runtime seam established for User Story 1.
- **Phase 6: Polish** depends on the user stories selected for delivery.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after the foundational seam is in place.
- **User Story 2 (P2)**: Builds on the ACP command and session surface from User Story 1 while staying independently testable for bootstrap and session reuse.
- **User Story 3 (P3)**: Builds on the same runtime seam and can start once the foundational seam is stable, but is safest after User Story 1 proves the adapter path.

### Parallel Opportunities

- `T002` can run in parallel with `T001` because it touches only /home/nbourdeau/dev/strandsclaw/README.md.
- `T004` and `T005` can run in parallel after `T003` because they create ACP package scaffolding and mapping helpers in separate files.
- `T010` and `T011` can run in parallel after `T009` because session initialization and prompt/result mapping live in separate ACP files.
- `T014`, `T015`, and `T016` can run in parallel because ACP reconnect/disconnect tests, session-recovery tests, and observability checks touch distinct validation concerns.
- `T024` and `T025` can run in parallel in the polish phase because they update separate documentation surfaces.

---

## Parallel Example: User Story 1

```bash
# Parallel ACP implementation after command routing exists
Task: T010 Implement ACP stdio agent initialization and session/new handling in src/strandsclaw/infrastructure/acp/agent.py
Task: T011 Implement ACP text prompt and final response mapping in src/strandsclaw/infrastructure/acp/mapping.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate ACP startup, capability advertisement, and one final completed text response.

### Incremental Delivery

1. Deliver User Story 1 for ACP-only MVP access.
2. Add User Story 2 to preserve bootstrap, file-scope, and shared-session semantics.
3. Add User Story 3 to harden the reusable adapter seam for future protocols.

### Scope Guardrails

- Keep the feature in the minimal core under `interfaces/`, `workspace/`, and `infrastructure/`.
- Do not add an OpenAI-compatible endpoint in this feature.
- Do not expand beyond launch-bound workspace selection, basic text chat turns, final completed responses, or the shared single workspace session model.
