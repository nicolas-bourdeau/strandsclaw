from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str


def register_workspace_file_read_tool() -> RegisteredTool:
    return RegisteredTool(
        name="workspace.read_file",
        description="Reads text files inside the active workspace boundary.",
    )
