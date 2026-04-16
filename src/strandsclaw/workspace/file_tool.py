from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from strandsclaw.workspace.file_scope import FileReadResult, read_workspace_text_file


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str


def register_workspace_file_read_tool() -> RegisteredTool:
    return RegisteredTool(
        name="workspace.read_file",
        description="Reads text files inside the active workspace boundary.",
    )


def collect_file_context(workspace_root: Path, user_prompt: str) -> tuple[str | None, FileReadResult | None]:
    candidate = _extract_candidate_path(user_prompt)
    if candidate is None:
        return None, None

    result = read_workspace_text_file(workspace_root, candidate)
    if result.status != "allowed":
        return None, result

    context = f"Requested file: {candidate}\n\n{result.contents or ''}"
    return context, result


def _extract_candidate_path(user_prompt: str) -> str | None:
    match = re.search(r"(?:read|summarize|open)\s+(`?)([^`\s]+)\1", user_prompt, re.IGNORECASE)
    if match is None:
        return None
    candidate = match.group(2).strip().rstrip(".,!?:;")
    if "/" in candidate or "." in candidate:
        return candidate
    return None
