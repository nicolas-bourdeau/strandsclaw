# Feature Specification: OpenClaw Context Integration

**Feature Branch**: `002-feature-branch`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: User description: "I want to ensure the workspace files from the \"openclaw style\" template (identity, agents, soul) is taken into context when chatting with the agent. Get inspiration from openclaw."

## Clarifications

### Session 2026-04-22

- Q: What deterministic precedence order should be used for OpenClaw-style context files? -> A: Apply context in this order: `AGENTS.md`, `IDENTITY.md`, then `SOUL.md`.
- Q: What user-visible coverage states are required when context loading is partial? -> A: Report each required file as one of: `applied`, `missing`, `unreadable`, `invalid`, or `trimmed`.
- Q: How should prompt budget limits be defined for requirement clarity? -> A: Context budget is the maximum workspace-context portion allowed per turn and must not exceed the active chat model context window after reserving room for the user turn and response generation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ground responses in workspace identity (Priority: P1)

A workspace owner can chat with the agent and receive responses that consistently reflect the workspace's identity, behavior rules, and tone defined in the OpenClaw-style files.

**Why this priority**: This is the direct user value of the feature. If these files are not applied during chat, the workspace-specific assistant behavior does not exist.

**Independent Test**: Can be fully tested by preparing known content in the workspace identity files, sending prompts that should trigger those rules, and confirming responses reflect the configured guidance.

**Acceptance Scenarios**:

1. **Given** a workspace containing `AGENTS.md`, `IDENTITY.md`, and `SOUL.md`, **When** the user starts chat and sends a prompt, **Then** the response reflects guidance from those files.
2. **Given** a workspace where one of the files is updated between chat turns, **When** the next prompt is sent, **Then** the response reflects the updated file content.

---

### User Story 2 - Stay resilient when files are missing or invalid (Priority: P2)

A workspace owner can still use chat when one or more OpenClaw-style context files are missing, unreadable, or malformed, and receives clear feedback about what context was applied.

**Why this priority**: Reliability is essential for day-to-day usage. Context loading failures should not block core chat usage.

**Independent Test**: Can be fully tested by removing or corrupting one or more files and verifying chat still works with clear fallback behavior and user-visible warnings.

**Acceptance Scenarios**:

1. **Given** `AGENTS.md` is missing, **When** the user sends a prompt, **Then** chat still returns a response and indicates reduced context.
2. **Given** `IDENTITY.md` or `SOUL.md` cannot be read, **When** chat starts, **Then** the system reports the issue and continues with available context.

---

### User Story 3 - Keep context relevant and bounded (Priority: P3)

A workspace owner can rely on chat behavior that prioritizes the most relevant workspace context while keeping prompt assembly within an explicit budget.

**Why this priority**: The feature must be sustainable over many turns and varying file sizes without degrading chat usefulness.

**Independent Test**: Can be fully tested by using oversized or highly verbose context files and verifying the assembled context follows prioritization rules and remains bounded.

**Acceptance Scenarios**:

1. **Given** context files exceed the prompt budget, **When** chat assembles context, **Then** priority rules are applied and required sections are preserved.
2. **Given** context files are within limits, **When** chat assembles context, **Then** all required files are included without omission.

### Edge Cases

- Workspace contains empty `AGENTS.md`, `IDENTITY.md`, or `SOUL.md` files.
- File content includes conflicting guidance across the three files.
- Files contain unexpected formatting, very long lines, or non-text bytes.
- Files change during an active chat session.
- Workspace path is valid but context files are inaccessible due to permissions.

## Domain Framing *(mandatory for meaningful feature work)*

### Bounded Context

- **Bounded Context**: Workspace Prompt Context Assembly
- **Context Fit**: This extends the existing workspace chat runtime by making OpenClaw-style context files a first-class input for each chat turn.

### Ubiquitous Language

