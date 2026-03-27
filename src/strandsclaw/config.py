from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    repo_root: Path
    workspace_root: Path
    workspace_template_dir: Path
    skills_dir: Path
    state_dir: Path
    default_model: str


def load_config(repo_root: Path | None = None, workspace_path: Path | None = None) -> AppConfig:
    resolved_root = repo_root or Path(__file__).resolve().parents[2]
    workspace_root = _resolve_workspace_root(resolved_root, workspace_path)
    workspace_template_dir = resolved_root / "workspace-template"
    skills_dir = workspace_root / "skills"
    state_dir = workspace_root / ".state"
    default_model = os.environ.get("STRANDSCLAW_MODEL", "openai:gpt-4.1")
    return AppConfig(
        repo_root=resolved_root,
        workspace_root=workspace_root,
        workspace_template_dir=workspace_template_dir,
        skills_dir=skills_dir,
        state_dir=state_dir,
        default_model=default_model,
    )


def _resolve_workspace_root(repo_root: Path, explicit_workspace: Path | None) -> Path:
    if explicit_workspace is not None:
        return explicit_workspace.expanduser().resolve()

    from_env = os.environ.get("STRANDSCLAW_WORKSPACE")
    if from_env:
        return Path(from_env).expanduser().resolve()

    dev_workspace = repo_root / ".workspace"
    if dev_workspace.exists():
        return dev_workspace.resolve()

    return (Path.home() / "strandsclaw").resolve()
