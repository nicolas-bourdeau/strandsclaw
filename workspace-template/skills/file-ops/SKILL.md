---
name: file-ops
description: Use this skill when reading or writing workspace state and memory files.
---

# File Operations

Use this skill when reading or writing workspace state, memory files, or template-derived documents.

- Persist structured state in `.state/` under the active workspace.
- Keep memory and profile files in workspace, not code repo internals.
- Avoid overwriting user-authored files unless explicitly requested.

See `references/API.md` for the local state store contract.
