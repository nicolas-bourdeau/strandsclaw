from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REQUIRED_ASSISTANT_FILES = ("AGENTS.md", "BOOTSTRAP.md", "IDENTITY.md", "SOUL.md")
NORMAL_TURN_FILES = ("AGENTS.md", "IDENTITY.md", "SOUL.md")


@dataclass(frozen=True)
class AssistantAssets:
    agents: str
    identity: str
    soul: str


def get_missing_assistant_files(workspace_root: Path) -> list[str]:
    missing: list[str] = []
    for filename in REQUIRED_ASSISTANT_FILES:
        if not (workspace_root / filename).exists():
            missing.append(filename)
    return missing


def load_normal_turn_assets(workspace_root: Path) -> AssistantAssets:
    return AssistantAssets(
        agents=_read_workspace_file(workspace_root / "AGENTS.md"),
        identity=_read_workspace_file(workspace_root / "IDENTITY.md"),
        soul=_read_workspace_file(workspace_root / "SOUL.md"),
    )


def load_bootstrap_instructions(workspace_root: Path) -> str:
    return _read_workspace_file(workspace_root / "BOOTSTRAP.md")


def _read_workspace_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