- **Workspace Context File**: A workspace-resident guidance document that influences chat behavior.
- **OpenClaw-Style Set**: The canonical trio of `AGENTS.md`, `IDENTITY.md`, and `SOUL.md`.
- **Context Assembly**: The process of loading, validating, ordering, and combining workspace context into the chat input.
- **Context Coverage**: A reportable view of which context files were successfully applied for a given chat turn.
- **Context Budget**: The maximum allowed amount of workspace context included in a chat turn.

### Domain Invariants

- **INV-001**: Every chat turn MUST attempt to assemble context from the OpenClaw-style set in the active workspace.
- **INV-002**: `AGENTS.md`, `IDENTITY.md`, and `SOUL.md` MUST be treated as distinct sources with stable ordering in context assembly.
- **INV-003**: Missing or unreadable context files MUST NOT block chat; they must degrade gracefully with explicit coverage reporting.
- **INV-004**: Context assembly MUST remain within a defined budget using deterministic prioritization.
- **INV-005**: Chat responses MUST be grounded only in the active workspace context and not in unrelated workspace roots.

### External Boundaries

- **Upstream Systems**: Active workspace filesystem, workspace template assets, and user-provided context file content.
- **Anti-Corruption Needs**: Normalize raw file content into a stable context model and isolate malformed file data from the core chat flow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST locate and load `AGENTS.md`, `IDENTITY.md`, and `SOUL.md` from the active workspace for chat context assembly.
- **FR-002**: The system MUST apply the deterministic precedence order `AGENTS.md` -> `IDENTITY.md` -> `SOUL.md` when assembling context so behavior is stable across runs.
- **FR-003**: The system MUST include applied context in every chat turn by default.
- **FR-004**: The system MUST detect context-file changes and apply updated content on subsequent chat turns without requiring workspace reinitialization.
- **FR-005**: The system MUST continue chat when one or more context files are unavailable and MUST provide a user-facing coverage report for each required file with one of these states: `applied`, `missing`, `unreadable`, `invalid`, or `trimmed`.
- **FR-006**: The system MUST guard chat context assembly with a defined context budget per turn and deterministic trimming rules.
- **FR-007**: The system MUST preserve the semantic distinction of identity, behavior, and soul guidance while assembling prompt context.
- **FR-008**: The system MUST expose runtime feedback per turn that identifies which required files were used and which were reduced or skipped due to availability or budget constraints.
- **FR-009**: The system MUST prevent context loading from escaping the active workspace boundary.
- **FR-010**: The system MUST document the OpenClaw-inspired context contract for workspace owners, including expected files and fallback behavior.
- **FR-011**: The system MUST ensure context budget allocation reserves capacity for the full user message and response generation in each turn.

### Key Entities *(include if feature involves data)*

- **Context Source**: A single workspace file in the OpenClaw-style set, including path, availability state, and parsed content.
- **Context Assembly Result**: The ordered, bounded context payload produced for a chat turn, including omitted or truncated sections.
- **Coverage Report**: A user-visible summary indicating which required context files were applied, skipped, missing, or invalid.
- **Assembly Policy**: The rule set that defines source order, priority, and budget behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance tests, at least 95% of prompts in workspaces with complete OpenClaw-style files produce responses that satisfy expected workspace-specific guidance checks.
- **SC-002**: In resilience tests where one or more context files are missing or unreadable, 100% of chat turns still produce a response and a coverage report.
- **SC-003**: In context-budget tests with oversized files, 100% of chat turns keep assembled context within the defined budget while preserving required priority segments.
- **SC-004**: In change-detection tests, updates to any of the three context files are reflected in the next chat turn in at least 95% of trials.

## Assumptions

- OpenClaw inspiration is applied as a behavioral contract pattern, not a strict copy of external project internals.
- The active workspace remains the only authority for context files during chat.
- Workspace owners are expected to maintain understandable markdown guidance in context files.
- Existing chat capabilities and runtime model behavior remain unchanged except for improved context grounding.
