# Tasks: Workspace Chat Agent

**Input**: Design documents from `/specs/001-workspace-chat-agent/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are required for this feature because the spec includes mandatory user-scenario testing and the constitution requires targeted coverage for state transitions, invariants, and persistence behavior.

**Organization**: Tasks are grouped by user story so each story remains independently implementable and testable.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish shared configuration needed by all stories.

- [X] T001 Extend structured model profile defaults and config serialization in src/strandsclaw/config.py and src/strandsclaw/interfaces/cli.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers and seams that all user stories depend on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T002 [P] Add shared assistant asset loading and prompt assembly helpers in src/strandsclaw/workspace/assistant_assets.py and src/strandsclaw/workspace/prompt_assembly.py
- [X] T003 [P] Add shared single-session persistence adapter in src/strandsclaw/infrastructure/state/session_store.py
- [X] T004 [P] Add structured runtime event logging for bootstrap, chat, session, file-read, and model-unavailable flows in src/strandsclaw/infrastructure/observability.py and src/strandsclaw/interfaces/cli.py
- [X] T005 [P] Add explicit workspace file-read tool registration seam in src/strandsclaw/workspace/file_tool.py and connect it in src/strandsclaw/interfaces/cli.py
- [X] T006 Add shared chat runtime fixtures and invariant-oriented test helpers in tests/test_chat_runtime.py

**Checkpoint**: Foundation ready; user story slices can now proceed.

---

## Phase 3: User Story 1 - Chat with the workspace assistant (Priority: P1) 🎯 MVP

**Goal**: Start the assistant for a prepared workspace, exchange prompts, persist one session, and keep the chat loop running through model outages.

**Independent Test**: Start `strandsclaw chat` against a workspace that already contains the required assistant assets, send prompts across two runs, and verify the session resumes while model-unavailable turns return actionable errors instead of failing startup.

### Tests for User Story 1

- [X] T007 [P] [US1] Add chat runtime integration tests for startup, prompt/response flow, session resume, model-unavailable turn errors, and structured runtime events in tests/test_chat_runtime.py
- [X] T008 [P] [US1] Add session persistence and archive-recovery tests in tests/test_session_store.py

### Implementation for User Story 1

- [X] T009 [US1] Implement single-session load, append, save, and archive-on-recovery behavior in src/strandsclaw/infrastructure/state/session_store.py
- [X] T010 [US1] Implement normal-turn assistant asset loading and prompt assembly from `AGENTS.md`, `IDENTITY.md`, and `SOUL.md` in src/strandsclaw/workspace/assistant_assets.py and src/strandsclaw/workspace/prompt_assembly.py
- [X] T011 [US1] Wire the `chat` command, explicit tool registration, session resume/persist flow, and per-turn model-unavailable errors in src/strandsclaw/interfaces/cli.py and src/strandsclaw/workspace/file_tool.py
- [X] T012 [US1] Verify INV-001, INV-004, INV-005, observability requirements, and interface-layer ownership boundaries in tests/test_chat_runtime.py and tests/test_session_store.py

**Checkpoint**: User Story 1 is independently functional and demonstrable as the MVP.

---

## Phase 4: User Story 2 - Bootstrap a missing or empty workspace (Priority: P2)

**Goal**: Automatically prepare absent or incomplete workspaces without overwriting user-authored assistant assets.

**Independent Test**: Start `strandsclaw chat` against a missing workspace, an empty workspace, and a customized workspace, then verify missing defaults are created, existing files remain intact, and chat opens without extra setup.

### Tests for User Story 2

- [ ] T013 [P] [US2] Extend bootstrap acceptance coverage for missing, empty, and customized workspaces in tests/test_bootstrap.py
- [ ] T014 [P] [US2] Add operator-facing bootstrap failure messaging tests for workspace creation and template-copy errors in tests/test_chat_runtime.py and tests/test_bootstrap.py

### Implementation for User Story 2

- [ ] T015 [P] [US2] Add default assistant asset templates in workspace-template/AGENTS.md, workspace-template/BOOTSTRAP.md, workspace-template/IDENTITY.md, and workspace-template/SOUL.md
- [ ] T016 [US2] Update bootstrap asset materialization to add only missing assistant defaults in src/strandsclaw/bootstrap/init.py
- [ ] T017 [US2] Add actionable bootstrap failure messages for workspace creation and template-copy errors in src/strandsclaw/bootstrap/init.py and src/strandsclaw/interfaces/cli.py
- [ ] T018 [US2] Use `BOOTSTRAP.md` only during bootstrap-time startup handling in src/strandsclaw/workspace/assistant_assets.py and src/strandsclaw/interfaces/cli.py
- [ ] T019 [US2] Verify INV-002, FR-014 bootstrap failure feedback, and operator-visible bootstrap outcomes in tests/test_bootstrap.py and tests/test_chat_runtime.py

**Checkpoint**: User Stories 1 and 2 both work independently, including first-run startup from an absent workspace.

---

## Phase 5: User Story 3 - Read workspace files safely during chat (Priority: P3)

**Goal**: Let the assistant read text files inside the active workspace while refusing boundary escapes, binary files, and oversize files.

**Independent Test**: Ask the assistant to summarize a valid workspace text file and then attempt reads outside the workspace, through traversal/symlinks, and against binary or oversize files.

### Tests for User Story 3

- [ ] T020 [P] [US3] Add file-scope policy tests for allowed reads, traversal/symlink denial, size limits, binary detection, and unreadable files in tests/test_file_scope.py
- [ ] T021 [P] [US3] Add chat integration tests for workspace file summarization, explicit tool usage, and outside-boundary refusal in tests/test_chat_runtime.py

### Implementation for User Story 3

- [ ] T022 [US3] Implement workspace-scoped text file read policy with 64 KB and binary checks in src/strandsclaw/workspace/file_scope.py
- [ ] T023 [US3] Integrate file-read events and explicit file-read tool use into prompt construction and chat turn handling in src/strandsclaw/workspace/prompt_assembly.py, src/strandsclaw/workspace/file_tool.py, and src/strandsclaw/interfaces/cli.py
- [ ] T024 [US3] Verify INV-003 and operator-facing denial messages in tests/test_file_scope.py and tests/test_chat_runtime.py

**Checkpoint**: All user stories are independently functional, including safe workspace file access.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish operator-facing docs and run full feature validation.

- [ ] T025 [P] Update operator documentation for `chat`, model profile defaults, outage behavior, explicit file-read tooling, and bootstrap failure feedback in README.md and specs/001-workspace-chat-agent/quickstart.md
- [ ] T026 Validate SC-001 startup timing and run full regression coverage for the feature in specs/001-workspace-chat-agent/quickstart.md, tests/test_bootstrap.py, tests/test_chat_runtime.py, tests/test_session_store.py, and tests/test_file_scope.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all story work.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and is the MVP slice.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and User Story 1 because its acceptance flow starts through the `chat` runtime.
- **User Story 3 (Phase 5)**: Depends on Phase 2 and User Story 1 because its acceptance flow uses the `chat` runtime and explicit file-read tool wiring.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1**: No story dependency after Phase 2.
- **US2**: Depends on US1 because bootstrap success is exercised through the `chat` command entrypoint.
- **US3**: Depends on US1 because safe file reads are exercised through the running chat loop and registered file-read tool.

### Within Each User Story

- Story tests should be written first and fail before implementation.
- Persistence and policy logic should land before CLI wiring.
- Observability and explicit tool registration should land before story-specific chat flows depend on them.
- CLI wiring should complete before invariant sign-off.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T004 and T005 can run in parallel after T001.
- T007 and T008 can run in parallel inside US1.
- T013 and T015 can run in parallel inside US2 after US1 is complete.
- T020 and T021 can run in parallel inside US3 after US1 is complete.
- T025 can run in parallel with final regression validation once implementation is stable.

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 test tasks together:
Task: "T007 [US1] Add chat runtime integration tests in tests/test_chat_runtime.py"
Task: "T008 [US1] Add session persistence and archive-recovery tests in tests/test_session_store.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch the User Story 3 test tasks together:
Task: "T020 [US3] Add file-scope policy tests in tests/test_file_scope.py"
Task: "T021 [US3] Add chat integration tests for workspace file reads in tests/test_chat_runtime.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate User Story 1 independently before expanding bootstrap and file-read behavior.

### Incremental Delivery

1. Deliver US1 for a prepared workspace chat loop with persisted single-session behavior.
2. Add US2 so missing or incomplete workspaces bootstrap automatically with actionable bootstrap failure feedback.
3. Add US3 so the assistant can inspect workspace files safely through the registered workspace file-read tool.
4. Finish with documentation, SC-001 timing validation, and full regression coverage.

### Parallel Team Strategy

1. One developer can finish T001-T006.
2. After US1 is complete, separate developers can take US2 and US3 test tasks in parallel.
3. Story owners can then land implementation and invariant sign-off in priority order.

---

## Notes

- All tasks use exact repository paths under `src/strandsclaw/`, `tests/`, `workspace-template/`, and `specs/001-workspace-chat-agent/`.
- No `domain/`, `application/`, repository, or agent-assembly tasks are included because the plan keeps the feature inside the current minimal core.
- Invariant sign-off tasks explicitly guard against leaking business rules into CLI or persistence adapters.
- Structured logging and explicit file-read tool registration are treated as foundational work to satisfy Observable Agent Operations before story delivery.
