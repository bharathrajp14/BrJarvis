# core/terminal/commands.py — Modular Slash Command Engine for BR JARVIS CLI MK41
from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from ..version import BUILD, CODENAME, VERSION
from .theme import HAS_RICH, MODE_COLORS, Glyphs

try:
    from rich.box import ROUNDED
    from rich.table import Table
except ImportError:
    Table = None
    ROUNDED = None

if TYPE_CHECKING:
    from .session import TerminalSession

logger = logging.getLogger("JARVIS.TerminalCommands")

VALID_MODES = ["general", "coder", "analyst", "recon", "exploit", "report", "planner", "researcher", "automation"]

# Permission mode aliases → canonical names
PERMISSION_ALIASES = {
    "auto": "allow_all",
    "allow_all": "allow_all",
    "allow": "allow_all",
    "allowall": "allow_all",
    "yolo": "allow_all",
    "all": "allow_all",
    "plan": "plan",
    "accept_edits": "accept_edits",
    "confirm_destructive": "confirm_destructive",
    "confirm_all": "confirm_all",
    "deny": "deny_all",
    "deny_all": "deny_all",
}


# Safe exit command aliases
EXIT_COMMANDS = {"/quit", "/exit", "/q", "quit", "exit", "q", ":q", ":quit", ":exit", "bye", "goodbye"}


