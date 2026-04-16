from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from strandsclaw.infrastructure.state.file_state_store import FileStateStore

ACTIVE_SESSION_KEY = "assistant_session"
ARCHIVE_PREFIX = "assistant_session__archived__"


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    timestamp: str


@dataclass(frozen=True)
class AssistantSession:
    session_id: str
    messages: list[ChatMessage]
    created_at: str
    updated_at: str


class SessionStore:
    def __init__(self, state_store: FileStateStore) -> None:
        self._state_store = state_store

    def load_or_create(self) -> AssistantSession:
        raw = self._state_store.read(ACTIVE_SESSION_KEY)
        if raw is None:
            session = _new_session()
            self.save(session)
            return session

        try:
            return _parse_session(raw)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._archive_unreadable(raw, reason=str(exc))
            session = _new_session()
            self.save(session)
            return session

    def append_turn(self, session: AssistantSession, user_prompt: str, assistant_response: str) -> AssistantSession:
        now = _iso_now()
        updated_messages = [
            *session.messages,
            ChatMessage(role="user", content=user_prompt, timestamp=now),
            ChatMessage(role="assistant", content=assistant_response, timestamp=now),
        ]
        return AssistantSession(
            session_id=session.session_id,
            messages=updated_messages,
            created_at=session.created_at,
            updated_at=now,
        )

    def save(self, session: AssistantSession) -> None:
        self._state_store.write(
            ACTIVE_SESSION_KEY,
            {
                "session_id": session.session_id,
                "messages": [
                    {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                    for msg in session.messages
                ],
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            },
        )

    def _archive_unreadable(self, raw_payload: Any, reason: str) -> None:
        archive_key = f"{ARCHIVE_PREFIX}{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}"
        self._state_store.write(
            archive_key,
            {
                "archived_from": ACTIVE_SESSION_KEY,
                "archived_at": _iso_now(),
                "reason": reason,
                "raw_payload": raw_payload,
            },
        )


def _parse_session(payload: dict[str, Any]) -> AssistantSession:
    session_id = str(payload["session_id"])
    created_at = str(payload["created_at"])
    updated_at = str(payload["updated_at"])
    messages_payload = payload["messages"]
    if not isinstance(messages_payload, list):
        raise ValueError("messages must be a list")

    messages: list[ChatMessage] = []
    for item in messages_payload:
        messages.append(
            ChatMessage(
                role=str(item["role"]),
                content=str(item["content"]),
                timestamp=str(item["timestamp"]),
            )
        )

    return AssistantSession(
        session_id=session_id,
        messages=messages,
        created_at=created_at,
        updated_at=updated_at,
    )


def _new_session() -> AssistantSession:
    now = _iso_now()
    return AssistantSession(session_id="default", messages=[], created_at=now, updated_at=now)


def _iso_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
