from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileStateStore:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def read(self, key: str, default: Any = None) -> Any:
        path = self._path_for(key)
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, key: str, value: Any) -> None:
        path = self._path_for(key)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def keys(self) -> list[str]:
        return sorted(path.stem for path in self._base_dir.glob("*.json"))

    def _path_for(self, key: str) -> Path:
        safe_key = key.replace("/", "__")
        return self._base_dir / f"{safe_key}.json"
