from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelProfile:
    provider: str
    model: str
    context_window: int

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "context_window": self.context_window,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ModelProfile":
        provider = str(payload.get("provider", "ollama"))
        model = str(payload.get("model", "qwen3.5:latest"))
        context_window = int(payload.get("context_window", 65536))
        if context_window <= 0:
            raise ValueError("context_window must be > 0")
        if not model:
            raise ValueError("model must be non-empty")
        return cls(provider=provider, model=model, context_window=context_window)


@dataclass(frozen=True)
class AppConfig:
    repo_root: Path
    workspace_root: Path
    workspace_template_dir: Path
    skills_dir: Path
    state_dir: Path
    model_profile: ModelProfile

    @property
    def default_model(self) -> str:
        return f"{self.model_profile.provider}:{self.model_profile.model}"


def load_config(repo_root: Path | None = None, workspace_path: Path | str | None = None) -> AppConfig:
    resolved_root = repo_root or Path(__file__).resolve().parents[2]
    workspace_root = _resolve_workspace_root(resolved_root, workspace_path)
    workspace_template_dir = resolved_root / "workspace-template"
    skills_dir = workspace_root / "skills"
    state_dir = workspace_root / ".state"
    provider = os.environ.get("STRANDSCLAW_MODEL_PROVIDER", "ollama")
    model = os.environ.get("STRANDSCLAW_MODEL", "qwen3.5:latest")
    context_window = int(os.environ.get("STRANDSCLAW_MODEL_CONTEXT_WINDOW", "65536"))
    model_profile = ModelProfile(provider=provider, model=model, context_window=context_window)
    return AppConfig(
        repo_root=resolved_root,
        workspace_root=workspace_root,
        workspace_template_dir=workspace_template_dir,
        skills_dir=skills_dir,
        state_dir=state_dir,
        model_profile=model_profile,
    )


def _resolve_workspace_root(repo_root: Path, explicit_workspace: Path | str | None) -> Path:
    if explicit_workspace is not None:
        return Path(explicit_workspace).expanduser().resolve()

    from_env = os.environ.get("STRANDSCLAW_WORKSPACE")
    if from_env:
        return Path(from_env).expanduser().resolve()

    dev_workspace = repo_root / ".workspace"
    if dev_workspace.exists():
        return dev_workspace.resolve()

    return (Path.home() / "strandsclaw").resolve()
