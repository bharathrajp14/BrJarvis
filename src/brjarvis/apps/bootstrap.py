# src/brjarvis/apps/bootstrap.py — Canonical Application Bootstrap Engine for BR JARVIS MK40.2+
from __future__ import annotations

import atexit
import os
import platform
import sys
from datetime import datetime
from typing import Optional

from brjarvis.core.paths import paths
from brjarvis.core.version import BUILD, CODENAME, VERSION

# Ensure environment variables from .env are loaded immediately
if paths.DOTENV_FILE.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(paths.DOTENV_FILE)
    except ImportError:
        pass

from brjarvis.diagnostics.doctor import DoctorReport, run_diagnostics_audit

PYTHON = sys.executable
BASE_DIR = paths.PROJECT_ROOT
LOG_DIR = paths.LOG_ROOT
PID_FILE = paths.PID_FILE

# Setup Rich formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text

    console = Console()
except ImportError:
    print("Notice: 'rich' module is missing. Running in basic console mode.")

    class DummyConsole:
        def print(self, *args, **kwargs):
            print(*args)

        def clear(self):
            pass

    console = DummyConsole()  # type: ignore


def _cleanup_pid_file():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


atexit.register(_cleanup_pid_file)


def banner():
    console.clear()
    now = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")
    text = Text(justify="center")
    text.append("⚡ BR JARVIS — ADVANCED AI OPERATING SYSTEM ⚡\n", style="bold cyan")
    text.append("Autonomous Cognitive Agent Architecture & Isolated Sandbox Lifecycle Engine\n\n", style="dim")
    text.append(f"Version: {VERSION}  │  Build: {BUILD}  │  Codename: {CODENAME}\n", style="bold green")
    text.append(
        f"Python: {sys.version.split()[0]}  │  Platform: {platform.system()}  │  Security: FAIL-CLOSED 🛡️\n",
        style="cyan",
    )
    text.append(now, style="dim")

    panel = Panel(text, border_style="bold cyan", padding=(0, 2))
    console.print(panel)
    console.print()


def show_status():
    banner()
    rep = run_diagnostics_audit(auto_repair=False)

    # Environment
    table_env = Table(title="Environment & Architecture", title_style="bold magenta", show_header=False, box=None)
    table_env.add_column("Property", style="bold")
    table_env.add_column("Value")
    table_env.add_row("Project Root", str(paths.PROJECT_ROOT))
    table_env.add_row("Source Root", str(paths.SOURCE_ROOT))
    table_env.add_row("Runtime Root", str(paths.RUNTIME_ROOT))
    table_env.add_row("Workspace Root", str(paths.WORKSPACE_ROOT))
    table_env.add_row("Python Executable", sys.executable)
    venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    table_env.add_row("Virtual Env", f"[green]Active ({paths.VENV_DIR})[/]" if venv else "[yellow]Not detected[/]")

    health_val = rep["overall_health"]
    health_style = (
        "bold green" if health_val == "HEALTHY" else ("bold red" if "FAILED" in health_val else "bold yellow")
    )
    table_env.add_row("Overall Health", f"[{health_style}]{health_val}[/]")

    # Backends
    table_be = Table(title="AI Backends & Gateway Routing", title_style="bold magenta", show_header=False, box=None)
    has_any = False
    for label, ok in rep["api_keys"].items():
        table_be.add_row(
            f"[green]✓ {label}[/]" if ok else f"[dim]○ {label}[/]",
            "[green]Configured[/]" if ok else "[dim]Not Configured[/]",
        )
        if ok:
            has_any = True

    # Subsystems
    table_sys = Table(title="Subsystems & Registries", title_style="bold magenta", show_header=False, box=None)
    for name, status_text in rep["subsystems_status"].items():
        table_sys.add_row(f"[green]✓ {name}[/]", status_text)

    console.print(table_env)
    console.print()
    if not has_any:
        console.print("[bold yellow]⚠ No backends configured. Add keys to .env[/]")
    console.print(table_be)
    console.print()
    console.print(table_sys)
    console.print()


