"""CLI entry point for the AI Dev Team system.

Usage
-----
    # Start the API server
    python -m ai_dev_team.main serve

    # Run a project from the command line
    python -m ai_dev_team.main run "Build a REST API for a todo application"
"""

from __future__ import annotations

import argparse
import asyncio
import logging

import uvicorn

from ai_dev_team.api.server import build_system
from ai_dev_team.config.settings import load_config


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------

def cmd_serve(args: argparse.Namespace) -> None:
    """Start the FastAPI server."""
    _setup_logging(args.log_level)
    uvicorn.run(
        "ai_dev_team.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_run(args: argparse.Namespace) -> None:
    """Execute a project from a prompt without the server."""
    _setup_logging(args.log_level)
    logger = logging.getLogger("main")

    config = load_config()
    leader = build_system(config)

    prompt = args.prompt
    logger.info("Running prompt: %s", prompt)

    result = asyncio.run(leader.handle_request(prompt))

    print("\n" + "=" * 60)
    print("PROJECT COMPLETE")
    print("=" * 60)
    print(f"\nPlan:\n{result.get('plan', '')}")
    print(f"\nTask Summary: {result.get('task_summary', {})}")

    tasks = result.get("tasks", {})
    for tid, info in tasks.items():
        status = info.get("status", "unknown")
        title = info.get("title", tid)
        print(f"  [{status}] {title}")

    print()


# ------------------------------------------------------------------
# Argument parser
# ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_dev_team",
        description="Autonomous multi-agent AI coding system",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.set_defaults(func=cmd_serve)

    # run
    run_parser = subparsers.add_parser("run", help="Run a project from a prompt")
    run_parser.add_argument("prompt", help="Natural-language project description")
    run_parser.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
