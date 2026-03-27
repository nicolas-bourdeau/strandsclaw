from __future__ import annotations

import argparse
import json

from strandsclaw.bootstrap.init import bootstrap_workspace
from strandsclaw.config import load_config
from strandsclaw.workspace.skill_catalog import SkillCatalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strandsclaw")
    parser.add_argument(
        "--workspace-path",
        type=str,
        help="Override workspace root path for this command",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap", help="Initialize runtime directories for the local workspace")
    subparsers.add_parser("show-config", help="Print the resolved runtime configuration")
    subparsers.add_parser("list-skills", help="List discovered local skills")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(workspace_path=args.workspace_path)

    if args.command == "bootstrap":
        created = bootstrap_workspace(config)
        print(json.dumps({"created": [str(path) for path in created]}, indent=2))
        return 0

    if args.command == "show-config":
        print(
            json.dumps(
                {
                    "repo_root": str(config.repo_root),
                    "workspace_root": str(config.workspace_root),
                    "skills_dir": str(config.skills_dir),
                    "state_dir": str(config.state_dir),
                    "default_model": config.default_model,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "list-skills":
        catalog = SkillCatalog(config.skills_dir)
        print(json.dumps(catalog.list_skills(), indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2
