# core/cli.py — Modern Canonical Interactive CLI REPL for BR JARVIS
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

from .runtime import ApplicationRuntime
from .terminal import (
    VALID_MODES,
    TerminalRenderer,
    TerminalSession,
)
from .terminal import (
    run_cli as terminal_run_cli,
)
from .terminal import (
    run_query as terminal_run_query,
)
from .version import CODENAME, VERSION

logger = logging.getLogger("JARVIS.CLI")


def print_banner() -> None:
    """Print the canonical terminal header banner (backward compatibility)."""
    renderer = TerminalRenderer()
    renderer.render_header()


def handle_slash_command(cmd: str, runtime: ApplicationRuntime) -> bool:
    """Process interactive slash commands (backward compatibility bridge)."""
    session = TerminalSession(runtime=runtime, auto_welcome=False)
    return session.commands.execute(cmd)


def run_cli(
    runtime: Optional[ApplicationRuntime] = None,
    mode: str = "general",
    session_id: Optional[str] = None,
) -> None:
    """Run the interactive CLI loop."""
    terminal_run_cli(runtime=runtime, mode=mode, session_id=session_id)


def run_query(
    query: str,
    runtime: Optional[ApplicationRuntime] = None,
    mode: str = "general",
) -> int:
    """Run a one-shot query."""
    return terminal_run_query(query, runtime=runtime, mode=mode)


def main(runtime: Optional[ApplicationRuntime] = None) -> int:
    """CLI entry point supporting both interactive REPL and one-shot commands."""
    parser = argparse.ArgumentParser(
        description=f"BR JARVIS v{VERSION} ({CODENAME}) — Advanced Cognitive Agent Terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Optional prompt or query to run in one-shot mode.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=VALID_MODES,
        default="general",
        help=f"Agent persona mode ({', '.join(VALID_MODES)}). Default: general.",
    )
    parser.add_argument(
        "--model",
        help="Specify active model backend profile (gemini, claude, gpt, mistral, ollama).",
    )
    parser.add_argument(
        "-s",
        "--session",
        help="Session ID to create or resume.",
    )
    parser.add_argument(
        "--permission",
        help="Specify active permission policy (auto, plan, accept_edits, confirm_destructive, confirm_all, deny).",
    )
    parser.add_argument(
        "--style",
        choices=["compact", "detailed", "minimal", "verbose"],
        default="compact",
        help="Set terminal rendering style (compact, detailed, minimal, verbose). Default: compact.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug output (tool arguments, timings, telemetry).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display subsystem telemetry and health diagnostics.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run system doctor self-healing diagnostic checks.",
    )
    parser.add_argument(
        "-p",
        "--plan",
        metavar="GOAL",
        help="Decompose a goal into a step plan and prompt for approval before executing.",
    )
    parser.add_argument(
        "--mouse",
        action="store_true",
        default=None,
        help="Enable interactive mouse support in terminal REPL (click cursor, select completions, scroll).",
    )
    parser.add_argument(
        "--no-mouse",
        action="store_true",
        default=False,
        help="Disable interactive mouse support (standard terminal text selection).",
    )

    parsed = parser.parse_args()
    app_runtime = runtime

    # Apply environment/runtime overrides
    if parsed.permission:
        os.environ["JARVIS_PERMISSION_MODE"] = parsed.permission.upper()
        try:
            from brjarvis.security.permissions import PERMISSIONS

            PERMISSIONS.set_mode(parsed.permission)
        except Exception:
            pass
        try:
            from brjarvis.security.policy_engine import get_policy_engine

            get_policy_engine().set_mode(parsed.permission)
        except Exception:
            pass

    # Subsystem status check
    if parsed.status:
        session = TerminalSession(runtime=app_runtime, mode=parsed.mode, auto_welcome=False)
        session.commands.execute("/status")
        return 0

    # Doctor diagnostics
    if parsed.doctor:
        session = TerminalSession(runtime=app_runtime, mode=parsed.mode, auto_welcome=False)
        session.commands.execute("/doctor")
        return 0

    # Plan mode one-shot
    if parsed.plan:
        session = TerminalSession(runtime=app_runtime, mode=parsed.mode, session_id=parsed.session, auto_welcome=False)
        if parsed.verbose:
            session.verbose = True
        if parsed.no_mouse:
            session.set_mouse_support(False)
        elif parsed.mouse:
            session.set_mouse_support(True)
        session.output_style = parsed.style
        session.commands.execute(f"/plan {parsed.plan}")
        return 0

    # Providers CLI diagnostics (test, health, models, quotas)
    if parsed.query and parsed.query[0].lower() in ("providers", "provider"):
        subcmd = parsed.query[1].lower() if len(parsed.query) > 1 else "health"
        try:
            from jarvis.gateway.cli import handle_providers_cli

            return handle_providers_cli(subcmd)
        except Exception as e:
            logger.error("Failed to run providers command: %s", e)
            print(f"Error running providers command: {e}")
            return 1

    # One-shot query mode
    if parsed.query:
        query_text = " ".join(parsed.query).strip()
        if query_text:
            return run_query(query_text, runtime=app_runtime, mode=parsed.mode)

    # Interactive REPL mode
    session = TerminalSession(runtime=app_runtime, mode=parsed.mode, session_id=parsed.session)
    if parsed.no_mouse:
        session.set_mouse_support(False)
    elif parsed.mouse:
        session.set_mouse_support(True)
    if parsed.model and hasattr(session, "commands"):
        session.commands.execute(f"/model {parsed.model}")
    if parsed.verbose:
        session.verbose = True
    session.output_style = parsed.style
    try:
        session.run_repl()
        return 0
    except (KeyboardInterrupt, EOFError):
        session.close(consolidate=True)
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
