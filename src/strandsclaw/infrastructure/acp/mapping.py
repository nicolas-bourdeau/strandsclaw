"""ACP message/session translation helpers.

Translates between ACP SDK types and the adapter-neutral workspace runtime
types.  No workspace business logic lives here - this is pure shape mapping.
"""

from __future__ import annotations

from typing import Any

from acp.schema import TextContentBlock
from acp.schema import StopReason

from strandsclaw.workspace.chat_runtime import TurnOutcome, TurnStatus


def extract_text_prompt(blocks: list[Any]) -> str | None:
    """Return the concatenated text content from a list of ACP content blocks.

    Returns None if there are no text blocks.
    """
    texts: list[str] = []
    for block in blocks:
        if isinstance(block, TextContentBlock):
            texts.append(block.text)
    return "\n".join(texts) if texts else None


def map_outcome_stop_reason(outcome: TurnOutcome) -> StopReason:
    """Map a TurnOutcome status to the closest ACP StopReason."""
    _MAP: dict[TurnStatus, StopReason] = {
        "completed": "end_turn",
        "refused": "refusal",
        "model_unavailable": "end_turn",
        "unsupported": "end_turn",
        "bootstrap_failed": "end_turn",
        "session_recovery_failed": "end_turn",
        "cancelled": "cancelled",
    }
    return _MAP.get(outcome.status, "end_turn")  # type: ignore[return-value]


def has_non_text_blocks(blocks: list[Any]) -> bool:
    """Return True if the block list contains any non-text content blocks."""
    return any(not isinstance(block, TextContentBlock) for block in blocks)
