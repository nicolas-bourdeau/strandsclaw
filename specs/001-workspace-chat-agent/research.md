# Research: Workspace Chat Agent

## Decision 1: Default Local Model Profile Representation

- Decision: Represent model runtime settings as a structured profile in configuration (`provider=ollama`, `model=qwen3.5:latest`, `context_window=65536`) rather than a single model string.
- Rationale: FR-007 and FR-008 require a default model setup that works now and remains replaceable by a future install/setup flow; a typed profile avoids scattering model/context rules across CLI and runtime glue.
- Alternatives considered:
  - Keep only `default_model` string (rejected: cannot cleanly represent context-window defaults and future provider-level overrides).
  - Hardcode model profile inside CLI command handler (rejected: violates boundary guidance by embedding runtime rules in interface code).

## Decision 2: Workspace-Scoped File Read Policy

- Decision: Implement a dedicated workspace policy module that validates and reads files through this sequence: canonicalize path, enforce workspace containment, enforce `<= 64 KB`, reject binary content, then decode UTF-8 text for prompt use.
- Rationale: FR-011, FR-012, and FR-018 plus INV-003 require deterministic, testable boundary enforcement and clear refusals for traversal/symlink escape, oversize files, and binary files.
- Alternatives considered:
  - Perform ad hoc path checks in CLI runtime loop (rejected: brittle and hard to test; business policy leaks into interface layer).
  - Permit symlink targets unconditionally if requested path is under workspace root (rejected: allows boundary bypass via symlink escape).

## Decision 3: Single Session Persistence and Corruption Recovery

- Decision: Add a session-focused state adapter over the existing file-backed JSON store that enforces one active session key per workspace, archives unreadable session records, and creates a fresh replacement session automatically.
- Rationale: FR-009, FR-010, FR-013 and INV-004/INV-005 require both continuity and safety. Archiving before recreation preserves operator recoverability while restoring service without manual intervention.
- Alternatives considered:
  - Delete unreadable session directly and recreate (rejected: violates archive requirement and loses forensics).
  - Keep multiple active session files with latest-pointer resolution (rejected: exceeds MVP scope and conflicts with single-session invariant).

## Decision 4: Layering and Ownership

- Decision: Keep this feature inside the minimal core (`bootstrap`, `interfaces`, `workspace`, `infrastructure/state`, `config`) and do not introduce `domain/` or `application/` packages.
- Rationale: Invariants are narrow and operational (path boundaries, bootstrap non-overwrite behavior, single-session guarantees), and can be enforced with focused modules in existing areas without extra orchestration layers.
- Alternatives considered:
  - Introduce `domain/session.py` and `application/chat_service.py` now (rejected: premature abstraction for MVP complexity and current repository conventions).

## Decision 5: Prompt Contract Assembly

- Decision: On normal chat turns, prompt assembly always includes `AGENTS.md`, `IDENTITY.md`, and `SOUL.md`; `BOOTSTRAP.md` is read only during bootstrap workflows.
- Rationale: Directly satisfies FR-015 and FR-016 while keeping prompt context smaller and startup behavior deterministic.
- Alternatives considered:
  - Include `BOOTSTRAP.md` on every turn (rejected: contradicts clarified prompt contract and adds unnecessary prompt bloat).
  - Dynamically include all `*.md` files in workspace root (rejected: nondeterministic and can violate predictable runtime behavior).
