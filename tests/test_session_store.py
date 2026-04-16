from __future__ import annotations

from pathlib import Path

from strandsclaw.infrastructure.state.file_state_store import FileStateStore
from strandsclaw.infrastructure.state.session_store import ACTIVE_SESSION_KEY, ARCHIVE_PREFIX, SessionStore


def test_load_or_create_initializes_single_session(tmp_path: Path) -> None:
    store = SessionStore(FileStateStore(tmp_path / ".state"))

    session = store.load_or_create()

    assert session.session_id == "default"
    assert session.messages == []

    persisted = FileStateStore(tmp_path / ".state").read(ACTIVE_SESSION_KEY)
    assert persisted is not None
    assert persisted["session_id"] == "default"


def test_append_and_save_round_trip(tmp_path: Path) -> None:
    state = FileStateStore(tmp_path / ".state")
    store = SessionStore(state)
    session = store.load_or_create()

    updated = store.append_turn(session, "hello", "world")
    store.save(updated)

    reloaded = store.load_or_create()
    assert len(reloaded.messages) == 2
    assert reloaded.messages[0].role == "user"
    assert reloaded.messages[0].content == "hello"
    assert reloaded.messages[1].role == "assistant"
    assert reloaded.messages[1].content == "world"


def test_unreadable_session_is_archived_then_replaced(tmp_path: Path) -> None:
    state = FileStateStore(tmp_path / ".state")
    state.write(ACTIVE_SESSION_KEY, {"invalid": "payload"})
    store = SessionStore(state)

    session = store.load_or_create()

    assert session.session_id == "default"
    keys = state.keys()
    assert ACTIVE_SESSION_KEY in keys
    archive_keys = [key for key in keys if key.startswith(ARCHIVE_PREFIX)]
    assert archive_keys

    archived_payload = state.read(archive_keys[0])
    assert archived_payload["archived_from"] == ACTIVE_SESSION_KEY
    assert archived_payload["raw_payload"] == {"invalid": "payload"}
