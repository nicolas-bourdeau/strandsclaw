from pathlib import Path

from strandsclaw.bootstrap.init import bootstrap_workspace
from strandsclaw.config import AppConfig, ModelProfile
from strandsclaw.infrastructure.state.file_state_store import FileStateStore
from strandsclaw.workspace.skill_catalog import SkillCatalog


def make_config(tmp_path: Path) -> AppConfig:
    workspace_root = tmp_path / ".workspace"
    template_root = tmp_path / "workspace-template"
    _seed_template(template_root)

    return AppConfig(
        repo_root=tmp_path,
        workspace_root=workspace_root,
        workspace_template_dir=template_root,
        skills_dir=workspace_root / "skills",
        state_dir=workspace_root / ".state",
        model_profile=ModelProfile(provider="ollama", model="qwen3.5:latest", context_window=65536),
    )


def _seed_template(template_root: Path) -> None:
    (template_root / "skills" / "system").mkdir(parents=True, exist_ok=True)
    (template_root / "skills" / "file-ops").mkdir(parents=True, exist_ok=True)
    (template_root / "skills" / "system" / "SKILL.md").write_text(
        "---\nname: system\ndescription: System skill\n---\n\n# System\n",
        encoding="utf-8",
    )
    (template_root / "skills" / "file-ops" / "SKILL.md").write_text(
        "---\nname: file-ops\ndescription: File operations skill\n---\n\n# File Ops\n",
        encoding="utf-8",
    )


def test_bootstrap_workspace_creates_expected_directories(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    created = bootstrap_workspace(config)

    assert config.workspace_root.exists()
    assert config.state_dir.exists()
    assert (config.skills_dir / "system").exists()
    assert (config.skills_dir / "file-ops").exists()
    assert (config.skills_dir / "system" / "SKILL.md").exists()
    assert (config.skills_dir / "file-ops" / "SKILL.md").exists()
    assert created


def test_file_state_store_round_trip(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path / ".state")

    store.write("agent/session", {"status": "ok"})

    assert store.read("agent/session") == {"status": "ok"}
    assert store.keys() == ["agent__session"]


def test_skill_catalog_discovers_local_skills(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".workspace"
    skills_dir = workspace_root / "skills"
    skill_dir = skills_dir / "system"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# System Operations\n\nUse this skill when supervising runtime behavior.\n",
        encoding="utf-8",
    )

    catalog = SkillCatalog(skills_dir)

    skills = catalog.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "system"
    assert skills[0]["description"] == "Use this skill when supervising runtime behavior."
