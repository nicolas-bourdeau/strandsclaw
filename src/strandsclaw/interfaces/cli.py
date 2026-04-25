"""CLI delivery surface for StrandsClaw.

This module owns only operator-facing argument parsing and command routing.
All workspace runtime behavior (bootstrap, session, turns) is delegated to
workspace/chat_runtime.py.
"""
from __future__ import annotations

import argparse
import json

from strandsclaw.bootstrap.init import BootstrapError, bootstrap_workspace
from strandsclaw.config import AppConfig, load_config
from strandsclaw.infrastructure.observability import RuntimeEventLogger
from strandsclaw.infrastructure.state.file_state_store import FileStateStore
from strandsclaw.infrastructure.state.session_store import SessionStore
from strandsclaw.workspace.assistant_assets import (
    get_missing_assistant_files,
    load_bootstrap_instructions,
    load_normal_turn_assets,
)
from strandsclaw.workspace.chat_runtime import (
    ModelUnavailableError,
    WorkspaceRuntimeContext,
    execute_turn,
    prepare_workspace,
)
from strandsclaw.workspace.file_tool import collect_file_context, register_workspace_file_read_tool
from strandsclaw.workspace.prompt_assembly import assemble_normal_turn_prompt
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
    chat = subparsers.add_parser("chat", help="Start the workspace assistant chat runtime")
    chat.add_argument("--prompt", type=str, help="Run a single prompt and exit")
    acp_sub = subparsers.add_parser("acp", help="Start the workspace assistant ACP adapter over stdio")
    acp_sub.add_argument(
        "--workspace-path",
        dest="acp_workspace_path",
        type=str,
        help="Workspace path for the ACP process (overrides global --workspace-path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(workspace_path=args.workspace_path)

    if args.command == "bootstrap":
        try:
            created = bootstrap_workspace(config)
        except BootstrapError as exc:
            print(f"Bootstrap failed: {exc}")
            return 1
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
                    "model_profile": config.model_profile.to_dict(),
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

    if args.command == "chat":
        return _run_chat(config, single_prompt=args.prompt)

    if args.command == "acp":
        from strandsclaw.interfaces.acp import main as acp_main
        workspace_path = getattr(args, "acp_workspace_path", None) or args.workspace_path
        return acp_main(["--workspace-path", workspace_path] if workspace_path else [])

    parser.error(f"unsupported command: {args.command}")
    return 2


def _run_chat(config: AppConfig, single_prompt: str | None) -> int:
    # Capture bootstrap_required before prepare_workspace runs bootstrap.
    bootstrap_required = (not config.workspace_root.exists()) or bool(
        get_missing_assistant_files(config.workspace_root)
    )

    try:
        ctx = prepare_workspace(config)
    except BootstrapError as exc:
        print(f"Bootstrap failed: {exc}")
        return 1

    if bootstrap_required:
        print(f"workspace> bootstrapped {config.workspace_root}")

    if single_prompt is not None:
        outcome = execute_turn(ctx, single_prompt)
        print(f"assistant> {outcome.assistant_text}")
        return 0

    while True:
        try:
            user_prompt = input("you> ").strip()
        except EOFError:
            break

        if not user_prompt:
            continue
        if user_prompt.lower() in {"quit", "exit"}:
            break

        outcome = execute_turn(ctx, user_prompt)
        print(f"assistant> {outcome.assistant_text}")

    return 0