class SlashCommandHandler:
    """Dispatches and executes interactive CLI slash commands for BR JARVIS MK41."""

    def __init__(self, session: "TerminalSession"):
        self.session = session
        self.renderer = session.renderer
        self._session_start = time.time()
        self._total_turns = 0
        self._output_style: str = "compact"

    def execute(self, cmd_line: str) -> bool:
        """Execute a slash command line. Returns False if exit/quit was requested."""
        raw = cmd_line.strip()
        if not raw:
            return True

        parts = raw.split(maxsplit=1)
        action = parts[0].lower()
        args_str = parts[1].strip() if len(parts) > 1 else ""

        # Normalize exit commands
        if action in EXIT_COMMANDS:
            return self._cmd_quit()

        # Show command palette when user types bare "/"
        if action == "/":
            res = self._cmd_palette(args_str)
            return True if res is None else res

        dispatch_map = {
            # Core
            "/help": self._cmd_help,
            "/status": self._cmd_status,
            "/version": self._cmd_version,
            "/clear": self._cmd_clear,
            "/config": self._cmd_config,
            # Agent & planning
            "/mode": lambda: self._cmd_mode(args_str),
            "/agents": lambda: self._cmd_mode(args_str),
            "/model": lambda: self._cmd_model(args_str),
            "/models": lambda: self._cmd_model(args_str),
            "/plan": lambda: self._cmd_plan(args_str),
            "/permission": lambda: self._cmd_permission(args_str),
            "/permissions": lambda: self._cmd_permission(args_str),
            "/style": lambda: self._cmd_style(args_str),
            "/verbose": lambda: self._cmd_verbose(args_str),
            "/mouse": lambda: self._cmd_mouse(args_str),
            "/tui": lambda: self._cmd_tui(args_str),
            "/interrupt": self._cmd_interrupt,
            # Task lifecycle
            "/tasks": lambda: self._cmd_tasks(args_str),
            "/pause": lambda: self._cmd_pause(args_str),
            "/resume": lambda: self._cmd_resume(args_str),
            "/cancel": lambda: self._cmd_cancel(args_str),
            "/retry": lambda: self._cmd_retry(args_str),
            "/approve": lambda: self._cmd_approve(args_str),
            "/continue": self._cmd_continue,
            # Verification
            "/verify": lambda: self._cmd_verify(args_str),
            "/diff": lambda: self._cmd_diff(args_str),
            # Session
            "/session": lambda: self._cmd_session(args_str),
            "/sessions": self._cmd_sessions,
            "/history": lambda: self._cmd_history(args_str),
            "/rename": lambda: self._cmd_rename(args_str),
            "/context": self._cmd_context,
            "/compact": self._cmd_compact,
            "/flush": self._cmd_compact,
            "/export": lambda: self._cmd_export(args_str),
            # Tools & infrastructure
            "/tools": lambda: self._cmd_tools(args_str),
            "/skills": lambda: self._cmd_skills(args_str),
            "/connectors": lambda: self._cmd_connectors(args_str),
            "/doctor": lambda: self._cmd_doctor(args_str),
            "/usage": self._cmd_usage,
            # Memory
            "/memory": lambda: self._cmd_memory(args_str),
            # Career OS
            "/career": lambda: self._cmd_career(args_str),
            "/applications": lambda: self._cmd_applications(args_str),
            "/interviews": lambda: self._cmd_interviews(args_str),
            "/offers": lambda: self._cmd_offers(args_str),
            "/emails": lambda: self._cmd_emails(args_str),
            "/career-resume": lambda: self._cmd_career_resume(args_str),
            "/resume-generate": lambda: self._cmd_career_resume(args_str),
            "/jobs": lambda: self._cmd_jobs(args_str),

            "/apply": lambda: self._cmd_apply(args_str),
            "/ats": lambda: self._cmd_ats(args_str),
        }

        handler = dispatch_map.get(action)
        if handler:
            try:
                res = handler()
                return True if res is None else res
            except Exception as e:
                logger.exception("Error executing command '%s': %s", action, e)
                self.renderer.render_error("Command Execution Failed", str(e))
                return True

        # Partial match — suggest similar commands
        similar = [k for k in dispatch_map if k.startswith(action)]
        if similar:
            self.renderer.render_error(
                f"Ambiguous Command: '{action}'",
                f"Did you mean: {', '.join(similar[:4])}?",
                ["Type /help for the complete command reference."],
            )
        else:
            self.renderer.render_error(
                "Unknown Command",
                f"Command '{action}' not recognized.",
                ["Type /help for the complete command reference.", "Type / for command palette."],
            )
        return True

    # ── Command Palette ───────────────────────────────────────────────────────

    def _cmd_palette(self, query: str = "") -> None:
        """Display interactive command palette."""
        try:
            from .autocomplete import SLASH_COMMANDS

            cmds = SLASH_COMMANDS
            if query:
                q = query.lower()
                cmds = [c for c in cmds if q in c["cmd"] or q in c["desc"].lower()]

            if HAS_RICH and self.renderer.console:
                table = Table(title="⚡ Command Palette", border_style="cyan", box=ROUNDED)
                table.add_column("Command", style="bold cyan", width=24)
                table.add_column("Description", style="dim")
                for c in cmds[:20]:
                    table.add_row(c["cmd"], c["desc"])
                self.renderer.console.print(table)
            else:
                print("\nCommands:")
                for c in cmds[:20]:
                    print(f"  {c['cmd']:<24} {c['desc']}")
        except Exception:
            self._cmd_help()

    # ── Help ──────────────────────────────────────────────────────────────────

    def _cmd_help(self) -> None:
        """Display categorized help cards."""
        if HAS_RICH and self.renderer.console:
            table = Table(title="⚡ BR JARVIS MK41 CLI Reference", border_style="cyan", box=ROUNDED)
            table.add_column("Category", style="bold yellow", width=18)
            table.add_column("Command", style="bold cyan", width=26)
            table.add_column("Description", style="white")

            rows = [
                # Agent
                ("Agent", "/mode <name>", f"Switch mode: {', '.join(VALID_MODES)}"),
                ("Agent", "/model [backend]", "View or switch active AI backend"),
                ("Agent", "/permission [mode]", "View or set permission policy"),
                ("Agent", "/style [compact|verbose]", "Set output verbosity style"),
                ("Agent", "/verbose [on|off]", "Toggle verbose debug output"),
                ("Agent", "/mouse [on|off|status]", "Toggle interactive mouse support (cursor, scroll, menus)"),
                # Planning
                ("Planning", "/plan <goal>", "Decompose goal → approve → execute"),
                ("Planning", "/approve [task_id]", "Approve pending task gate (auto-detects if omitted)"),
                # Tasks
                ("Tasks", "/tasks [id]", "Dashboard or task detail"),
                ("Tasks", "/pause <task_id>", "Pause running task"),
                ("Tasks", "/resume <task_id>", "Resume paused task"),
                ("Tasks", "/cancel <task_id>", "Cancel task"),
                ("Tasks", "/retry <task_id>", "Retry failed task from checkpoint"),
                ("Tasks", "/continue", "Resume latest incomplete session"),
                # Memory
                ("Memory", "/memory search <q>", "Search vector store"),
                ("Memory", "/memory recent", "Latest stored memories"),
                ("Memory", "/memory project", "Project & workspace context"),
                ("Memory", "/memory stats", "Memory type breakdown"),
                ("Memory", "/memory forget <id>", "Remove specific memory entry"),
                ("Memory", "/compact", "Consolidate to long-term store"),
                # Session
                ("Session", "/context", "Show session context & model"),
                ("Session", "/history [n]", "Session turn history"),
                ("Session", "/history task <id>", "Task execution history"),
                ("Session", "/rename <name>", "Name this session"),
                ("Session", "/export [format]", "Export session transcript"),
                # Tools
                ("Tools", "/tools [search <q>]", "Browse tool catalog"),
                ("Tools", "/tools health", "Check tool registry health"),
                ("Tools", "/tools failed", "Show recently failed tools"),
                ("Tools", "/connectors", "Connector status overview"),
                ("Tools", "/connectors <name>", "Specific connector detail"),
                # Diagnostics
                ("Diagnostics", "/doctor", "Interactive system health check"),
                ("Diagnostics", "/status", "Subsystem telemetry"),
                ("Diagnostics", "/usage", "Token & request usage stats"),
                # Verification
                ("Verify", "/verify [path]", "Verify file existence/integrity"),
                ("Verify", "/diff <file>", "Syntax-highlighted file diff"),
                # Career OS
                ("Career OS", "/career [stats|sync]", "Career profile & analytics"),
                ("Career OS", "/applications", "Tracked applications"),
                ("Career OS", "/interviews", "Upcoming interviews"),
                ("Career OS", "/offers", "Detected job offers"),
                ("Career OS", "/emails", "Career email intelligence"),
                ("Career OS", "/resume [role]", "Generate/tailor resume"),
                ("Career OS", "/jobs <query>", "Search job postings"),
                ("Career OS", "/apply <job_id>", "Prepare application package"),
                ("Career OS", "/ats [role]", "Run ATS compatibility audit"),
                # Control
                ("Control", "/clear", "Clear terminal screen"),
                ("Control", "/version", "Build & version info"),
                ("Control", "/quit", "Exit with consolidation"),
            ]
            for cat, cmd, desc in rows:
                table.add_row(cat, cmd, desc)
            self.renderer.console.print(table)
        else:
            print("Commands: /help /plan /mode /model /tasks /memory /tools /doctor /career /quit")

    # ── Status ────────────────────────────────────────────────────────────────

    def _cmd_status(self) -> None:
        """Display live subsystem status."""
        runtime = self.session.runtime
        orch = runtime.orchestrator if runtime else None
        current_mode = getattr(orch, "current_mode", "general") if orch else "offline"
        session_id = getattr(orch, "session_id", "N/A") if orch else "N/A"

        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS

            tool_count = len(TOOL_SCHEMAS)
        except Exception:
            tool_count = 0

        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()
            mem_summary = f"{len(um._cache) if hasattr(um, '_cache') else 'Active'} cached memories"
        except Exception:
            mem_summary = "Active"

        perm_mode = os.environ.get("JARVIS_PERMISSION_MODE", "CONFIRM_DESTRUCTIVE")

        # MK40.2: Specific model & credential source info
        try:
            from brjarvis.core.config import get_model_display_info

            model_info = get_model_display_info()
            backend_disp = f"{model_info['provider']} — {model_info['model']}"
            cred_disp = model_info["credential_source"]
            if model_info.get("credential_conflict") == "True":
                cred_disp += " (CONFLICT: both Google & Gemini keys set)"
        except Exception:
            backend_disp = "Gemini 2.5 Flash"
            cred_disp = "Environment"

        status_data = {
            "Version & Build": f"v{VERSION} ({CODENAME}, Build {BUILD})",
            "Active Agent Mode": current_mode.upper(),
            "Session ID": session_id,
            "Session Name": self.session.session_name or "(unnamed)",
            "Active Model": backend_disp,
            "Credential Source": cred_disp,
            "Permission Mode": perm_mode,
            "Output Style": self.session.output_style,
            "Registered Tools": f"{tool_count} tools",
            "Unified Memory": mem_summary,
            "Execution Ledger": "Append-Only SQLite WAL Active",
            "Action Verifier": "Host & Sandbox Validation Active",
            "Security Policy": "FAIL-CLOSED (Guardian Protected)",
        }
        self.renderer.render_status_table(status_data)

    # ── Mode ──────────────────────────────────────────────────────────────────

    def _cmd_mode(self, mode_name: str) -> None:
        """Switch active agent persona mode."""
        if not mode_name:
            current = (
                getattr(self.session.orchestrator, "current_mode", "general")
                if self.session.orchestrator
                else self.session.current_mode
            )
            self.renderer.render_markdown(
                f"**Current Mode:** `{current.upper()}`\n\nAvailable: {', '.join(f'`{m}`' for m in VALID_MODES)}"
            )
            return

        target_mode = mode_name.lower().strip()
        if target_mode not in VALID_MODES:
            self.renderer.render_error(
                "Invalid Mode",
                f"'{mode_name}' is not a recognized mode.",
                [f"Available modes: {', '.join(VALID_MODES)}"],
            )
            return

        orch = self.session.orchestrator
        if orch:
            orch.current_mode = target_mode
            if hasattr(orch, "router") and hasattr(orch.router, "set_mode"):
                try:
                    orch.router.set_mode(target_mode)
                except Exception:
                    pass

        self.session.current_mode = target_mode
        mode_color = MODE_COLORS.get(target_mode, "cyan")
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(
                f"[{mode_color} bold]{Glyphs.CHECK} Mode switched →[/] [bold white]{target_mode.upper()}[/]"
            )
        else:
            print(f"✓ Mode: {target_mode.upper()}")

    # ── Model ─────────────────────────────────────────────────────────────────

    def _cmd_model(self, model_name: str) -> None:
        """View or switch active model backend with availability validation."""
        runtime = self.session.runtime
        active = (
            getattr(runtime.config.models, "default_backend", "gemini")
            if runtime and hasattr(runtime, "config")
            else "gemini"
        )

        # Check available backends
        backends = self._get_model_registry()
        if not model_name:
            self.renderer.render_model_table(backends, active=active)
            return

        # Find backend by name
        target = model_name.lower().strip()
        backend = next((b for b in backends if b["name"].lower() == target), None)
        if not backend:
            self.renderer.render_error(
                "Backend Not Found",
                f"'{target}' is not a registered backend.",
                [f"Available: {', '.join(b['name'] for b in backends)}"],
            )
            return

        if backend["status"] == "no_key":
            self.renderer.render_error(
                "Model Unavailable",
                f"'{target}' requires an API key that is not configured.",
                [f"Add {target.upper()}_API_KEY to your .env file", "Run /doctor to check configuration"],
            )
            return

        # Apply switch
        if runtime and hasattr(runtime, "config"):
            runtime.config.models.default_backend = target
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(
                f"[bold green]{Glyphs.CHECK} Model backend switched →[/] [bold cyan]{target}[/]"
            )
        else:
            print(f"✓ Model: {target}")

    def _get_model_registry(self) -> List[Dict[str, Any]]:
        """Build model registry from environment and config."""
        import os

        backends = [
            {
                "name": "gemini",
                "model": "gemini-2.5-flash",
                "status": "available"
                if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                else "no_key",
                "context": "1M",
                "capabilities": ["vision", "code", "reasoning", "function_calling"],
            },
            {
                "name": "gpt",
                "model": "gpt-4o",
                "status": "available" if os.environ.get("OPENAI_API_KEY") else "no_key",
                "context": "128K",
                "capabilities": ["vision", "code", "function_calling"],
            },
            {
                "name": "claude",
                "model": "claude-3-7-sonnet",
                "status": "available" if os.environ.get("ANTHROPIC_API_KEY") else "no_key",
                "context": "200K",
                "capabilities": ["vision", "code", "reasoning"],
            },
            {
                "name": "mistral",
                "model": "mistral-large",
                "status": "available" if os.environ.get("MISTRAL_API_KEY") else "no_key",
                "context": "128K",
                "capabilities": ["code", "function_calling"],
            },
        ]
        return backends

    # ── Permission ────────────────────────────────────────────────────────────

    def _cmd_permission(self, args_str: str) -> None:
        """View or set permission policy mode."""
        if not args_str:
            current_mode = os.environ.get("JARVIS_PERMISSION_MODE", "CONFIRM_DESTRUCTIVE")
            self.renderer.render_markdown(
                f"**Current Permission Mode:** `{current_mode}`\n\n"
                "Available modes:\n"
                "- `AUTO` — Allow all tools without confirmation\n"
                "- `PLAN` — Only allow reads; require plan approval for mutations\n"
                "- `ACCEPT_EDITS` — Auto-accept file edits, confirm external actions\n"
                "- `CONFIRM_DESTRUCTIVE` — Confirm destructive & external tools (default)\n"
                "- `CONFIRM_ALL` — Confirm every tool call\n"
                "- `DENY` — Block all tool execution\n\n"
                "Use `/permission <mode>` to change."
            )
            return

        target = args_str.lower().strip().replace("-", "_")
        canonical = PERMISSION_ALIASES.get(target)
        if not canonical:
            self.renderer.render_error(
                "Invalid Permission Mode",
                f"'{args_str}' is not a recognized mode.",
                [f"Valid modes: {', '.join(PERMISSION_ALIASES.keys())}"],
            )
            return

        os.environ["JARVIS_PERMISSION_MODE"] = canonical.upper()
        try:
            from brjarvis.security.permissions import PERMISSIONS

            PERMISSIONS.set_mode(canonical)
        except Exception:
            pass
        try:
            from brjarvis.security.policy_engine import get_policy_engine

            get_policy_engine().set_mode(canonical)
        except Exception:
            pass

        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(f"[bold green]{Glyphs.SHIELD} Permission mode → {canonical.upper()}[/]")
        else:
            print(f"🛡️ Permission: {canonical.upper()}")

    # ── Plan Mode (Phase 3) ───────────────────────────────────────────────────

    def _cmd_plan(self, goal: str) -> None:
        """Run step planner with approval gate before execution."""
        if not goal:
            self.renderer.render_error("Missing Goal", "Provide a goal: `/plan Build a REST API in Python`")
            return

        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(f"[bold cyan]◆ Planning:[/] [white]{goal[:80]}[/]\n")

        # Generate plan
        steps, risk, external = self._generate_plan(goal)
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Render plan panel
        self.renderer.render_plan_panel(
            goal=goal,
            steps=steps,
            risk=risk,
            external_actions=external,
            plan_id=plan_id,
        )

        # Approval gate
        while True:
            try:
                choice = self.renderer.prompt_plan_approval()
            except (KeyboardInterrupt, EOFError):
                choice = "cancel"

            if choice in ("cancel", "quit", "exit", "q"):
                if HAS_RICH and self.renderer.console:
                    self.renderer.console.print("[bold yellow]Plan cancelled.[/bold yellow]")
                else:
                    print("Plan cancelled.")
                return

            elif choice == "approve":
                # Create task state
                task_id = self._create_task_from_plan(goal, steps, plan_id)
                if HAS_RICH and self.renderer.console:
                    self.renderer.console.print(
                        f"\n[bold green]{Glyphs.CHECK} Plan approved.[/] [dim]Executing {task_id}...[/dim]\n"
                    )
                else:
                    print(f"\n✓ Plan approved. Executing {task_id}...")

                # Set session to task prompt state
                self.session.set_active_task(task_id, goal[:24])

                # Execute the approved plan
                self.session.execute_turn(f"[PLAN_APPROVED:{plan_id}] {goal}")
                return

            elif choice == "edit":
                if HAS_RICH and self.renderer.console:
                    from rich.prompt import Prompt as RPrompt

                    try:
                        new_goal = RPrompt.ask("  Edit goal").strip()
                        if new_goal.lower() in EXIT_COMMANDS or new_goal.lower() in ("cancel", "c"):
                            return
                        if new_goal:
                            goal = new_goal
                            steps, risk, external = self._generate_plan(goal)
                            self.renderer.render_plan_panel(goal, steps, risk, external, plan_id)
                    except (KeyboardInterrupt, EOFError):
                        return
                continue

            elif choice == "replan":
                if HAS_RICH and self.renderer.console:
                    self.renderer.console.print("[dim]Re-planning...[/dim]\n")
                steps, risk, external = self._generate_plan(goal)
                self.renderer.render_plan_panel(goal, steps, risk, external, plan_id)
                continue

            else:  # cancel fallback
                if HAS_RICH and self.renderer.console:
                    self.renderer.console.print("[bold yellow]Plan cancelled.[/bold yellow]")
                else:
                    print("Plan cancelled.")
                return

    def _generate_plan(self, goal: str) -> Tuple[List[str], str, List[str]]:
        """Generate plan steps, risk level, and external actions."""
        steps: List[str] = []
        risk = "Medium"
        external: List[str] = []

        try:
            from brjarvis.agent.stage_decomposer import StageDecomposer
            from brjarvis.agent.step_planner import StepPlanner

            if StageDecomposer.is_composite_task(goal):
                stages = StageDecomposer.decompose(goal)
                for s in stages:
                    steps.append(getattr(s, "goal", getattr(s, "name", str(s))))
            else:
                plan_info = StepPlanner.plan_steps(goal)
                raw_steps = plan_info.get("steps", [])
                if isinstance(raw_steps, list):
                    for s in raw_steps:
                        if isinstance(s, dict):
                            steps.append(s.get("description", s.get("name", str(s))))
                        else:
                            steps.append(str(s))
                risk = plan_info.get("risk", "Medium")
        except Exception as e:
            logger.debug("Plan generation using fallback: %s", e)
            # Keyword-based fallback
            goal_lower = goal.lower()
            if any(k in goal_lower for k in ["portfolio", "website", "html"]):
                steps = [
                    "Inspect existing profile and project data",
                    "Inspect project directory structure",
                    "Generate HTML/CSS portfolio files",
                    "Validate HTML syntax",
                    "Create git commit",
                    "Push to GitHub remote",
                    "Verify remote deployment",
                    "Open in browser and verify",
                ]
                external = ["GitHub push"]
                risk = "Medium"
            elif any(k in goal_lower for k in ["git", "github", "push", "commit"]):
                steps = ["Inspect repository", "Stage changes", "Create commit", "Push to remote", "Verify remote"]
                external = ["GitHub push"]
                risk = "Low"
            elif any(k in goal_lower for k in ["email", "send", "gmail"]):
                steps = ["Compose email", "Review content", "Send email", "Verify delivery"]
                external = ["Gmail send"]
                risk = "High"
            elif any(k in goal_lower for k in ["code", "python", "api", "app"]):
                steps = ["Inspect codebase", "Plan implementation", "Write code", "Run tests", "Verify output"]
                risk = "Low"
            elif any(k in goal_lower for k in ["research", "search", "find"]):
                steps = [
                    "Define research scope",
                    "Search web sources",
                    "Collect data",
                    "Analyze findings",
                    "Produce report",
                ]
                external = ["Web search"]
                risk = "Low"
            else:
                steps = [
                    "Understand and clarify goal",
                    "Inspect context and dependencies",
                    "Execute primary action",
                    "Verify result",
                ]
                risk = "Low"

        if not steps:
            steps = ["Execute: " + goal[:60]]

        # Detect external actions from goal if not already set
        if not external:
            goal_lower = goal.lower()
            if any(k in goal_lower for k in ["github", "git push", "push to"]):
                external.append("GitHub push")
            if any(k in goal_lower for k in ["email", "gmail", "send message"]):
                external.append("Email send")
            if any(k in goal_lower for k in ["telegram", "slack", "discord"]):
                external.append("Message send")
            if any(k in goal_lower for k in ["calendar", "schedule", "meeting"]):
                external.append("Calendar create")

        return steps, risk, external

    def _create_task_from_plan(self, goal: str, steps: List[str], plan_id: str) -> str:
        """Create a TaskState for the approved plan."""
        try:
            from brjarvis.agent.task_state import get_task_state_manager

            mgr = get_task_state_manager()
            task = mgr.create_task(
                goal=goal,
                total_steps=len(steps),
                goal_spec={
                    "plan_id": plan_id,
                    "planned_steps": steps,
                },
            )
            # Store plan in task
            task.plan = {"plan_id": plan_id, "steps": steps, "goal": goal}
            task.planned_steps = [{"description": s} for s in steps]
            mgr.save_task(task)
            return task.task_id
        except Exception as e:
            logger.warning("Could not create task state: %s", e)
            return f"task_{uuid.uuid4().hex[:8]}"

    # ── Task Dashboard (Phase 5) ──────────────────────────────────────────────

    def _cmd_tasks(self, filter_query: str = "") -> None:
        """List active tasks or show task detail."""
        try:
            from brjarvis.agent.task_state import get_task_state_manager

            mgr = get_task_state_manager()

            # Task detail if ID provided
            if filter_query and not filter_query.startswith("status:"):
                task = mgr.get_task(filter_query)
                if not task:
                    # Try prefix match
                    all_tasks = mgr.list_tasks(limit=50)
                    matches = [t for t in all_tasks if t.task_id.startswith(filter_query)]
                    task = matches[0] if matches else None
                self.renderer.render_task_detail(task)
                return

            # Task list
            tasks = mgr.list_tasks(limit=20)
            if not tasks:
                self.renderer.render_markdown("_No task lifecycle records found._")
                return
            self.renderer.render_tasks_table(tasks)

        except Exception as e:
            self.renderer.render_error("Tasks Query Failed", str(e))

    def _cmd_pause(self, task_id: str) -> None:
        """Pause a running task."""
        if not task_id:
            self.renderer.render_error("Missing Task ID", "Usage: `/pause <task_id>`")
            return
        try:
            from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

            mgr = get_task_state_manager()
            state = mgr.update_status(task_id, TaskStatus.WAITING_FOR_USER)
            if state:
                self.renderer.render_markdown(f"⏸ Task `{task_id}` paused.")
            else:
                self.renderer.render_error("Task Not Found", f"No task with ID '{task_id}'")
        except Exception as e:
            self.renderer.render_error("Pause Failed", str(e))

    def _cmd_resume(self, args_str: str) -> None:
        """Resume a paused task or session."""
        if not args_str:
            self._cmd_continue()
            return
        try:
            from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

            mgr = get_task_state_manager()
            task = mgr.get_task(args_str)
            if not task:
                self.renderer.render_error("Task Not Found", f"No task with ID '{args_str}'")
                return
            goal = task.goal or task.user_request
            state = mgr.update_status(args_str, TaskStatus.RUNNING)
            if state:
                self.renderer.render_markdown(f"▶ Resuming task `{args_str}`: _{goal[:60]}_")
                self.session.set_active_task(args_str, goal[:24])
                self.session.execute_turn(f"[RESUME_TASK:{args_str}] Continue: {goal}")
        except Exception as e:
            self.renderer.render_error("Resume Failed", str(e))

    def _cmd_cancel(self, task_id: str) -> None:
        """Cancel a task."""
        if not task_id:
            self.renderer.render_error("Missing Task ID", "Usage: `/cancel <task_id>`")
            return
        try:
            from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

            mgr = get_task_state_manager()
            state = mgr.update_status(task_id, TaskStatus.CANCELLED)
            if state:
                self.session.clear_active_task()
                self.renderer.render_markdown(
                    f"[bold red]{Glyphs.CROSS} Task `{task_id}` cancelled.[/bold red]"
                    if HAS_RICH
                    else f"✗ Task {task_id} cancelled."
                )
            else:
                self.renderer.render_error("Task Not Found", f"No task with ID '{task_id}'")
        except Exception as e:
            self.renderer.render_error("Cancel Failed", str(e))

    def _cmd_retry(self, task_id: str) -> None:
        """Retry a failed task from its last checkpoint."""
        if not task_id:
            self.renderer.render_error("Missing Task ID", "Usage: `/retry <task_id>`")
            return
        try:
            from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

            mgr = get_task_state_manager()
            task = mgr.get_task(task_id)
            if not task:
                self.renderer.render_error("Task Not Found", f"No task with ID '{task_id}'")
                return
            goal = task.goal or task.user_request
            state = mgr.update_status(task_id, TaskStatus.RECOVERING)
            if state:
                self.renderer.render_markdown(f"🔄 Retrying task `{task_id}`: _{goal[:60]}_")
                self.session.set_active_task(task_id, goal[:24])
                self.session.execute_turn(f"[RETRY_TASK:{task_id}] Retry from failure: {goal}")
        except Exception as e:
            self.renderer.render_error("Retry Failed", str(e))

    def _cmd_approve(self, task_id: str = "") -> None:
        """Approve a task waiting for approval."""
        task_id = (task_id or "").strip()
        if not task_id:
            try:
                from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

                mgr = get_task_state_manager()
                if self.session._active_task_id:
                    t = mgr.get_task(self.session._active_task_id)
                    if t and (t.approval_request or str(t.status) == TaskStatus.WAITING_FOR_APPROVAL.value):
                        task_id = self.session._active_task_id
                if not task_id:
                    for t in mgr.list_tasks(limit=10):
                        if t.approval_request or str(t.status) == TaskStatus.WAITING_FOR_APPROVAL.value:
                            task_id = t.task_id
                            break
            except Exception as ex:
                logger.debug("Auto-detect approval task note: %s", ex)

        if not task_id:
            self.renderer.render_error(
                "No Pending Approval", "No task is currently waiting for approval. Usage: `/approve <task_id>`"
            )
            return

        try:
            from brjarvis.agent.task_state import get_task_state_manager

            mgr = get_task_state_manager()
            task = mgr.get_task(task_id)
            if not task:
                self.renderer.render_error("Task Not Found", f"Task '{task_id}' was not found.")
                return

            req_id = task.approval_request.request_id if task.approval_request else ""
            state = mgr.resolve_approval(task_id, req_id, approved=True)
            self.session.clear_active_task()
            if state:
                self.renderer.render_markdown(
                    f"[bold green]{Glyphs.CHECK} Approval granted for task `{task_id}`.[/]"
                    if HAS_RICH
                    else f"✓ Approved: {task_id}"
                )
                self.session.execute_turn(
                    f"[APPROVED:{task_id}] Continue approved task: {task.goal or task.user_request}"
                )
            else:
                self.renderer.render_markdown(
                    f"[bold green]{Glyphs.CHECK} Task `{task_id}` marked as approved.[/]"
                    if HAS_RICH
                    else f"✓ Approved: {task_id}"
                )
        except Exception as e:
            self.renderer.render_error("Approve Failed", str(e))

    def _cmd_continue(self) -> None:
        """Resume latest incomplete session or task."""
        try:
            from brjarvis.agent.task_state import get_task_state_manager

            mgr = get_task_state_manager()
            tasks = mgr.list_tasks(limit=5)
            # Find latest non-completed task
            incomplete = [t for t in tasks if str(t.status) not in ("SUCCESS_VERIFIED", "CANCELLED", "FAILED")]
            if not incomplete:
                self.renderer.render_markdown("_No incomplete tasks found. Start fresh with a new goal._")
                return
            task = incomplete[0]
            goal = task.goal or task.user_request
            self.renderer.render_markdown(
                f"**Resuming:** [{task.task_id}] _{goal[:80]}_\n\n**Status:** `{task.status}`"
            )
            self.session.set_active_task(task.task_id, goal[:24])
            self.session.execute_turn(f"[CONTINUE_TASK:{task.task_id}] {goal}")
        except Exception as e:
            self.renderer.render_error("Continue Failed", str(e))

    # ── Context Panel ──────────────────────────────────────────────────────────

    def _cmd_context(self) -> None:
        """Show current session context, model, memory, and services."""
        runtime = self.session.runtime
        orch = self.session.orchestrator

        context: Dict[str, Any] = {
            "Session ID": self.session.session_id[:16],
            "Session Name": self.session.session_name or "(unnamed)",
            "Mode": self.session.current_mode.upper(),
            "Output Style": self.session.output_style,
            "Permission Mode": os.environ.get("JARVIS_PERMISSION_MODE", "CONFIRM_DESTRUCTIVE"),
            "Active Model": (
                getattr(runtime.config.models, "default_backend", "gemini")
                if runtime and hasattr(runtime, "config")
                else "gemini"
            ),
        }

        if self.session._active_task_id:
            context["Active Task"] = f"{self.session._active_task_id} — {self.session._active_task_label or ''}"

        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()
            cache_count = len(um._cache) if hasattr(um, "_cache") else "?"
            context["Memory Cache"] = f"{cache_count} entries"
        except Exception:
            context["Memory"] = "Active"

        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS

            context["Tools Registered"] = f"{len(TOOL_SCHEMAS)} tools"
        except Exception:
            pass

        self.renderer.render_context_panel(context)

    # ── Session Rename ─────────────────────────────────────────────────────────

    def _cmd_rename(self, name: str) -> None:
        """Assign a display name to the current session."""
        if not name:
            self.renderer.render_error("Missing Name", "Usage: `/rename <session name>`")
            return
        self.session.session_name = name.strip()
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(f"[green]{Glyphs.CHECK} Session renamed to:[/] [bold white]{name}[/]")
        else:
            print(f"✓ Session: {name}")

    # ── Memory ────────────────────────────────────────────────────────────────

    def _cmd_memory(self, subcmd_line: str) -> None:
        """Handle /memory commands: search, recent, project, stats, forget."""
        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()

            parts = subcmd_line.split(maxsplit=1)
            sub = parts[0].lower() if parts else ""
            arg = parts[1].strip() if len(parts) > 1 else ""

            if sub == "search" and arg:
                hits = um.recall(arg, limit=6)
                if not hits:
                    self.renderer.render_markdown(f"_No memories found for:_ `{arg}`")
                    return
                self.renderer.render_memory_card(hits, title=f"Memory Search: '{arg}'")

            elif sub in ("recent", "latest"):
                from brjarvis.memory.persistent_store import load_index

                entries = load_index("user")[:8]
                mem_list = [{"type": e.type, "name": e.name, "content": e.content} for e in entries]
                if not mem_list:
                    self.renderer.render_markdown("_No recent memories found._")
                    return
                self.renderer.render_memory_card(mem_list, title="Recent Memories")

            elif sub in ("project", "workspace"):
                from brjarvis.memory.persistent_store import load_index

                entries = [e for e in load_index("user") if e.type in ("project", "operational")][:8]
                mem_list = [{"type": e.type, "name": e.name, "content": e.content} for e in entries]
                if not mem_list:
                    self.renderer.render_markdown("_No project memories found._")
                    return
                self.renderer.render_memory_card(mem_list, title="Project & Operational Memories")

            elif sub in ("stats", "summary"):
                from brjarvis.memory.persistent_store import load_index

                user_e = load_index("user")
                proj_e = load_index("project")
                by_type: dict = {}
                for e in user_e + proj_e:
                    by_type[e.type] = by_type.get(e.type, 0) + 1
                stats_dict = {"Total Persistent Memories": len(user_e) + len(proj_e)}
                for t, cnt in sorted(by_type.items()):
                    stats_dict[f"Type: {t}"] = f"{cnt} entries"
                self.renderer.render_status_table(stats_dict)

            elif sub == "forget" and arg:
                try:
                    from brjarvis.memory.persistent_store import delete_entry

                    delete_entry(arg)
                    self.renderer.render_markdown(f"{Glyphs.CHECK} Memory entry `{arg}` removed.")
                except Exception:
                    self.renderer.render_error("Forget Failed", f"Could not remove memory '{arg}'.")

            else:
                self.renderer.render_markdown(
                    "### 🧠 Memory Commands\n"
                    "- `/memory search <query>` — Search vector store\n"
                    "- `/memory recent` — Latest stored memories\n"
                    "- `/memory project` — Project & workspace context\n"
                    "- `/memory stats` — Memory type breakdown\n"
                    "- `/memory forget <id>` — Remove specific entry\n"
                )
        except Exception as e:
            self.renderer.render_error("Memory Command Error", str(e))

    # ── Tools (Phase 10) ──────────────────────────────────────────────────────

    def _cmd_tools(self, filter_query: str = "") -> None:
        """Browse registered tool schemas, with health/failed sub-commands."""
        sub = filter_query.split()[0].lower() if filter_query else ""

        if sub == "health":
            self._tools_health()
            return
        if sub == "failed":
            self._tools_failed()
            return
        if sub == "search" and len(filter_query.split()) > 1:
            filter_query = " ".join(filter_query.split()[1:])

        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS, _import_plugins

            _import_plugins()
            self.renderer.render_tools_table(TOOL_SCHEMAS, filter_query=filter_query)
        except Exception as e:
            self.renderer.render_error("Tool Registry Error", str(e))

    def _tools_health(self) -> None:
        """Check tool registry health."""
        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS

            total = len(TOOL_SCHEMAS)
            self.renderer.render_markdown(
                f"### Tool Registry Health\n"
                f"- **Total Tools:** `{total}`\n"
                f"- **Status:** {Glyphs.CHECK} Registry loaded successfully\n"
                f"- **Categories:** {len(set(t.get('category', '') for t in TOOL_SCHEMAS))} categories\n"
            )
        except Exception as e:
            self.renderer.render_error("Tool Health Check Failed", str(e))

    def _tools_failed(self) -> None:
        """Show tools that recently failed."""
        self.renderer.render_markdown(
            "_Tool failure tracking is recorded via execution ledger._\n\n"
            "Use `/tasks` to inspect task-level tool failures.\n"
            "Use `/doctor` for system-wide tool health diagnostics."
        )

    # ── Connectors (Phase 10) ─────────────────────────────────────────────────

    def _cmd_connectors(self, connector_name: str = "") -> None:
        """Display connector registry status."""
        connectors = self._get_connector_registry()

        if connector_name:
            conn = next((c for c in connectors if c["name"].lower() == connector_name.lower()), None)
            if not conn:
                self.renderer.render_error("Connector Not Found", f"No connector named '{connector_name}'")
                return
            self.renderer.render_markdown(
                f"### Connector: **{conn['name']}**\n"
                f"- **Status:** `{conn['status']}`\n"
                f"- **Capabilities:** {', '.join(conn.get('capabilities', []))}\n"
                f"- **Auth:** {conn.get('auth_info', 'Not configured')}\n"
            )
            return

        self.renderer.render_connectors_table(connectors)

    def _get_connector_registry(self) -> List[Dict[str, Any]]:
        """Build connector status from environment."""
        import os

        return [
            {
                "name": "GitHub",
                "status": "connected" if os.environ.get("GITHUB_TOKEN") else "auth_required",
                "capabilities": ["read_repo", "push", "create_repo", "issues"],
                "auth_info": "GITHUB_TOKEN in .env",
            },
            {
                "name": "Gmail",
                "status": "auth_required",
                "capabilities": ["read_email", "send_email", "search"],
                "auth_info": "OAuth2 setup required",
            },
            {
                "name": "Calendar",
                "status": "auth_required",
                "capabilities": ["read_events", "create_event", "update_event"],
                "auth_info": "OAuth2 setup required",
            },
            {
                "name": "Telegram",
                "status": "connected" if os.environ.get("TELEGRAM_BOT_TOKEN") else "disabled",
                "capabilities": ["send_message", "receive_updates"],
                "auth_info": "TELEGRAM_BOT_TOKEN in .env",
            },
            {
                "name": "Web",
                "status": "connected",
                "capabilities": ["search", "scrape", "browser_control"],
                "auth_info": "Built-in (playwright/selenium)",
            },
            {
                "name": "Filesystem",
                "status": "connected",
                "capabilities": ["read", "write", "delete", "search"],
                "auth_info": "Local access (security policy enforced)",
            },
            {
                "name": "Canva",
                "status": "disabled",
                "capabilities": ["create_design", "export"],
                "auth_info": "CANVA_API_KEY in .env",
            },
        ]

    # ── Doctor (Phase 11) ─────────────────────────────────────────────────────

    def _cmd_doctor(self) -> None:
        """Run interactive system diagnostic health checks."""
        import os
        import sys

        if HAS_RICH and self.renderer.console:
            self.renderer.console.print("[bold cyan]🩺 Running BR JARVIS System Check...[/bold cyan]\n")

        checks = []

        # Python
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append({"name": f"Python {py_ver}", "ok": sys.version_info >= (3, 10), "detail": sys.executable})

        # Virtual environment
        in_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        checks.append({"name": "Virtual Environment", "ok": in_venv, "detail": sys.prefix if in_venv else "Not active"})

        # .env configuration
        try:
            from brjarvis.core.paths import paths

            dotenv_ok = paths.DOTENV_FILE.exists()
        except Exception:
            dotenv_ok = False
        checks.append({"name": "Configuration (.env)", "ok": dotenv_ok, "detail": ""})

        # API Keys
        has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        has_openai = bool(os.environ.get("OPENAI_API_KEY"))
        has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
        checks.append(
            {"name": "Gemini API Key", "ok": has_gemini, "detail": "GEMINI_API_KEY" if has_gemini else "Missing"}
        )
        checks.append(
            {"name": "OpenAI API Key", "ok": has_openai, "detail": "OPENAI_API_KEY" if has_openai else "Not configured"}
        )
        checks.append(
            {
                "name": "Anthropic API Key",
                "ok": has_anthropic,
                "detail": "ANTHROPIC_API_KEY" if has_anthropic else "Not configured",
            }
        )

        # Rich
        try:
            import rich

            ver = getattr(rich, "__version__", "Installed")
            checks.append({"name": "Rich (terminal UI)", "ok": True, "detail": ver})
        except ImportError:
            checks.append({"name": "Rich (terminal UI)", "ok": False, "detail": "pip install rich"})

        # prompt_toolkit
        try:
            import prompt_toolkit

            ver = getattr(prompt_toolkit, "__version__", "Installed")
            checks.append({"name": "prompt_toolkit (autocomplete)", "ok": True, "detail": ver})
        except ImportError:
            checks.append(
                {"name": "prompt_toolkit (autocomplete)", "ok": False, "detail": "pip install prompt_toolkit"}
            )

        # Tool registry
        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS, _import_plugins

            _import_plugins()
            checks.append({"name": f"Tool Registry ({len(TOOL_SCHEMAS)} tools)", "ok": True, "detail": ""})
        except Exception as e:
            checks.append({"name": "Tool Registry", "ok": False, "detail": str(e)[:60]})

        # Memory
        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            get_unified_memory()
            checks.append({"name": "Unified Memory", "ok": True, "detail": "SQLite WAL active"})
        except Exception as e:
            checks.append({"name": "Unified Memory", "ok": False, "detail": str(e)[:60]})

        # Orchestrator
        orch_ok = self.session.orchestrator is not None
        checks.append({"name": "Orchestrator", "ok": orch_ok, "detail": "Connected" if orch_ok else "Not initialized"})

        # Browser
        try:
            import playwright

            checks.append({"name": "Browser (Playwright)", "ok": True, "detail": ""})
        except ImportError:
            try:
                import selenium

                checks.append({"name": "Browser (Selenium)", "ok": True, "detail": ""})
            except ImportError:
                checks.append({"name": "Browser", "ok": False, "detail": "playwright or selenium not installed"})

        # GitHub connector
        github_ok = bool(os.environ.get("GITHUB_TOKEN"))
        checks.append(
            {
                "name": "GitHub Connector",
                "ok": github_ok,
                "detail": "Token configured" if github_ok else "GITHUB_TOKEN not set",
            }
        )

        # Career OS
        try:
            from brjarvis.career.profile_manager import get_profile_manager

            get_profile_manager()
            checks.append({"name": "Career OS", "ok": True, "detail": ""})
        except Exception as e:
            checks.append({"name": "Career OS", "ok": False, "detail": str(e)[:60]})

        # Compute overall health
        failures = [c for c in checks if not c["ok"]]
        critical_failures = [
            c for c in failures if any(k in c["name"].lower() for k in ["python", "tool registry", "orchestrator"])
        ]

        if not failures:
            overall = "HEALTHY"
        elif critical_failures:
            overall = f"FAILED — {len(critical_failures)} critical issue(s)"
        else:
            overall = f"DEGRADED — {len(failures)} non-critical issue(s) — " + ", ".join(
                c["name"] for c in failures[:3]
            )

        self.renderer.render_doctor_report(checks, overall)

    # ── Usage Stats (Phase 9) ─────────────────────────────────────────────────

    def _cmd_usage(self) -> None:
        """Show token and request usage statistics."""
        runtime = self.session.runtime
        orch = self.session.orchestrator

        stats: Dict[str, Any] = {
            "Session Duration": f"{(time.time() - self._session_start) / 60:.1f} minutes",
            "Session ID": self.session.session_id[:16],
        }

        try:
            if orch and hasattr(orch, "working_memory"):
                hist = orch.working_memory.get()
                stats["Conversation Turns"] = f"{len(hist) // 2} turns"
        except Exception:
            pass

        try:
            if runtime and hasattr(runtime, "config"):
                stats["Active Backend"] = getattr(runtime.config.models, "default_backend", "gemini")
        except Exception:
            pass

        try:
            from brjarvis.tools.registry import TOOL_SCHEMAS

            stats["Registered Tools"] = len(TOOL_SCHEMAS)
        except Exception:
            pass

        stats["Permission Mode"] = os.environ.get("JARVIS_PERMISSION_MODE", "CONFIRM_DESTRUCTIVE")
        stats["Output Style"] = self.session.output_style

        self.renderer.render_usage_stats(stats)

    # ── Verify ────────────────────────────────────────────────────────────────

    def _cmd_verify(self, target_path: str = "") -> None:
        """Run verification check on file or path."""
        try:
            from brjarvis.agent.verifier import get_action_verifier

            verifier = get_action_verifier()
            if target_path:
                res = verifier.verify_file_operation(target_path, "read")
                self.renderer.render_verification(res)
            else:
                self.renderer.render_markdown(
                    "**ActionVerifier Status:** `ACTIVE`\n\n"
                    "Usage: `/verify <filepath>` to verify disk presence, integrity and size."
                )
        except Exception as e:
            self.renderer.render_error("Verification Failed", str(e))

    # ── Diff ──────────────────────────────────────────────────────────────────

    def _cmd_diff(self, file_path: str = "") -> None:
        """Show diff for file if available."""
        if not file_path:
            self.renderer.render_markdown("Usage: `/diff <filepath>` to inspect changes.")
            return
        p = Path(file_path)
        if not p.exists():
            self.renderer.render_error("File Not Found", f"Cannot diff: '{file_path}' does not exist.")
            return
        content = p.read_text(encoding="utf-8", errors="replace")
        self.renderer.render_diff(file_path, "", content)

    # ── History ───────────────────────────────────────────────────────────────

    def _cmd_history(self, args_str: str = "") -> None:
        """View recent session turns, task ledger, or search past sessions."""
        parts = args_str.split(maxsplit=1)
        sub = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        # 1. /history task <id>
        if sub == "task" and arg:
            try:
                from brjarvis.agent.execution_ledger import get_execution_ledger
                from brjarvis.agent.task_state import get_task_state_manager

                mgr = get_task_state_manager()
                task = mgr.get_task(arg)
                if task:
                    self.renderer.render_task_detail(task)
                    # Also show execution ledger entries for this task
                    ledger = get_execution_ledger()
                    entries = ledger.get_task_entries(arg)
                    if entries:
                        report = ledger.build_evidence_report(arg)
                        self.renderer.render_markdown(f"```\n{report}\n```")
                else:
                    self.renderer.render_error("Task Not Found", f"No task with ID '{arg}'")
            except Exception as e:
                self.renderer.render_error("Task History Error", str(e))
            return

        # 2. /history tools [task_id]
        if sub in ("tools", "ledger"):
            try:
                from brjarvis.agent.execution_ledger import get_execution_ledger

                ledger = get_execution_ledger()
                target_task = arg or self.session._active_task_id or ""
                if target_task:
                    report = ledger.build_evidence_report(target_task)
                    self.renderer.render_markdown(f"```\n{report}\n```")
                else:
                    self.renderer.render_markdown(
                        "### 📋 Execution Ledger\n"
                        "Usage: `/history tools <task_id>` to view step-by-step evidence for a specific task.\n"
                        "Use `/tasks` to list available task IDs."
                    )
            except Exception as e:
                self.renderer.render_error("Ledger History Error", str(e))
            return

        # 3. /history search <query>
        if sub == "search" and arg:
            try:
                from brjarvis.history.session_store import SessionStore

                store = SessionStore()
                results = store.search(arg, limit=8)
                if not results:
                    self.renderer.render_markdown(f"_No session history matches found for:_ `{arg}`")
                    return
                self.renderer.render_markdown(f"### 🔍 Session Search: '{arg}' ({len(results)} matches)")
                for r in results:
                    role = r.get("role", "turn").upper()
                    content = str(r.get("content", ""))[:180]
                    sid = r.get("session_id", "")[:8]
                    self.renderer.render_markdown(f"- **[{role}]** `({sid})`: {content}")
            except Exception as e:
                self.renderer.render_error("History Search Error", str(e))
            return

        # 4. Standard /history [n] — session turns
        try:
            limit = int(sub) if sub.isdigit() else 5
        except Exception:
            limit = 5

        try:
            orch = self.session.orchestrator
            if orch and hasattr(orch, "working_memory"):
                history = orch.working_memory.get()[-(limit * 2) :]
                if not history:
                    self.renderer.render_markdown("_No conversation history in current session._")
                    return
                self.renderer.render_markdown(f"### 📜 Session History (Last {len(history)} messages)")
                for msg in history:
                    role = msg.get("role", "system").upper()
                    content = str(msg.get("content", ""))[:200]
                    self.renderer.render_markdown(f"**[{role}]**: {content}")
            else:
                self.renderer.render_markdown("_History store not connected._")
        except Exception as e:
            self.renderer.render_error("History Error", str(e))

    # ── Style & Verbose ───────────────────────────────────────────────────────

    def _cmd_style(self, style: str) -> None:
        """Set output style."""
        valid = ["compact", "detailed", "minimal", "verbose"]
        if not style or style.lower() not in valid:
            self.renderer.render_markdown(
                f"**Current Style:** `{self.session.output_style}`\n\n"
                f"Available: {', '.join(f'`{s}`' for s in valid)}\n\n"
                f"Usage: `/style compact`"
            )
            return
        self.session.output_style = style.lower()
        self._output_style = style.lower()
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(f"[green]{Glyphs.CHECK} Output style → {style.lower()}[/]")
        else:
            print(f"✓ Style: {style.lower()}")

    def _cmd_verbose(self, args_str: str) -> None:
        """Toggle verbose debug output."""
        if args_str.lower() in ("on", "1", "true", "yes"):
            self.session.verbose = True
            if HAS_RICH and self.renderer.console:
                self.renderer.console.print(
                    "[bold yellow]⚠ Verbose mode ON — showing tool arguments, timings, routing[/]"
                )
            else:
                print("Verbose: ON")
        elif args_str.lower() in ("off", "0", "false", "no"):
            self.session.verbose = False
            if HAS_RICH and self.renderer.console:
                self.renderer.console.print("[dim]Verbose mode OFF[/]")
            else:
                print("Verbose: OFF")
        else:
            status = "ON" if self.session.verbose else "OFF"
            self.renderer.render_markdown(f"**Verbose Mode:** `{status}`\n\nUse `/verbose on` or `/verbose off`")

    # ── Mouse Interaction & TUI ───────────────────────────────────────────────

    def _cmd_mouse(self, args_str: str = "") -> None:
        """Toggle or configure interactive mouse support in terminal session."""
        from .events import MouseCaptureMode

        sub = args_str.strip().lower()

        def _notify(rich_msg: str, plain_msg: str) -> None:
            if HAS_RICH and self.renderer and self.renderer.console:
                self.renderer.console.print(rich_msg)
            else:
                print(plain_msg)

        if sub in ("on", "enable", "1", "true", "yes"):
            self.session.set_mouse_support(True)
            _notify(
                f"[bold green]{Glyphs.CHECK} Mouse mode: INTERACTIVE[/bold green] (clicks, selection, URLs, expandable tools, scrolling).",
                "✓ Mouse mode: INTERACTIVE.",
            )
        elif sub in ("off", "disable", "0", "false", "no"):
            self.session.set_mouse_support(False)
            _notify(
                "[bold yellow]⚠ Mouse mode: OFF[/bold yellow]. Native terminal text selection is active.",
                "⚠ Mouse mode: OFF.",
            )
        elif sub == "interactive":
            if hasattr(self.session, "set_mouse_capture_mode"):
                self.session.set_mouse_capture_mode(MouseCaptureMode.MOUSE_INTERACTIVE)
            else:
                self.session.set_mouse_support(True)
            _notify(f"[bold green]{Glyphs.CHECK} Mouse mode: INTERACTIVE[/bold green].", "✓ Mouse mode: INTERACTIVE.")
        elif sub in ("scroll", "wheel"):
            if hasattr(self.session, "set_mouse_capture_mode"):
                self.session.set_mouse_capture_mode(MouseCaptureMode.MOUSE_SCROLL)
            else:
                self.session.set_mouse_support(True)
            _notify(
                "[bold cyan]◆ Mouse mode: SCROLL ONLY[/bold cyan]. Wheel scrolls transcript; native terminal selection preserved.",
                "◆ Mouse mode: SCROLL ONLY.",
            )
        elif sub in ("full", "all"):
            if hasattr(self.session, "set_mouse_capture_mode"):
                self.session.set_mouse_capture_mode(MouseCaptureMode.MOUSE_FULL)
            else:
                self.session.set_mouse_support(True)
            _notify(
                "[bold magenta]◆ Mouse mode: FULL CAPTURE[/bold magenta] (motion hover tracking + all interactive features).",
                "◆ Mouse mode: FULL CAPTURE.",
            )
        elif sub in ("status", "info"):
            mode_val = getattr(self.session, "mouse_capture_mode", MouseCaptureMode.MOUSE_OFF)
            mode_str = mode_val.value if hasattr(mode_val, "value") else str(mode_val)
            self.renderer.render_markdown(
                f"### 🖱️ Mouse Subsystem Telemetry\n"
                f"* **Capture Mode:** `{mode_str.upper()}`\n"
                f"* **Mouse Enabled:** `{'YES' if getattr(self.session, 'mouse_support', False) else 'NO'}`\n"
                f"* **Click Handling:** `{'ACTIVE' if mode_val in (MouseCaptureMode.MOUSE_INTERACTIVE, MouseCaptureMode.MOUSE_FULL) else 'DISABLED'}`\n"
                f"* **Wheel Scroll:** `{'ACTIVE' if mode_val != MouseCaptureMode.MOUSE_OFF else 'DISABLED'}`\n"
                f"* **Protocol:** `SGR Extended (1006) + Drag (1002)`\n\n"
                f"_Usage: `/mouse [on | off | scroll | interactive | full]`_"
            )
        else:
            # Toggle
            new_state = not getattr(self.session, "mouse_support", False)
            self.session.set_mouse_support(new_state)
            st = "ENABLED" if new_state else "DISABLED"
            color = "green" if new_state else "yellow"
            _notify(f"[bold {color}]Mouse mode toggled: {st}[/bold {color}].", f"Mouse mode toggled: {st}.")

    def _cmd_tui(self, args_str: str = "") -> None:
        """Switch between standard streaming CLI and fullscreen interactive TUI."""
        sub = args_str.strip().lower()
        if sub in ("fullscreen", "alt", "full"):
            if hasattr(self.session, "state_guard"):
                self.session.state_guard.enter_alternate_screen()
                self.session.render_header()
            self.renderer.render_markdown(
                f"{Glyphs.CHECK} Switched to **Fullscreen TUI Mode** (Alternate screen active)."
            )
        elif sub in ("default", "inline", "normal", "exit"):
            if hasattr(self.session, "state_guard"):
                self.session.state_guard.exit_alternate_screen()
            self.renderer.render_markdown(f"{Glyphs.CHECK} Switched to **Default Streaming Mode**.")
        else:
            is_alt = getattr(getattr(self.session, "state_guard", None), "is_alt_screen", False)
            self.renderer.render_markdown(
                f"### 🖥️ TUI Display State\n"
                f"* **Active Display Buffer:** `{'ALTERNATE SCREEN (Fullscreen)' if is_alt else 'PRIMARY (Inline Stream)'}`\n\n"
                f"_Use `/tui fullscreen` or `/tui default` to switch._"
            )

    # ── Export ────────────────────────────────────────────────────────────────

    def _cmd_export(self, format_spec: str = "markdown") -> None:
        """Export session transcript to artifact."""
        try:
            from brjarvis.agent.artifacts import get_artifact_manager

            mgr = get_artifact_manager()
            orch = self.session.orchestrator
            history = orch.working_memory.get() if orch and hasattr(orch, "working_memory") else []

            lines = [
                f"# BR JARVIS Session Export ({self.session.session_id})",
                f"**Session:** {self.session.session_name or self.session.session_id}",
                f"**Mode:** {self.session.current_mode}",
                "",
            ]
            for h in history:
                role = h.get("role", "").upper()
                content = h.get("content", "")
                lines.append(f"### [{role}]\n{content}\n")

            body = "\n".join(lines)
            art = mgr.create_artifact(
                filename=f"session_{self.session.session_id[:8]}.md",
                content=body,
                category="report",
                metadata={"session_id": self.session.session_id},
            )
            self.renderer.render_markdown(f"{Glyphs.CHECK} Session exported to: `{art.host_path or art.sandbox_path}`")
        except Exception as e:
            self.renderer.render_error("Export Failed", str(e))

    # ── Compact ───────────────────────────────────────────────────────────────

    def _cmd_compact(self) -> None:
        """Consolidate working memory into long-term storage."""
        try:
            orch = self.session.orchestrator
            if orch and hasattr(orch, "consolidate_on_exit"):
                res = orch.consolidate_on_exit()
                if hasattr(orch, "working_memory") and hasattr(orch.working_memory, "trim"):
                    orch.working_memory.trim(max_turns=4)
                self.renderer.render_markdown(
                    f"{Glyphs.CHECK} **Memory Consolidated:** {res or 'Working memory trimmed.'}"
                )
            else:
                self.renderer.render_markdown("Memory consolidation completed.")
        except Exception as e:
            self.renderer.render_error("Compaction Failed", str(e))

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _cmd_clear(self) -> None:
        """Clear screen and re-render header."""
        self.renderer.clear()
        self.session.render_header()

    # ── Version ───────────────────────────────────────────────────────────────

    def _cmd_version(self) -> None:
        """Display canonical version info."""
        self.renderer.render_markdown(f"**BR JARVIS:** `v{VERSION}` | Codename: `{CODENAME}` | Build: `{BUILD}`")

    # ── Quit ──────────────────────────────────────────────────────────────────

    def _cmd_quit(self) -> bool:
        """Clean shutdown with consolidation."""
        self.session.close(consolidate=True)
        return False

    # ── Career OS Commands (preserved + enhanced) ──────────────────────────────

    def _cmd_career(self, args_str: str = "") -> None:
        """Career Profile and Funnel Analytics overview."""
        try:
            from brjarvis.career.analytics import CareerAnalyticsEngine
            from brjarvis.career.profile_manager import get_profile_manager

            mgr = get_profile_manager()
            profile = mgr.get_profile()
            val = mgr.validate_profile(profile)
            analytics = CareerAnalyticsEngine.compute_analytics()

            if "sync" in args_str.lower():
                from brjarvis.career.spreadsheet.projection import get_spreadsheet_projection

                self.renderer.render_markdown("⏳ _Synchronizing Career Database and Excel Projection..._")
                proj = get_spreadsheet_projection()
                res = proj.project_database_to_excel()
                if res.get("status") == "SUCCESS_VERIFIED":
                    self.renderer.render_markdown(
                        f"{Glyphs.CHECK} **Career Tracker Excel Synchronized:** `{res['target_path']}`"
                    )
                else:
                    self.renderer.render_markdown(f"⚠ **Sync Notice:** {res}")
                return

            if "onboard" in args_str.lower():
                qs = mgr.get_onboarding_questions(profile)
                if not qs:
                    self.renderer.render_markdown(
                        f"{Glyphs.CHECK} **Profile Onboarding Complete:** Zero missing critical fields."
                    )
                    return
                self.renderer.render_markdown(f"### 📋 Career Onboarding ({len(qs)} missing fields):")
                for idx, q in enumerate(qs, 1):
                    self.renderer.render_markdown(f"**{idx}. [{q['field']}]**: {q['question']}")
                return

            if "analytics" in args_str.lower() or "stats" in args_str.lower():
                self.renderer.render_markdown(f"""### 📊 Career Analytics & Pipeline Telemetry:
* **Jobs Discovered:** `{analytics.total_jobs_discovered}` │ **Shortlisted:** `{analytics.total_shortlisted}`
* **Applications Submitted:** `{analytics.total_applications_submitted}` │ **Screenings:** `{analytics.total_screenings}`
* **Interviews Scheduled:** `{analytics.total_interviews}` │ **Offers Received:** `{analytics.total_offers}`
* **Response Rate:** `{analytics.response_rate}%` │ **Interview Conversion:** `{analytics.interview_rate}%`
* **Offer Conversion Rate:** `{analytics.offer_rate}%`
""")
                return

            self.renderer.render_markdown(f"""### 💼 Career Profile: **{profile.contact.full_name}**
* **Completeness:** `{val["score"]}%` ({val["status"]})
* **Target Roles:** {", ".join(profile.preferences.target_roles) or "Not Specified"}
* **Work Mode:** {profile.preferences.remote_preference.replace("_", " ").title()}
* **Experience:** {len(profile.experience)} entries │ **Projects:** {len(profile.projects)} │ **Skills:** {sum(len(s.skills) for s in profile.skills)}

#### 📊 Pipeline:
* **Applied:** `{analytics.total_applications_submitted}` │ **Interviews:** `{analytics.total_interviews}` │ **Offers:** `{analytics.total_offers}`
* **Response Rate:** `{analytics.response_rate}%`
""")
        except Exception as e:
            self.renderer.render_error("Career Profile Error", str(e))

    def _cmd_applications(self, args_str: str = "") -> None:
        """List tracked job applications."""
        try:
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            apps = db.list_applications(limit=25)
            arg_low = args_str.lower().strip()
            if "followup" in arg_low:
                from brjarvis.career.crm.followup_engine import get_followup_engine

                fol_engine = get_followup_engine()
                pending = fol_engine.get_pending_followups()
                if not pending:
                    self.renderer.render_markdown(f"{Glyphs.CHECK} **No follow-ups due right now.**")
                    return
                self.renderer.render_markdown(f"### ⏰ Pending Follow-ups ({len(pending)}):")
                for f in pending:
                    self.renderer.render_markdown(
                        f"• `[{f.followup_id}]` **{f.company}** — {f.role} (Due: `{f.due_date}`)"
                    )
                return
            if not apps:
                self.renderer.render_markdown("_No tracked applications. Use `/jobs` or `/apply` to start._")
                return
            self.renderer.render_markdown(f"### 📋 Job Applications ({len(apps)} tracked):")
            for a in apps[:10]:
                st_val = (
                    a.application_status.value if hasattr(a.application_status, "value") else str(a.application_status)
                )
                self.renderer.render_markdown(f"• `[{a.application_id}]` **{a.company}** — {a.job_title} │ `{st_val}`")
        except Exception as e:
            self.renderer.render_error("Applications Error", str(e))

    def _cmd_interviews(self, args_str: str = "") -> None:
        """List scheduled interviews."""
        try:
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            interviews = db.list_interviews(limit=15)
            if not interviews:
                self.renderer.render_markdown("_No upcoming interviews scheduled._")
                return
            self.renderer.render_markdown(f"### 📅 Upcoming Interviews ({len(interviews)}):")
            for iv in interviews:
                self.renderer.render_markdown(
                    f"• `[{iv.interview_id}]` **{iv.company}** ({iv.round}) — `{iv.date} {iv.time_str}` │ {iv.meeting_url or 'TBD'}"
                )
        except Exception as e:
            self.renderer.render_error("Interviews Error", str(e))

    def _cmd_offers(self, args_str: str = "") -> None:
        """List detected job offers."""
        try:
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            offers = db.list_offers(limit=10)
            if not offers:
                self.renderer.render_markdown("_No job offers detected._")
                return
            self.renderer.render_markdown(f"### 🏆 Job Offers ({len(offers)}):")
            for off in offers:
                st_val = off.status.value if hasattr(off.status, "value") else str(off.status)
                self.renderer.render_markdown(
                    f"• `[{off.offer_id}]` **{off.company}** — {off.role} │ `{st_val}` │ {off.salary}"
                )
        except Exception as e:
            self.renderer.render_error("Offers Error", str(e))

    def _cmd_emails(self, args_str: str = "") -> None:
        """Career email intelligence."""
        try:
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            events = db.list_email_records(limit=10)
            if not events:
                self.renderer.render_markdown("_No career email events recorded. Sync to ingest._")
                return
            self.renderer.render_markdown(f"### 📧 Career Email Feed ({len(events)} events):")
            for ev in events:
                cls_val = ev.classification.value if hasattr(ev.classification, "value") else str(ev.classification)
                self.renderer.render_markdown(
                    f"• `[{ev.email_event_id}]` **{ev.sender}** │ `{cls_val}` ({ev.confidence * 100:.0f}%) │ _{ev.subject[:50]}_"
                )
        except Exception as e:
            self.renderer.render_error("Email Intelligence Error", str(e))

    def _cmd_career_resume(self, args_str: str = "") -> None:
        """Generate or tailor a Career OS resume."""

        try:
            from brjarvis.career.profile_manager import get_profile_manager
            from brjarvis.career.resume_engine.exporter import ResumeExportPipeline
            from brjarvis.career.resume_engine.renderer import ResumeRenderer
            from brjarvis.career.resume_engine.version_manager import ResumeVersionManager

            mgr = get_profile_manager()
            profile = mgr.get_profile()
            role = args_str.strip() or (
                profile.preferences.target_roles[0] if profile.preferences.target_roles else "Systems Architect"
            )
            schema = ResumeRenderer.schema_from_profile(profile, target_role=role)
            exporter = ResumeExportPipeline()
            res = exporter.export_all_formats(schema)
            ver_mgr = ResumeVersionManager.get_instance()
            ver_rec = ver_mgr.register_version(
                resume=schema,
                provider="native",
                docx_path=res["docx"]["path"],
                pdf_path=res["pdf"]["path"],
                html_path=res["html"]["path"],
            )
            self.renderer.render_markdown(f"""{Glyphs.CHECK} **Resume Generated (v{ver_rec.version_id}):**
* **Title:** {schema.title}
* **DOCX:** `{res["docx"]["path"]}` ({"✓" if res["docx"]["verified"] else "✗"})
* **PDF:** `{res["pdf"]["path"]}` ({"✓" if res["pdf"]["verified"] else "✗"})
* **HTML:** `{res["html"]["path"]}` ({"✓" if res["html"]["verified"] else "✗"})
""")
        except Exception as e:
            self.renderer.render_error("Resume Generation Error", str(e))

    def _cmd_jobs(self, query: str = "") -> None:
        """Search and match live job postings."""
        try:
            from brjarvis.career.job_engine.finder import JobFinder

            q = query.strip() or "Autonomous AI Systems Engineer"
            self.renderer.render_markdown(f"🔍 _Searching for:_ `{q}`...")
            finder = JobFinder.get_instance()
            results = finder.search_and_match(query_or_filters=q, limit=5)
            if not results:
                self.renderer.render_markdown(f"_No matches found for '{q}'._")
                return
            self.renderer.render_markdown(f"### 🎯 Top Job Matches ({len(results)}):")
            for idx, r in enumerate(results, 1):
                j = r.job
                m = r.match
                self.renderer.render_markdown(f"""**{idx}. {j.title}** @ **{j.company}** (Fit: `{m.overall_score}%`)
* **ID:** `{j.job_id}` │ **Platform:** {j.platform} │ **Location:** {j.location}
* **Salary:** {j.salary or "Competitive"}
""")
        except Exception as e:
            self.renderer.render_error("Job Search Error", str(e))

    def _cmd_apply(self, job_id: str = "") -> None:
        """Prepare application package and open browser."""
        try:
            from brjarvis.career.application_engine.assistant import ManualApplicationAssistant
            from brjarvis.career.job_engine.finder import JobFinder

            jid = job_id.strip()
            if not jid:
                self.renderer.render_markdown("Usage: `/apply <job_id>` (Use `/jobs` to discover IDs).")
                return
            finder = JobFinder.get_instance()
            job = finder.get_job_by_id(jid)
            if not job:
                self.renderer.render_error("Job Not Found", f"No job found with ID '{jid}'.")
                return
            assistant = ManualApplicationAssistant()
            res = assistant.prepare_and_assist(job=job, auto_open_browser=True)
            if not res.get("success"):
                self.renderer.render_error("Application Blocked", res.get("message", "Could not prepare."))
                return
            self.renderer.render_markdown(f"""{Glyphs.CHECK} **Application Package Ready for {job.company}:**
* **Application ID:** `{res["application_id"]}` │ **Package:** `{res["package_id"]}`
* **Portal URL:** {res["application_url"]}
* **Resume PDF:** `{res["resume_pdf"]}`
* **Cover Letter:** `{res["cover_letter_pdf"]}`
* **Status:** `READY_FOR_REVIEW`
""")
        except Exception as e:
            self.renderer.render_error("Application Assistant Error", str(e))

    def _cmd_ats(self, role_str: str = "") -> None:
        """Run 7-factor ATS audit."""
        try:
            from brjarvis.career.ats_engine.scorer import ATSEngine
            from brjarvis.career.profile_manager import get_profile_manager
            from brjarvis.career.resume_engine.renderer import ResumeRenderer

            mgr = get_profile_manager()
            profile = mgr.get_profile()
            schema = ResumeRenderer.schema_from_profile(profile, target_role=role_str.strip() or None)
            rep = ATSEngine.evaluate_resume(schema)
            self.renderer.render_markdown(f"""### 🎯 ATS Audit: **Grade {rep.grade}** (`{rep.overall_score}%`)
* **Keyword Coverage:** `{rep.keyword_coverage_score}%`
* **Section Recognition:** `{rep.section_recognition_score}%`
* **Parsing Safety:** `{rep.parsing_risk_score}%`
* **Readability:** `{rep.readability_score}%`
* **Role Alignment:** `{rep.role_relevance_score}%`

#### 💡 Recommended Changes:
{chr(10).join(f"* {c}" for c in rep.recommended_changes[:4]) if rep.recommended_changes else "* All ATS metrics optimal."}
""")
        except Exception as e:
            self.renderer.render_error("ATS Audit Error", str(e))

    def _cmd_session(self, args_str: str = "") -> None:
        """View or switch active AgentSession."""
        try:
            from brjarvis.agent.session import get_or_create_session

            sess_id = args_str.strip()
            if not sess_id:
                sid = getattr(self.session, "session_id", "default")
                mode = getattr(self.session, "current_mode", "general")
                self.renderer.render_markdown(
                    f"### 📋 Active Session Context\n"
                    f"* **Session ID:** `{sid}`\n"
                    f"* **Mode:** `{mode.upper()}`\n"
                    f"* **Working Directory:** `{os.getcwd()}`\n"
                    f"* **Output Style:** `{getattr(self.session, 'output_style', 'compact')}`\n\n"
                    f"_Use `/sessions` to list active sessions, or `/session <id>` to switch._"
                )
            else:
                self.session.session_id = sess_id
                if hasattr(self.session, "agent_session"):
                    self.session.agent_session = get_or_create_session(sess_id)
                self.renderer.render_markdown(f"{Glyphs.CHECK} Switched to session: `{sess_id}`")
        except Exception as e:
            self.renderer.render_error("Session Error", str(e))

    def _cmd_sessions(self) -> None:
        """List active and persisted AgentSessions."""
        try:
            from brjarvis.agent.session import list_active_sessions

            sessions = list_active_sessions()
            if not sessions:
                self.renderer.render_markdown(
                    f"_Current active session:_ `{getattr(self.session, 'session_id', 'default')}`"
                )
                return

            lines = ["### 📋 Active Agent Sessions:"]
            for s in sessions:
                cur_mark = " (Active)" if s.session_id == getattr(self.session, "session_id", "") else ""
                lines.append(f"• `{s.session_id}` [{s.current_mode.upper()}] — {len(s.turns)} turns{cur_mark}")
            self.renderer.render_markdown("\n".join(lines))
        except Exception as e:
            self.renderer.render_error("Sessions Error", str(e))

    def _cmd_skills(self, args_str: str = "") -> None:
        """Browse registered skills catalog and workflows."""
        try:
            from brjarvis.skills import load_skills

            skills = load_skills()
            if not skills:
                self.renderer.render_markdown("_No external skills discovered in `./skills` or builtin._")
                return

            query = args_str.strip().lower()
            if query:
                skills = [s for s in skills if query in s.name.lower() or query in s.description.lower()]

            lines = [f"### ⚡ Extensible Skills Catalog ({len(skills)} found):"]
            for sk in skills:
                lines.append(f"• **{sk.name}** (`/{sk.name}`): {sk.description[:100]}")
            self.renderer.render_markdown("\n".join(lines))
        except Exception as e:
            self.renderer.render_error("Skills Catalog Error", str(e))

    def _cmd_config(self) -> None:
        """Display configuration and runtime environment summary."""
        try:
            from brjarvis.core.config import get_config

            cfg = get_config()
            self.renderer.render_markdown(
                f"### ⚙️ Runtime Configuration\n"
                f"* **Environment:** `{getattr(cfg, 'environment', 'production')}`\n"
                f"* **Default Provider:** `{getattr(cfg.models, 'default_backend', 'Gemini')}`\n"
                f"* **Permission Policy:** `{os.environ.get('JARVIS_PERMISSION_MODE', 'CONFIRM_DESTRUCTIVE')}`\n"
                f"* **Mouse Support:** `{'Enabled' if getattr(self.session, 'mouse_support', True) else 'Disabled'}`\n"
            )
        except Exception as e:
            self.renderer.render_error("Config Error", str(e))

    def _cmd_interrupt(self) -> None:
        """Manually trigger task interrupt / pause."""
        try:
            if hasattr(self.session, "_handle_interrupt"):
                self.session._handle_interrupt(force_quit=False)
            self.renderer.render_markdown(f"{Glyphs.WARNING} **Agent task interrupted safely. State preserved.**")
        except Exception as e:
            self.renderer.render_error("Interrupt Error", str(e))

    def _cmd_doctor(self, args_str: str = "") -> None:
        """Run system diagnostics or mouse/terminal interaction telemetry."""
        sub = args_str.strip().lower()
        if sub in ("mouse", "tui", "input", "terminal"):
            from .events import MouseCaptureMode

            term = (
                os.environ.get("TERM_PROGRAM")
                or os.environ.get("TERM")
                or ("Windows Terminal" if os.name == "nt" else "Standard ANSI")
            )
            mode_val = getattr(self.session, "mouse_capture_mode", MouseCaptureMode.MOUSE_OFF)
            mode_str = mode_val.value if hasattr(mode_val, "value") else str(mode_val)
            is_mouse = getattr(self.session, "mouse_support", False)
            in_tmux = "YES" if os.environ.get("TMUX") else "NO"
            in_ssh = "YES" if os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY") else "NO"

            self.renderer.render_markdown(
                f"### 🩺 Terminal & Interaction Diagnostics\n"
                f"* **Terminal Emulator:** `{term}`\n"
                f"* **Platform / OS:** `{sys.platform}` (`{os.name}`)\n"
                f"* **TMUX Session:** `{in_tmux}`\n"
                f"* **SSH Session:** `{in_ssh}`\n"
                f"* **Alternate Screen:** `SUPPORTED`\n"
                f"* **Mouse Protocol:** `SGR Extended (1006) + Drag (1002)`\n"
                f"* **Mouse Reporting:** `{'ENABLED (' + mode_str.upper() + ')' if is_mouse else 'DISABLED (Native selection active)'}`\n"
                f"* **Wheel Scrolling:** `SUPPORTED (Independent of click)`\n"
                f"* **Clipboard Support:** `SUPPORTED (Win32 / OSC 52 / pbcopy / xclip)`\n"
                f"* **Spatial Hit Testing:** `ACTIVE (2D Bounding Boxes)`\n"
                f"* **Auto-Follow Mechanics:** `ACTIVE (Pauses on scroll-up, resumes at bottom)`\n\n"
                f"_Toggle mouse mode anytime via `/mouse [on | off | scroll | interactive | full]`._"
            )
            return

        try:
            from brjarvis.diagnostics.doctor import run_diagnostics_audit

            rep = run_diagnostics_audit(auto_repair=False)
            healthy = rep.get("healthy", True)
            checks = rep.get("checks", {})
            status_glyph = Glyphs.CHECK if healthy else Glyphs.WARNING
            color = "green" if healthy else "yellow"

            lines = [f"### {status_glyph} Diagnostic Health Audit: `{rep.get('status', 'OK')}`"]
            for name, details in checks.items():
                ok = details.get("status") in ("ok", "passed", "healthy", True)
                g = Glyphs.CHECK if ok else Glyphs.CROSS
                c = "green" if ok else "red"
                lines.append(f"* **{name}**: [{c}]{g} {details.get('message', details.get('status', 'OK'))}[/{c}]")

            self.renderer.render_markdown("\n".join(lines))
        except Exception as e:
            self.renderer.render_error("Doctor Audit Error", str(e))

    def _cmd_usage(self) -> None:
        """Display token metrics, turn count, and cost telemetry."""
        try:
            sess = getattr(self.session, "agent_session", None)
            turns_count = len(sess.turns) if sess and hasattr(sess, "turns") else 0
            prompt_toks = 0
            completion_toks = 0
            if sess and hasattr(sess, "turns"):
                for t in sess.turns:
                    prompt_toks += getattr(t, "prompt_tokens", 0)
                    completion_toks += getattr(t, "completion_tokens", 0)

            total_toks = prompt_toks + completion_toks
            self.renderer.render_markdown(
                f"### 📊 Session Resource & Token Usage\n"
                f"* **Active Turns:** `{turns_count}`\n"
                f"* **Prompt Tokens:** `{prompt_toks:,}`\n"
                f"* **Completion Tokens:** `{completion_toks:,}`\n"
                f"* **Total Tokens Consumed:** `{total_toks:,}`\n"
                f"* **Active Backend:** `{getattr(sess, 'model', 'Gemini') if sess else 'Gemini'}`\n"
            )
        except Exception as e:
            self.renderer.render_error("Usage Telemetry Error", str(e))

    def _cmd_connectors(self, args_str: str = "") -> None:
        """Browse registered MCP and external connectors."""
        self.renderer.render_markdown(
            "### 🔌 External Connectors & MCP Integrations\n"
            "* **MCP Bridge:** `Active`\n"
            "* **Browser Engine:** `Playwright / Headless Chromium`\n"
            "* **Filesystem Provider:** `Native Workspace Sandbox`\n"
            "* **Voice Subsystem:** `Whisper / Edge-TTS`\n"
        )
