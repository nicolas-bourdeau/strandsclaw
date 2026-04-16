from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 65536


@dataclass(frozen=True)
class FileReadResult:
    requested_path: str
    resolved_path: str | None
    status: str
    reason: str | None
    bytes_read: int | None
    contents: str | None


def read_workspace_text_file(workspace_root: Path, requested_path: str) -> FileReadResult:
    candidate = (workspace_root / requested_path).expanduser()
    try:
        resolved_workspace = workspace_root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
    except OSError:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=None,
            status="denied",
            reason="Denied: file could not be read.",
            bytes_read=None,
            contents=None,
        )

    if resolved_workspace not in resolved_candidate.parents and resolved_candidate != resolved_workspace:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_candidate),
            status="denied",
            reason="Denied: requested path is outside the active workspace boundary.",
            bytes_read=None,
            contents=None,
        )

    try:
        payload = resolved_candidate.read_bytes()
    except OSError:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_candidate),
            status="denied",
            reason="Denied: file could not be read.",
            bytes_read=None,
            contents=None,
        )

    if len(payload) > MAX_BYTES:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_candidate),
            status="denied",
            reason="Denied: file exceeds 64 KB limit.",
            bytes_read=None,
            contents=None,
        )

    if b"\x00" in payload:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_candidate),
            status="denied",
            reason="Denied: binary files are not supported in this MVP.",
            bytes_read=None,
            contents=None,
        )

    try:
        contents = payload.decode("utf-8")
    except UnicodeDecodeError:
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=str(resolved_candidate),
            status="denied",
            reason="Denied: binary files are not supported in this MVP.",
            bytes_read=None,
            contents=None,
        )

    return FileReadResult(
        requested_path=requested_path,
        resolved_path=str(resolved_candidate),
        status="allowed",
        reason=None,
        bytes_read=len(payload),
        contents=contents,
    )
