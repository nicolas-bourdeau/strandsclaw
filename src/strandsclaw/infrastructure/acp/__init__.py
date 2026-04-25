"""ACP adapter package.

Exports the StrandsClaw ACP agent and its mapping helpers.
"""

from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
from strandsclaw.infrastructure.acp.mapping import extract_text_prompt, map_outcome_stop_reason

__all__ = [
    "StrandsClawACPAgent",
    "extract_text_prompt",
    "map_outcome_stop_reason",
]
