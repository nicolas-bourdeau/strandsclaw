# strandsclaw Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-23

## Active Technologies
- Python >= 3.11 + `strands-agents==1.33.0`, `agent-client-protocol`, `pyyaml>=6.0` (003-add-acp-adapter)
- Existing file-backed JSON state under workspace `.state/` via `FileStateStore` and `SessionStore` (003-add-acp-adapter)

- Python >= 3.11 + `strands-agents==1.33.0`, `pyyaml>=6.0` (001-workspace-chat-agent)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python >= 3.11: Follow standard conventions

## Recent Changes
- 003-add-acp-adapter: Added Python >= 3.11 + `strands-agents==1.33.0`, `agent-client-protocol`, `pyyaml>=6.0`

- 001-workspace-chat-agent: Added Python >= 3.11 + `strands-agents==1.33.0`, `pyyaml>=6.0`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