def show_doctor(rep: Optional[DoctorReport] = None):
    if rep is None:
        rep = run_diagnostics_audit(auto_repair=False)
    show_status()

    # Detailed Python Packages Table
    table_pkg = Table(title="Python Runtime Packages", title_style="bold cyan")
    table_pkg.add_column("Package", style="bold")
    table_pkg.add_column("Status")
    table_pkg.add_column("Version / Details")
    for pkg, (ok, ver) in rep["python_packages"].items():
        table_pkg.add_row(pkg, "[green]Installed[/]" if ok else "[red]Missing[/]", ver)

    # Detailed System Tools Table
    table_tools = Table(title="System & Binary Tools", title_style="bold cyan")
    table_tools.add_column("Category", style="bold")
    table_tools.add_column("Binary")
    table_tools.add_column("Status")
    for cat, found in rep["system_tools"].items():
        table_tools.add_row(cat, found or "N/A", "[green]Available[/]" if found else "[yellow]Not Found[/]")

    console.print(table_pkg)
    console.print()
    console.print(table_tools)
    console.print()


def launch_cli():
    console.print("\n[bold cyan]▶ Starting CLI Orchestrator[/]")
    console.print("[dim]Type /quit to exit.[/]\n")
    from brjarvis.core.cli import run_cli

    run_cli()


def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    import socket

    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


def launch_web_server(
    open_url: Optional[str] = None,
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
):
    """Start the canonical web server with explicit CLI-over-environment settings."""
    bind_host = (host or os.environ.get("HOST", "127.0.0.1")).strip() or "127.0.0.1"
    requested_port = int(port if port is not None else os.environ.get("PORT", os.environ.get("BR_SERVER_PORT", "8000")))
    port = find_available_port(requested_port)

    if port != requested_port:
        console.print(f"[yellow]⚠ Port {requested_port} is busy. Automatically re-routing to port {port}.[/]")

    display_host = "127.0.0.1" if bind_host in {"0.0.0.0", "::"} else bind_host

    base_url = f"http://{display_host}:{port}"
    if open_url:
        if open_url.startswith("/"):
            target_url = f"{base_url}{open_url}"
        else:
            target_url = open_url

    else:
        target_url = base_url

    console.print("\n[bold cyan]▶ Starting BR Web Core Server[/]")
    console.print(f"  [green]Server Running on[/] {base_url}")
    console.print(f"  [green]Interface URL[/] Access [cyan]{target_url}[/]")
    console.print(f"  [green]Control plane[/] Rebuilt UI at [cyan]{base_url}/web[/] (legacy rollback: [cyan]{base_url}/web/legacy[/])")
    console.print("[dim]Press Ctrl+C to shut down.[/]\n")

    import uvicorn

    try:
        from brjarvis.web.api.server import create_app

        app = create_app()
    except Exception:
        from brjarvis.web.api.app import app
    uvicorn.run(app, host=bind_host, port=port, log_level="info")


def launch_career_studio(open_url: Optional[str] = None):
    launch_web_server(open_url="/career")


def launch_voice():
    console.print("\n[bold cyan]▶ Starting BR Voice Assistant Cyberpunk HUD[/]")
    try:
        from brjarvis.desktop.ui_mark import run_voice_ui

        run_voice_ui()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Error launching Voice Assistant: {e}[/]")


def show_help():
    banner()
    table = Table(title="BR JARVIS MK40.2+ Commands & Modes", title_style="bold cyan")
    table.add_column("Command / Argument", style="bold green")
    table.add_column("Description")

    table.add_row("python start.py", "Display system status and diagnostics overview")
    table.add_row("python start.py doctor [--fix]", "Run comprehensive diagnostic audit and dependency checks")
    table.add_row("python start.py cli", "Launch interactive CLI REPL session")
    table.add_row("python start.py web", "Launch BR Web Server and REST API (:8000)")
    table.add_row("python start.py career", "Launch Career OS Studio and CRM portal")
    table.add_row("python start.py sync", "Synchronize Career CRM applications and spreadsheets")
    table.add_row("python start.py voice", "Launch Voice Assistant and HUD interface")
    table.add_row("python start.py <query>", "Execute a one-shot natural language query or task")
    table.add_row("python start.py --help", "Show this help and usage message")

    console.print(table)
    console.print()


