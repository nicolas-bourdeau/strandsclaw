from __future__ import annotations

import os
from pathlib import Path

import pytest

from strandsclaw.workspace.file_scope import read_workspace_text_file


def test_read_workspace_text_file_allows_valid_text_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    target = workspace_root / "notes.txt"
    target.write_text("hello world", encoding="utf-8")

    result = read_workspace_text_file(workspace_root, "notes.txt")

    assert result.status == "allowed"
    assert result.contents == "hello world"
    assert result.bytes_read == len("hello world".encode("utf-8"))


def test_read_workspace_text_file_denies_traversal(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    result = read_workspace_text_file(workspace_root, "../secret.txt")

    assert result.status == "denied"
    assert result.reason == "Denied: requested path is outside the active workspace boundary."


def test_read_workspace_text_file_denies_symlink_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("nope", encoding="utf-8")
    symlink = workspace_root / "link.txt"
    symlink.symlink_to(outside)

    result = read_workspace_text_file(workspace_root, "link.txt")

    assert result.status == "denied"
    assert result.reason == "Denied: requested path is outside the active workspace boundary."


def test_read_workspace_text_file_denies_oversize_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    target = workspace_root / "big.txt"
    target.write_text("a" * 65537, encoding="utf-8")

    result = read_workspace_text_file(workspace_root, "big.txt")

    assert result.status == "denied"
    assert result.reason == "Denied: file exceeds 64 KB limit."


def test_read_workspace_text_file_denies_binary_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    target = workspace_root / "blob.bin"
    target.write_bytes(b"\x00\x01\x02")

    result = read_workspace_text_file(workspace_root, "blob.bin")

    assert result.status == "denied"
    assert result.reason == "Denied: binary files are not supported in this MVP."


def test_read_workspace_text_file_denies_unreadable_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    target = workspace_root / "notes.txt"
    target.write_text("hello", encoding="utf-8")

    def _raise(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_bytes", _raise)

    result = read_workspace_text_file(workspace_root, "notes.txt")

    assert result.status == "denied"
    assert result.reason == "Denied: file could not be read."
