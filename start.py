#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start.py — BR JARVIS MK40.2+ Canonical Application Bootstrap & Launcher
=============================================================================
Universal master launcher and entry point for BR JARVIS.

Commands & Usage:
  python start.py                       Display system status & diagnostics overview
  python start.py cli                   Launch interactive CLI terminal REPL
  python start.py web [--port 8000]     Launch FastAPI web server & desktop dashboard
  python start.py doctor [--fix]        Run comprehensive diagnostic health audit
  python start.py status                Display quick status & subsystem readiness
  python start.py voice                 Launch Voice Assistant & Cyberpunk HUD
  python start.py career [studio|sync]  Launch Career OS Studio or run CRM sync
  python start.py test [pytest args]    Run automated test suite
  python start.py version               Print version metadata & build details
  python start.py "<query>"             Execute natural language task one-shot
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles and subprocesses
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Dynamic Path & Environment Initialization ────────────────────────────────
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from brjarvis.core.paths import ensure_canonical_python

    ensure_canonical_python()
except Exception as _init_err:
    print(f"[Warning] Environment canonical check note: {_init_err}", file=sys.stderr)

# Import core version metadata (lightweight, zero-dependency)
from brjarvis.core.version import BUILD, CODENAME, VERSION  # noqa: E402


# ── Backwards-Compatible Public API Re-Exports ──────────────────────────────
def doctor(auto_confirm: bool = False) -> dict:
    """Backwards-compatible doctor entry point."""
    from brjarvis.apps.bootstrap import show_doctor
    from brjarvis.diagnostics.doctor import run_diagnostics_audit

    rep = run_diagnostics_audit(auto_repair=auto_confirm)
    show_doctor(rep)
    return rep


def core_doctor() -> dict:
    """Run only the rebuilt core readiness audit."""
    from jarvis.core.bootstrap import run_doctor as run_core_doctor

    report = run_core_doctor()
    print(report)
    return report


def launch_career_sync() -> dict:
    """Trigger career application and email inbox synchronization."""
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    stats = db.get_stats() if hasattr(db, "get_stats") else {"total": len(db.list_applications())}
    print(f"✓ Career CRM synchronized. Total applications: {stats.get('total', len(db.list_applications()))}")
    return stats


def launch_web_server(*args, **kwargs):
    """Backwards-compatible web server launcher entry point."""
    from brjarvis.apps.bootstrap import launch_web_server as _launch_web_server

    return _launch_web_server(*args, **kwargs)


