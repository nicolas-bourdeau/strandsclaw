# Research: ACP Adapter

## Decision 1: Use the official ACP Python SDK over stdio

- Decision: Implement the first protocol adapter with the official `agent-client-protocol` Python SDK and run it over stdio.
- Rationale: The repository must stay pure Python, ACP clients commonly launch local agents over stdio, and the official SDK already provides the agent lifecycle, session methods, and capability advertisement needed for an MVP adapter.
- Alternatives considered:
  - Hand-roll ACP JSON-RPC transport support (rejected: unnecessary protocol risk and maintenance cost for the first standard integration seam).
  - Start with an HTTP transport (rejected: unnecessary scope for the first local ACP slice and not required to satisfy the feature stories).

## Decision 2: Advertise only the ACP MVP capability set

- Decision: Support the core ACP session surface required for a basic chat agent and advertise only what the runtime can actually honor in this release. Do not advertise optional capabilities such as `session/list`, `loadSession`, streaming output, attachments, or alternate transports.
- Rationale: INV-003 and FR-011/FR-012 require explicit capability boundaries. The safest MVP is to expose a narrow, accurate surface instead of claiming partial support for features the current runtime cannot preserve.
- Alternatives considered:
  - Advertise optional capabilities and stub them out (rejected: violates the capability invariant and creates ambiguous client behavior).
  - Add `loadSession` immediately (rejected: ACP client-visible session restoration is not needed to preserve the existing shared workspace session behavior and would blur the distinction between protocol sessions and workspace persistence).

## Decision 3: Separate protocol sessions from the shared workspace session

- Decision: Treat each ACP `session/new` result as a client-visible protocol session that binds to the existing shared StrandsClaw workspace session instead of creating a new persisted conversation record.
- Rationale: The current runtime already enforces one persisted workspace session. Preserving that behavior through ACP is simpler and more consistent than inventing a second persistence model for protocol sessions.
- Alternatives considered:
  - Create one persisted workspace session per ACP session ID (rejected: conflicts with the clarified single-session invariant and adds new persistence semantics the spec does not require).
  - Persist ACP session IDs for client-directed `session/load` support now (rejected: broader scope than the MVP and not necessary to let reconnecting clients reuse the same underlying workspace state).

## Decision 4: Extract an adapter-neutral workspace turn contract from the CLI path

- Decision: Move workspace preparation and turn execution into a shared runtime contract in `workspace/`, with ACP and the CLI both delegating to it.
- Rationale: FR-009, FR-010, and INV-004 require protocol adapters to reuse the same core behavior instead of copying bootstrap, prompt, session, and file-scope logic into each transport entrypoint.
- Alternatives considered:
  - Call existing CLI helpers directly from ACP glue (rejected: leaks CLI-specific assumptions into protocol code and makes future transports harder to add).
  - Introduce `application/` services immediately (rejected: the needed seam is small and operational; a focused workspace runtime module is sufficient).

## Decision 5: Keep the feature in the minimal core

- Decision: Extend `interfaces/`, `workspace/`, and `infrastructure/` only; do not introduce `domain/` or `application/` packages for this feature.
- Rationale: The new complexity is protocol translation and runtime reuse, not a new domain model. The feature's invariants are explicit, narrow, and enforceable without broad DDD scaffolding.
- Alternatives considered:
  - Introduce `domain/protocol_session.py` and `application/chat_service.py` now (rejected: premature layering without corresponding domain richness).
  - Put all ACP logic directly in `interfaces/cli.py` (rejected: violates boundary guidance and would entangle delivery glue with runtime rules).

## Decision 6: Defer OpenAI-compatible transport while designing for it

- Decision: Keep any OpenAI-compatible endpoint out of scope for this feature, but ensure the internal adapter-runtime contract uses StrandsClaw-owned request and outcome shapes rather than ACP-specific payload types.
- Rationale: FR-013 and FR-014 require future extensibility without dragging future transport work into the ACP MVP. A transport-neutral contract preserves that seam cleanly.
- Alternatives considered:
  - Design the runtime contract directly around ACP request/response models (rejected: would lock the core seam to ACP assumptions and complicate future adapters).
  - Add an OpenAI-compatible stub now (rejected: increases scope without validating the standard ACP seam first).

## Decision 7: Return model-unavailable turns as actionable final turn outcomes

- Decision: When model access is unavailable during an ACP prompt, return a completed turn with actionable recovery text and preserve the shared workspace session instead of corrupting or replacing session state.
- Rationale: FR-007 and FR-015 emphasize recoverable operator outcomes. The current CLI runtime already treats model outages as turn-scoped failures, and ACP should preserve that behavior.
- Alternatives considered:
  - Fail ACP session startup whenever the model runtime is unavailable (rejected: prevents workspace bootstrap and session reuse paths from remaining usable).
  - Raise opaque transport errors without user-facing guidance (rejected: not actionable and weakens client experience).
