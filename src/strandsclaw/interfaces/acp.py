"""ACP adapter launch entrypoint.

Provides the `strandsclaw acp --workspace-path <path>` command that starts
StrandsClaw as an ACP agent over stdio.

Usage:
    strandsclaw acp --workspace-path /path/to/workspace
    uv run strandsclaw acp --workspace-path ~/.strandsclaw-workspace
"""

from __future__ import annotations

import argparse
import asyncio
import sys


def build_acp_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strandsclaw acp")
    parser.add_argument(
        "--workspace-path",
        type=str,
        required=False,
        help="Workspace root path for this ACP process",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ACP adapter process."""
    parser = build_acp_parser()
    args = parser.parse_args(argv)

    from strandsclaw.bootstrap.init import BootstrapError
    from strandsclaw.config import load_config
    from strandsclaw.infrastructure.acp.agent import StrandsClawACPAgent
    from strandsclaw.workspace.chat_runtime import prepare_workspace

    config = load_config(workspace_path=args.workspace_path)

    try:
        ctx = prepare_workspace(config)
    except BootstrapError as exc:
        print(f"ACP bootstrap failed: {exc}", file=sys.stderr)
        return 1

    agent = StrandsClawACPAgent(ctx)

    try:
        asyncio.run(_run_acp(agent))
    except KeyboardInterrupt:
        pass
    return 0


async def _run_acp(agent: object) -> None:
    from acp import run_agent
    await run_agent(agent)
