# Feature Specification: Workspace Chat Agent

**Feature Branch**: `001-workspace-chat-agent`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Build the first minimal feature: a base personal assistant agent that lives in the workspace, bootstraps the workspace when absent or empty, can read files inside the workspace, uses local Ollama with qwen3.5:latest and a 64k context by default, supports a configurable future installation setup, persists a single session, and returns chat responses."

## Clarifications

### Session 2026-03-27

- Q: Which default workspace files should bootstrap create for the MVP? → A: Bootstrap `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, and `SOUL.md`.
- Q: How should workspace instruction files affect agent behavior while keeping prompt context small? → A: Always load `AGENTS.md`, `IDENTITY.md`, and `SOUL.md`; use `BOOTSTRAP.md` only during bootstrap; defer `TOOLS.md` for a later clarification.
- Q: What should happen if the persisted session is unreadable or corrupted? → A: Archive the unreadable session and start a fresh single session automatically.
- Q: What file-read size limit should the MVP enforce? → A: Limit reads to text files up to 64 KB per request and refuse larger or binary files with a clear message.

### Session 2026-04-16

- Q: How should runtime behave when local Ollama is unavailable? → A: Start chat loop anyway, but each turn returns a model-unavailable error until operator fixes runtime.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chat with the workspace assistant (Priority: P1)

An operator can start the base personal assistant for a workspace, send a message, and receive a natural-language response in an ongoing conversation.

**Why this priority**: Without a usable chat loop there is no assistant product. This is the smallest slice that proves the runtime works end to end.

**Independent Test**: Can be fully tested by starting the assistant against a prepared workspace, sending one or more prompts, and verifying that the assistant returns responses while keeping the conversation in the active session.

**Acceptance Scenarios**:

1. **Given** a workspace that already contains the required assistant assets, **When** the operator starts the assistant and sends a prompt, **Then** the assistant returns a response in the same run.
2. **Given** an existing persisted session for that workspace, **When** the operator starts the assistant again, **Then** the assistant resumes the existing conversation instead of creating a parallel session.

---

### User Story 2 - Bootstrap a missing or empty workspace (Priority: P2)

An operator can point the runtime at a workspace that is missing or empty and still reach a usable assistant because the runtime bootstraps the required workspace structure automatically before the first chat turn.

**Why this priority**: This removes manual setup as a prerequisite and makes the assistant usable from the first run, which is essential for the intended workspace-first experience.

**Independent Test**: Can be fully tested by starting the assistant against a non-existent or empty workspace and verifying that the workspace is initialized and the first prompt receives a response.

**Acceptance Scenarios**:

1. **Given** a workspace path that does not exist, **When** the operator starts the assistant, **Then** the runtime creates the workspace, materializes the default assistant assets, and opens the chat session.
2. **Given** an existing workspace directory with no assistant assets, **When** the operator starts the assistant, **Then** the runtime adds the missing default assets without blocking the first conversation.
3. **Given** a workspace that already contains customized assistant files, **When** bootstrap runs, **Then** existing user-authored files remain intact and only missing defaults are added.

---

### User Story 3 - Read workspace files safely during chat (Priority: P3)

An operator can ask the assistant about files in the active workspace, and the assistant can inspect those files while remaining confined to the workspace boundary.

**Why this priority**: File awareness is the first practical capability that makes the assistant useful for workspace-oriented tasks while still keeping the MVP small.

**Independent Test**: Can be fully tested by asking the assistant to summarize a file inside the workspace and separately attempting to access a path outside the workspace boundary.

**Acceptance Scenarios**:

1. **Given** a readable text file inside the active workspace, **When** the operator asks the assistant about that file, **Then** the assistant can read the file and use its contents in the response.
2. **Given** a path outside the active workspace, **When** the operator asks the assistant to read it, **Then** the request is refused with a clear boundary explanation.

### Edge Cases

- The local model runtime is unavailable, unreachable, or does not provide the configured default model.
- The workspace exists but contains unrelated user files and none of the required assistant assets.
- The persisted session file is missing, corrupted, or unreadable when the assistant starts.
- The operator asks the assistant to read a binary file, a file larger than 64 KB, or a file without read permission.
- A requested file path uses traversal or symlink resolution that would escape the active workspace boundary.

## Domain Framing *(mandatory for meaningful feature work)*

### Bounded Context

- **Bounded Context**: Workspace Assistant Runtime
- **Context Fit**: This extends the current minimal StrandsClaw core by introducing the first end-to-end assistant runtime behavior across workspace bootstrap, assistant startup, file-scoped tools, and session persistence.

### Ubiquitous Language

- **Workspace**: The operator-selected directory where assistant assets, state, and scoped tools are resolved.
- **Bootstrap**: The act of creating the minimum required assistant asset set inside a workspace before use.
- **Assistant Asset Set**: The default files and directories that make the workspace assistant operable, consisting of `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, and `SOUL.md` for this MVP.
- **Assistant Session**: The single persisted conversation context for one workspace in this MVP.
- **Chat Turn**: One operator request and the assistant response generated from the active session.
- **Tool Scope**: The enforced boundary that limits assistant file reads to the active workspace.
- **Model Profile**: The configured default provider, model identity, and context budget used for chat generation.