def run_tests(extra_args: list[str] | None = None) -> int:
    """Run pytest suite through virtual environment."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest"] + (extra_args or [])
    try:
        return subprocess.call(cmd, cwd=str(_ROOT))
    except Exception as e:
        print(f"Error running pytest: {e}", file=sys.stderr)
        return 1


# ── Primary Launcher CLI Dispatcher ──────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    """Master application dispatcher."""
    raw_args = list(sys.argv[1:] if argv is None else argv)

    # 1. No arguments -> Interactive Selection Menu & Overview
    if not raw_args:
        from brjarvis.apps.bootstrap import interactive_menu

        return interactive_menu()

    first = raw_args[0].lower().strip().lstrip("-")

    # 2. Version Flag
    if first in ("v", "version"):
        print(f"BR JARVIS v{VERSION} ({CODENAME}) | Build: {BUILD}")
        return 0

    # 3. Help Flag
    if first in ("h", "help", "?"):
        from brjarvis.apps.bootstrap import show_help

        show_help()
        return 0

    # 4. Status Command
    if first in ("status", "info", "health"):
        from brjarvis.apps.bootstrap import show_status

        show_status()
        return 0

    # 5. Doctor & Diagnostic Diagnostics
    if first in ("doctor", "check", "diagnose", "diagnostics"):
        auto_fix = any(arg in raw_args for arg in ("--fix", "-f", "--repair", "--auto-fix"))
        doctor(auto_confirm=auto_fix)
        return 0

    # 5b. Rebuilt Core Doctor
    if first in ("core-doctor", "core_doctor"):
        core_doctor()
        return 0

    # 5c. Rebuilt Jarvis CLI REPL
    if first in ("jarvis-cli", "new-cli"):
        from jarvis.surfaces.cli.repl import run_cli

        run_cli()
        return 0

    # 5d. Rebuilt Jarvis Web Control Plane
    if first in ("jarvis-web", "new-web"):
        import uvicorn
        from jarvis.surfaces.web.server import create_app

        parser = argparse.ArgumentParser(prog="start.py jarvis-web", add_help=False)
        parser.add_argument("--port", "-p", type=int, default=8000)
        parser.add_argument("--host", "-h", type=str, default="127.0.0.1")
        parsed, _ = parser.parse_known_args(raw_args[1:])
        print(f"Starting rebuilt JARVIS Control Plane on http://{parsed.host}:{parsed.port}")
        uvicorn.run(create_app(), host=parsed.host, port=parsed.port)
        return 0

    # 6. Interactive CLI REPL
    if first in ("cli", "repl", "terminal", "interactive"):
        from brjarvis.core.cli import main as cli_main

        sys.argv = [sys.argv[0]] + raw_args[1:]
        return cli_main()

    # 7. Web Server & Dashboard
    if first in ("web", "server", "api", "dashboard", "ui"):
        parser = argparse.ArgumentParser(prog="start.py web", add_help=False)
        parser.add_argument(
            "--port", "-p", type=int, default=int(os.environ.get("PORT", os.environ.get("BR_SERVER_PORT", "8000")))
        )
        parser.add_argument("--host", "-h", type=str, default="127.0.0.1")
        parser.add_argument("--no-open", action="store_true", default=False)
        parsed, _ = parser.parse_known_args(raw_args[1:])

        target_url = f"http://{parsed.host}:{parsed.port}"

        open_url = None if parsed.no_open else target_url
        launch_web_server(open_url=open_url, host=parsed.host, port=parsed.port)

        return 0

    # 8. Career OS Subsystem
    if first in ("career", "careeros", "career-os"):
        sub = raw_args[1].lower().strip() if len(raw_args) > 1 else "studio"
        if sub in ("sync", "update"):
            launch_career_sync()
            return 0
        elif sub in ("stats", "summary", "list"):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            apps = db.list_applications()
            print(f"Total Applications: {len(apps)}")
            for a in apps[:10]:
                comp = getattr(a, "company", getattr(a, "company_name", "Unknown"))
                st_val = (
                    a.application_status.value if hasattr(a, "application_status") else getattr(a, "status", "UNKNOWN")
                )
                print(f"  • [{st_val:<12}] {comp} — {a.job_title} ({a.application_id})")
            if len(apps) > 10:
                print(f"  ... and {len(apps) - 10} more.")
            return 0
        else:
            from brjarvis.apps.bootstrap import launch_career_studio

            launch_career_studio()
            return 0

    # 9. Sync Command
    if first in ("sync", "career-sync"):
        launch_career_sync()
        return 0

    # 10. Voice Assistant HUD
    if first in ("voice", "hud", "speech"):
        from brjarvis.apps.bootstrap import launch_voice

        launch_voice()
        return 0

    # 11. Floating HUD Widget
    if first in ("floating", "widget", "float"):
        try:
            from brjarvis.desktop.float_widget import main as float_main

            return float_main() or 0
        except Exception as exc:
            print(f"Error launching Floating Widget: {exc}", file=sys.stderr)
            return 1

    # 12. Startup Smoke Verification
    if first in ("smoke", "sanity", "verify"):
        try:
            from scripts.smoke_startup import main as smoke_main

            return smoke_main()
        except Exception as exc:
            print(f"Error executing smoke verification: {exc}", file=sys.stderr)
            return 1

    # 13. Audio & Voice Diagnostic Probe
    if first in ("audio", "sound", "mic", "microphone"):
        try:
            from scripts.probe_voice_env import main as probe_main

            return probe_main()
        except Exception as exc:
            print(f"Error executing audio probe: {exc}", file=sys.stderr)
            return 1

    # 14. Pytest Test Runner
    if first in ("test", "tests", "pytest"):
        return run_tests(raw_args[1:])

    # 15. Fallback: Query / Intent Execution
    from brjarvis.core.cli import run_query

    query_str = " ".join(raw_args)
    return run_query(query_str)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\n\n[JARVIS] Session terminated by user. Goodbye.")
        sys.exit(0)
    except SystemExit as _se:
        sys.exit(_se.code if _se.code is not None else 0)
    except Exception as _fatal:
        print(f"\n[Fatal Error] {_fatal}", file=sys.stderr)
        print("Tip: Run 'python start.py doctor' to diagnose system health.", file=sys.stderr)
        sys.exit(1)
