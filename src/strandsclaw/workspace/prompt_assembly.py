from __future__ import annotations

from strandsclaw.workspace.assistant_assets import AssistantAssets


def assemble_normal_turn_prompt(assets: AssistantAssets, user_prompt: str, file_context: str | None = None) -> str:
    sections = [
        "# AGENTS", assets.agents.strip(),
        "# IDENTITY", assets.identity.strip(),
        "# SOUL", assets.soul.strip(),
        "# WORKSPACE FILE", (file_context or "").strip(),
        "# USER", user_prompt.strip(),
    ]
    return "\n\n".join(section for section in sections if section)
