# Feature Specification: ACP Adapter

**Feature Branch**: `003-add-acp-adapter`  
**Created**: 2026-04-23  
**Status**: Draft  
**Input**: User description: "start a new spec for the ACP adapter. the goal is to provide a standard integration point. offering an openai compatible endpoint would be nice too. maybe not now. but take into account we may support many types of integrations."

## Clarifications

### Session 2026-04-23

- Q: How should an ACP client select the active workspace? → A: The ACP process is launch-bound to one workspace, and all ACP sessions use that workspace.
- Q: What should the first ACP release support? → A: Support only basic chat turns in the first release.
- Q: How should multiple ACP sessions targeting the same workspace behave? → A: All ACP sessions for the same workspace map onto the same shared underlying workspace session.
- Q: Does the first ACP slice need streaming output? → A: No. A final completed response per turn is sufficient for the first release.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect a Standard ACP Client (Priority: P1)

An operator can point a standard ACP-capable client at StrandsClaw and start a usable conversation without needing a custom client-specific integration.

**Why this priority**: ACP provides the first standard integration point for external clients. Without it, StrandsClaw remains tied to its CLI interface and cannot interoperate with editor integrations such as Obsidian Agent Client.

**Independent Test**: Can be fully tested by launching StrandsClaw through an ACP-capable client, starting a session, sending a prompt, and receiving a compliant response without client-specific code in the caller.

**Acceptance Scenarios**:

1. **Given** a client that supports ACP, **When** the operator launches StrandsClaw for one workspace and connects the client, **Then** the client can discover StrandsClaw as an agent and start a usable chat session for that workspace.
2. **Given** an ACP session with the launch-bound active workspace, **When** the operator sends a prompt through the client, **Then** StrandsClaw returns one completed assistant response through the ACP session in a form the client can render as normal conversation output.

---

### User Story 2 - Preserve Workspace Assistant Behavior Through the Adapter (Priority: P2)

An operator using StrandsClaw through ACP gets the same workspace-scoped assistant behavior they would expect from the native runtime, including bootstrap, session continuity, and workspace-bound file awareness.

**Why this priority**: A protocol adapter only has value if it preserves the assistant's core behavior instead of creating a weaker parallel runtime.

**Independent Test**: Can be fully tested by connecting through ACP to a prepared workspace, performing multiple turns, restarting the client, and confirming that the active workspace semantics and persisted session behavior remain intact.

**Acceptance Scenarios**:

1. **Given** a workspace that is missing required assistant assets, **When** an ACP client starts the first session, **Then** StrandsClaw bootstraps the workspace before serving the first usable turn.
2. **Given** a workspace with an existing persisted assistant session, **When** the operator reconnects through ACP, **Then** StrandsClaw resumes the existing shared workspace session instead of creating an unrelated conversation state.
3. **Given** a prompt that causes the assistant to inspect workspace files, **When** the turn is served through ACP, **Then** workspace boundary rules and refusal behavior remain unchanged.

---

### User Story 3 - Extend the Integration Surface Safely (Priority: P3)

A maintainer can add future protocol adapters, such as an OpenAI-compatible endpoint, without redesigning the assistant core or duplicating business rules across protocol-specific entry points.

**Why this priority**: The ACP adapter should create a durable integration seam, not a one-off protocol binding that makes later integrations harder.

**Independent Test**: Can be fully tested by reviewing the adapter contract and confirming that protocol-specific responsibilities are isolated from assistant behavior, session rules, and workspace state rules.

**Acceptance Scenarios**:

1. **Given** ACP is the only implemented external protocol, **When** maintainers define a second protocol later, **Then** they can reuse the same core interaction contract rather than reimplementing assistant behavior from scratch.
2. **Given** future OpenAI-compatible support is deferred, **When** the ACP adapter is introduced, **Then** the specification still defines scope boundaries and extension expectations clearly enough to avoid locking StrandsClaw into ACP-only assumptions.

### Edge Cases

- An ACP client connects before the local model runtime is available.
- An ACP client disconnects during a turn or while a response is still being delivered.
- The ACP client requests capabilities or session actions that StrandsClaw does not support in the first release of the adapter.
- Multiple ACP sessions target the same workspace while the MVP still relies on a single shared persisted assistant session.
- The active workspace session record is unreadable when the ACP client starts a session.
- A future protocol adapter needs different session metadata or transport conventions than ACP while still relying on the same underlying assistant behavior.

## Domain Framing *(mandatory for meaningful feature work)*

### Bounded Context

- **Bounded Context**: Protocol Integration Surface
- **Context Fit**: This feature extends the current Workspace Assistant Runtime by introducing the first standard protocol adapter for external clients while preserving the existing minimal core behavior.

### Ubiquitous Language

- **Protocol Adapter**: A transport-facing component that exposes StrandsClaw through a named external integration standard while delegating assistant behavior to the core runtime.
- **Integration Surface**: The stable contract through which external clients initiate sessions, send prompts, receive responses, and observe runtime outcomes.
- **ACP Session**: A client-visible conversation session created through the Agent Client Protocol and mapped onto the single shared StrandsClaw workspace session for the launch-bound workspace.
- **Workspace Session**: The persisted StrandsClaw conversation state for one active workspace.
- **Capability Advertisement**: The set of behaviors the adapter declares as available to external clients.
- **Future Protocol Adapter**: A later transport binding, such as an OpenAI-compatible endpoint, that reuses the same assistant interaction contract without changing core business rules.