### Domain Invariants

- **INV-001**: The assistant MUST resolve exactly one active workspace before it processes a chat turn.
- **INV-002**: Bootstrap MUST make the workspace operable by adding missing assistant assets, but it MUST NOT overwrite existing user-authored workspace content.
- **INV-003**: File-read tools MUST remain confined to the active workspace boundary for every request.
- **INV-004**: At most one persisted assistant session may be active per workspace in this MVP.
- **INV-005**: If persisted session state cannot be recovered, the unreadable record must be archived before a replacement single session is created.

### External Boundaries

- **Upstream Systems**: Operator CLI input, local filesystem, workspace template assets, local Ollama runtime, and the operator's existing workspace contents.
- **Anti-Corruption Needs**: The runtime must translate filesystem paths into workspace-scoped access decisions, map OpenClaw-inspired template concepts into StrandsClaw workspace assets, and turn local model/runtime failures into actionable operator-facing messages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow the operator to start a base personal assistant for a chosen workspace from the runtime interface.
- **FR-002**: The system MUST resolve the active workspace path before starting chat behavior.
- **FR-003**: The system MUST detect when the active workspace is absent or lacks the minimum assistant asset set and MUST bootstrap it automatically before the first chat turn.
- **FR-004**: The system MUST bootstrap an assistant asset set that follows an OpenClaw-like structure for core workspace assistant files and includes `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, and `SOUL.md`.
- **FR-005**: The system MUST preserve existing user-authored workspace files during bootstrap and only create missing default assets.
- **FR-006**: The system MUST support an operator sending prompts to the assistant and receiving chat responses within the active session.
- **FR-007**: The system MUST use a local Ollama model profile with `qwen3.5:latest` and a 64k context window as the default chat configuration when no override has been configured.
- **FR-008**: The system MUST store the default model profile in configuration that can be replaced by a future installation or setup flow without requiring a redesign of the chat workflow.
- **FR-009**: The system MUST persist the single active assistant session in file-backed state for the workspace.
- **FR-010**: The system MUST restore the persisted session when the operator returns to the same workspace, unless the session cannot be recovered.
- **FR-011**: The system MUST provide a basic file-read capability to the assistant for text files inside the active workspace.
- **FR-012**: The system MUST refuse file-read attempts that would access content outside the active workspace and MUST explain the refusal to the operator.
- **FR-013**: The system MUST recover safely from missing or unreadable session state by archiving the unreadable record and creating a usable replacement single session without leaving multiple active session records.
- **FR-014**: The system MUST provide actionable error feedback when bootstrap, local model access, or scoped file reading cannot be completed.
- **FR-015**: The system MUST assemble the default chat prompt from `AGENTS.md`, `IDENTITY.md`, and `SOUL.md` on normal chat turns.
- **FR-016**: The system MUST use `BOOTSTRAP.md` only during workspace bootstrap behavior and MUST NOT include it in normal chat-turn prompt assembly.
- **FR-017**: Tool-definition files are out of scope for this MVP prompt contract and MUST remain deferred until a later feature clarification.
- **FR-018**: The system MUST limit each file-read request to readable text files of at most 64 KB and MUST refuse larger or binary files with a clear message.
- **FR-019**: The system MUST allow startup to succeed when local model runtime is unavailable, and each attempted chat turn MUST return an actionable model-unavailable error until the operator restores model availability.

### Key Entities *(include if feature involves data)*

- **Workspace Runtime**: The active workspace context, including resolved path, bootstrap status, assistant asset availability, and tool scope.
- **Assistant Asset Set**: The default workspace-resident files required to make the assistant operable in a newly prepared workspace, with `SOUL.md` carrying workspace-local personality guidance for the assistant and `AGENTS.md` remaining the primary behavioral contract.
- **Assistant Session**: The single persisted conversation record for one workspace, including session identity, transcript history, and last-updated state.
- **Archived Session Record**: A persisted session file that is no longer readable as an active session and is retained only for operator recovery or inspection.
- **Chat Turn**: A single operator prompt and resulting assistant response, optionally linked to workspace file reads used during the response.
- **Model Profile**: The configured default provider, model name, and context budget used when creating responses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From an empty or missing workspace, an operator can reach the first assistant response in one start action and under 60 seconds, excluding any external model download time.
- **SC-002**: In acceptance testing, 100% of supported startup flows either resume the existing session or bootstrap the workspace and open a usable chat session without manual file preparation.
- **SC-003**: In restart testing for a single workspace, the latest session history is recovered successfully in at least 95% of runs where the session file remains readable.
- **SC-004**: In boundary tests, 100% of file-read attempts outside the active workspace are denied, and 100% of valid readable text files of 64 KB or less inside the active workspace are available to the assistant.

## Assumptions

- This MVP targets a single local operator working with one active assistant session per workspace.
- The operator may start chat before local Ollama or the default `qwen3.5:latest` model is available and can restore model availability during runtime.
- Only basic text-oriented file reading is in scope for this feature; file writing, file editing, and multi-tool orchestration can be added later.
- The OpenClaw-inspired workspace structure will be adapted into StrandsClaw starter assets rather than copied as a strict one-to-one clone.
- A future installation or setup flow may change the default model profile, but that flow itself is out of scope for this feature.