def interactive_menu() -> int:
    """Display an interactive multi-option selection menu when run without CLI arguments."""
    show_status()
    console.print("\n[bold cyan]⚡ SELECT AN OPERATIONAL MODE TO LAUNCH ⚡[/]")

    menu_table = Table(box=None, show_header=False, padding=(0, 2))
    menu_table.add_column("Key", style="bold cyan", justify="right")
    menu_table.add_column("Option", style="bold white")
    menu_table.add_column("Description", style="dim")

    menu_table.add_row("[1]", "🌐 Web Dashboard & 3D Galaxy", "FastAPI web control plane & Three.js graph (:8000)")
    menu_table.add_row("[2]", "💼 Career OS Studio & ATS Scorer", "Resume engine, job matching & CRM portal (/career)")
    menu_table.add_row("[3]", "🎙️ Cyberpunk Voice Assistant HUD", "PySide6 real-time audio waveform & EdgeTTS")
    menu_table.add_row("[4]", "💻 Interactive CLI Terminal REPL", "Command session with 30+ slash commands")
    menu_table.add_row("[5]", "🪟 Floating Desktop HUD Widget", "Compact desktop widget with quick triggers")
    menu_table.add_row("[6]", "📊 System Status & Health", "Environment, active AI backends & registries")
    menu_table.add_row("[7]", "🩺 Comprehensive Diagnostics (Doctor)", "Diagnostic audit with auto-repair advice")
    menu_table.add_row("[8]", "⚡ Lifecycle Smoke Verification", "12 non-destructive startup invariant tests")
    menu_table.add_row("[9]", "🎤 Microphone & Audio Hardware Probe", "Audio driver, input/output device test")
    menu_table.add_row("[10]", "🔄 Sync Career CRM & Spreadsheets", "Synchronize applications and Excel tracker")
    menu_table.add_row("[0]", "🚪 Exit", "Close launcher session")

    console.print(menu_table)
    console.print()

    try:
        choice = (
            Prompt.ask(
                "[bold green]▶ Enter option number[/]",
                default="1",
                choices=[
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                    "0",
                    "q",
                    "exit",
                    "quit",
                    "web",
                    "career",
                    "voice",
                    "cli",
                    "status",
                    "doctor",
                    "smoke",
                    "audio",
                    "sync",
                ],
            )
            .strip()
            .lower()
        )
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Session closed.[/]")
        return 0

    if choice in ("1", "web"):
        launch_web_server()
    elif choice in ("2", "career", "careeros"):
        launch_career_studio()
    elif choice in ("3", "voice", "hud"):
        launch_voice()
    elif choice in ("4", "cli", "repl", "terminal"):
        launch_cli()
    elif choice in ("5", "floating", "widget"):
        try:
            from brjarvis.desktop.float_widget import main as float_main

            return float_main() or 0
        except Exception as exc:
            console.print(f"[red]Error launching Floating Widget: {exc}[/]")
            return 1
    elif choice in ("6", "status", "info"):
        show_status()
    elif choice in ("7", "doctor", "check"):
        rep = run_diagnostics_audit(auto_repair=False)
        show_doctor(rep)
    elif choice in ("8", "smoke", "verify"):
        try:
            from scripts.smoke_startup import main as smoke_main

            return smoke_main()
        except Exception as exc:
            console.print(f"[red]Error executing smoke verification: {exc}[/]")
            return 1
    elif choice in ("9", "audio", "sound", "mic"):
        try:
            from scripts.probe_voice_env import main as probe_main

            return probe_main()
        except Exception as exc:
            console.print(f"[red]Error executing audio probe: {exc}[/]")
            return 1
    elif choice in ("10", "sync"):
        from brjarvis.career.crm.database import get_career_crm_db

        db = get_career_crm_db()
        console.print(f"[green]✓ Career CRM synchronized. Total applications: {len(db.list_applications())}[/]")
    elif choice in ("0", "q", "exit", "quit"):
        console.print("[dim]Exiting BR JARVIS. Have a great day![/]")
        return 0
    return 0


def main() -> int:
    """Canonical Application Bootstrap CLI Dispatcher."""
    try:
        args = sys.argv[1:]
        if not args:
            return interactive_menu()

        cmd = args[0].lower().strip().lstrip("-")
        if cmd in ("status", "info"):
            show_status()
        elif cmd in ("help", "h", "?"):
            show_help()
        elif cmd in ("doctor", "check"):
            auto_fix = "--fix" in args or "-f" in args
            rep = run_diagnostics_audit(auto_repair=auto_fix)
            show_doctor(rep)
        elif cmd in ("cli", "repl", "terminal"):
            launch_cli()
        elif cmd in ("web", "server", "dashboard"):
            launch_web_server()
        elif cmd in ("career", "careeros", "career-os", "studio"):
            launch_career_studio()
        elif cmd in ("sync", "career-sync"):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            console.print(f"[green]Career CRM synchronized. Total applications: {len(db.list_applications())}[/]")
        elif cmd in ("voice", "hud"):
            launch_voice()
        else:
            # Default to CLI asking question or executing query
            from brjarvis.core.cli import run_query

            return run_query(" ".join(args))
        return 0
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Session closed.[/]")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