### Domain Invariants

- **INV-001**: A protocol adapter MUST resolve exactly one launch-bound active workspace before it processes a client turn.
- **INV-002**: Protocol-specific entry points MUST preserve the same workspace boundary rules, bootstrap behavior, and persisted session guarantees as the native runtime.
- **INV-003**: Protocol adapters MUST advertise only capabilities that StrandsClaw actually supports for that protocol release.
- **INV-004**: Assistant behavior, session rules, and workspace safety rules MUST remain outside protocol-specific transport glue.
- **INV-005**: The first ACP adapter MUST establish a reusable integration seam so later protocols can share the same core turn-handling contract.

### External Boundaries

- **Upstream Systems**: ACP-capable clients, future external protocol clients, local filesystem state, workspace template assets, and the configured model runtime.
- **Anti-Corruption Needs**: The adapter must translate external session and message conventions into StrandsClaw workspace turns, preserve assistant invariants across transport boundaries, and isolate future protocol differences from the assistant core.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose StrandsClaw through ACP as a standard client integration point.
- **FR-002**: The system MUST allow an ACP-capable client to discover, start, and use a StrandsClaw assistant session for the launch-bound workspace without requiring client-specific integration logic.
- **FR-003**: The system MUST resolve the active workspace from launch configuration before accepting an ACP turn.
- **FR-004**: The system MUST preserve workspace bootstrap behavior when ACP is the entry point for the first session in a workspace.
- **FR-005**: The system MUST preserve the current single persisted workspace session behavior when ACP clients reconnect to the same workspace, including when multiple ACP sessions map to that same workspace session.
- **FR-006**: The system MUST return one final completed assistant response per turn through ACP in a form compatible with normal conversational rendering by a compliant client.
- **FR-007**: The system MUST surface actionable protocol-compliant error outcomes when model access, workspace bootstrap, or session recovery cannot be completed.
- **FR-008**: The system MUST preserve workspace-scoped file access rules and refusal behavior for turns initiated through ACP.
- **FR-009**: The system MUST define a core interaction contract between the assistant runtime and protocol adapters so future integrations can reuse the same turn-handling behavior.
- **FR-010**: The system MUST keep protocol-specific transport concerns separate from assistant business rules, persistence rules, and workspace safety rules.
- **FR-011**: The system MUST document that the ACP adapter's first release supports basic chat turns only and treat unsupported capabilities as explicit non-goals rather than undefined behavior.
- **FR-012**: The system MUST treat streaming output, client-supplied attachments, and expanded client-side session management as out of scope for the first ACP release.
- **FR-013**: The system MUST allow future protocol adapters, including a potential OpenAI-compatible endpoint, to be added without requiring a redesign of workspace bootstrap, session persistence, or file-scope behavior.
- **FR-014**: The system MUST treat an OpenAI-compatible endpoint as out of scope for this feature release while preserving the ability to specify it later against the same integration seam.
- **FR-015**: The system MUST handle ACP session startup when the local model runtime is unavailable by returning actionable outcomes that allow the client operator to recover without corrupting workspace session state.

### Key Entities *(include if feature involves data)*

- **Protocol Session**: The client-visible integration session, including client identity, session lifecycle, and the mapping to the shared StrandsClaw workspace session.
- **Adapter Capability Set**: The explicit list of supported client-visible actions and behaviors for a protocol adapter release.
- **Integration Contract**: The internal contract that protocol adapters use to invoke workspace turn handling, session recovery, and assistant responses.
- **Workspace Runtime Context**: The resolved workspace path, bootstrap state, assistant asset availability, and file-scope boundary used during protocol-served turns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A standard ACP-capable client can connect to StrandsClaw and complete a first successful prompt-response exchange in one setup flow without custom client code.
- **SC-002**: In acceptance testing, 100% of ACP-started sessions preserve the same workspace bootstrap and workspace-boundary behavior as the native runtime for supported scenarios.
- **SC-003**: In restart testing for the same workspace, at least 95% of readable persisted sessions are resumed successfully through ACP without creating conflicting conversation state.
- **SC-004**: Maintainers can describe the supported ACP capability set and the deferred future-protocol scope without ambiguity, with zero undocumented client-visible behaviors in the first release.

## Assumptions

- The first protocol adapter targets locally launched ACP-capable clients rather than remote multi-tenant gateway scenarios.
- The active workspace is chosen when StrandsClaw is launched and is not selected per ACP session.
- ACP is the only protocol implemented in this feature slice; an OpenAI-compatible endpoint is explicitly deferred.
- The existing single persisted workspace session remains the governing session model for this feature.
- The first ACP release supports basic chat turns only and returns final completed responses rather than streaming partial output.
- Unsupported ACP capabilities may be omitted or rejected explicitly in the first release as long as the supported subset is documented clearly.
- Future integration types will reuse the same assistant runtime behaviors rather than introducing protocol-specific business rules.
