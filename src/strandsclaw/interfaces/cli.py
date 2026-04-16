from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from dataclasses import asdict

from strandsclaw.bootstrap.init import bootstrap_workspace
from strandsclaw.config import AppConfig, load_config
from strandsclaw.infrastructure.observability import RuntimeEventLogger
from strandsclaw.infrastructure.state.file_state_store import FileStateStore
from strandsclaw.infrastructure.state.session_store import SessionStore
from strandsclaw.workspace.assistant_assets import load_normal_turn_assets
from strandsclaw.workspace.file_tool import register_workspace_file_read_tool
from strandsclaw.workspace.prompt_assembly import assemble_normal_turn_prompt
from strandsclaw.workspace.skill_catalog import SkillCatalog


class ModelUnavailableError(RuntimeError):
    pass


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

    parser.error(f"unsupported command: {args.command}")
    return 2


def _run_chat(config: AppConfig, single_prompt: str | None) -> int:
    logger = RuntimeEventLogger()
    registered_tool = register_workspace_file_read_tool()
    logger.emit("tool.registered", tool=asdict(registered_tool))

    created = bootstrap_workspace(config)
    logger.emit("workspace.bootstrap", created=[str(path) for path in created])

    state_store = FileStateStore(config.state_dir)
    session_store = SessionStore(state_store)
    session = session_store.load_or_create()
    logger.emit("session.loaded", message_count=len(session.messages))

    if single_prompt is not None:
        _handle_turn(config, logger, session_store, session, single_prompt)
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

        session = _handle_turn(config, logger, session_store, session, user_prompt)

    return 0


def _handle_turn(
    config: AppConfig,
    logger: RuntimeEventLogger,
    session_store: SessionStore,
    session,
    user_prompt: str,
):
    assets = load_normal_turn_assets(config.workspace_root)
    prompt = assemble_normal_turn_prompt(assets, user_prompt)
    try:
        response = _generate_with_ollama(config, prompt)
        logger.emit("chat.turn_succeeded")
    except ModelUnavailableError as exc:
        response = f"Model unavailable: {exc}. Verify Ollama is running and the model is installed."
        logger.emit("chat.turn_model_unavailable", error=str(exc))

    print(f"assistant> {response}")
    updated = session_store.append_turn(session, user_prompt, response)
    session_store.save(updated)
    logger.emit("session.saved", message_count=len(updated.messages))
    return updated


def _generate_with_ollama(config: AppConfig, prompt: str) -> str:
    if config.model_profile.provider != "ollama":
        raise ModelUnavailableError(f"unsupported provider '{config.model_profile.provider}'")

    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(
            {
                "model": config.model_profile.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": config.model_profile.context_window},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - local ollama endpoint
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ModelUnavailableError(str(exc)) from exc

    message = str(payload.get("response", "")).strip()
    if not message:
        raise ModelUnavailableError("empty response from model runtime")
    return message
