from __future__ import annotations

import shutil
from pathlib import Path

from strandsclaw.config import AppConfig, load_config


class BootstrapError(RuntimeError):
    pass


def bootstrap_workspace(config: AppConfig | None = None) -> list[Path]:
    resolved = config or load_config()
    created: list[Path] = []

    for path in (resolved.workspace_root, resolved.state_dir, resolved.skills_dir):
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                operation = "workspace creation" if path == resolved.workspace_root else "directory creation"
                raise BootstrapError(f"{operation} failed for {path} during mkdir: {exc}") from exc
            created.append(path)

    created.extend(_materialize_workspace_template(resolved.workspace_template_dir, resolved.workspace_root))

    return created


def _materialize_workspace_template(template_root: Path, workspace_root: Path) -> list[Path]:
    created: list[Path] = []
    if not template_root.exists():
        return created

    for source_path in sorted(template_root.rglob("*")):
        relative = source_path.relative_to(template_root)
        target_path = workspace_root / relative

        if source_path.is_dir():
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                created.append(target_path)
            continue

        if target_path.exists():
            continue

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BootstrapError(f"directory creation failed for {target_path.parent} during mkdir: {exc}") from exc

        try:
            shutil.copy2(source_path, target_path)
        except OSError as exc:
            raise BootstrapError(f"template copy failed for {target_path} from {source_path}: {exc}") from exc
        created.append(target_path)

    return created
