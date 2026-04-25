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
        help=(
            "Workspace root path for this ACP process. "
            "If omitted, the path is resolved from STRANDSCLAW_WORKSPACE_PATH or the default (~/.strandsclaw-workspace)."
        ),
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

    ctx = None
    try:
        ctx = prepare_workspace(config)
    except BootstrapError as exc:
        print(f"ACP workspace not ready ({exc}); starting in bootstrap-required mode.", file=sys.stderr)

    if ctx is not None:
        print(f"Starting StrandsClaw ACP agent in workspace: {config.workspace_root}", file=sys.stderr)
    agent = StrandsClawACPAgent(ctx, config=config, log_sink=lambda s: print(s, file=sys.stderr))

    try:
        asyncio.run(_run_acp(agent))
    except KeyboardInterrupt:
        pass
    return 0


async def _run_acp(agent: object) -> None:
    from acp import run_agent
    await run_agent(agent)
