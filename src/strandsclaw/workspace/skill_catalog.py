from __future__ import annotations

from pathlib import Path

import yaml


class SkillCatalog:
    def __init__(self, skills_dir: Path) -> None:
        self._skills_dir = skills_dir

    def list_skills(self) -> list[dict[str, str]]:
        if not self._skills_dir.exists():
            return []

        skills: list[dict[str, str]] = []
        for skill_file in sorted(self._skills_dir.glob("*/SKILL.md")):
            metadata = self._extract_metadata(skill_file)
            skills.append(
                {
                    "name": metadata.get("name", skill_file.parent.name),
                    "description": metadata.get("description", self._extract_description(skill_file)),
                    "path": str(skill_file.parent),
                }
            )
        return skills

    @staticmethod
    def _extract_metadata(skill_file: Path) -> dict[str, str]:
        content = skill_file.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            return {}

        _, _, remainder = content.partition("---\n")
        frontmatter, separator, _ = remainder.partition("\n---\n")
        if not separator:
            return {}

        parsed = yaml.safe_load(frontmatter) or {}
        return {
            key: str(value)
            for key, value in parsed.items()
            if key in {"name", "description"} and value is not None
        }

    @staticmethod
    def _extract_description(skill_file: Path) -> str:
        heading = skill_file.parent.name
        for line in skill_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                heading = stripped[2:].strip()
                continue
            if stripped and not stripped.startswith("#"):
                return stripped
        return heading
