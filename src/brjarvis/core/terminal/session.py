# core/terminal/session.py — Premium Interactive Agent Terminal Session for BR JARVIS MK41
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
import uuid
from typing import Any, Optional

from brjarvis.agent.agent_loop import AgentLoop
from brjarvis.agent.session import AgentSession, get_or_create_session
from brjarvis.security.permission_request import PermissionDecision, PermissionRequest

from ..runtime import ApplicationRuntime, get_runtime
from .commands import VALID_MODES, SlashCommandHandler
from .components import PermissionPromptComponent
from .events import MouseCaptureMode
from .guard import TerminalStateGuard
from .interactive_tui import InteractiveTUIController
from .renderer import TerminalRenderer
from .theme import (
    COLOR_AMBER,
    COLOR_CYAN,
    MODE_COLORS,
    Glyphs,
)

# ── autocomplete / prompt engine ─────────────────────────────────────────────
try:
    from .autocomplete import (
        HAS_PROMPT_TOOLKIT,
        build_prompt_session,
        get_history_path,
    )
except Exception:
    HAS_PROMPT_TOOLKIT = False

    def build_prompt_session(**_: Any) -> None:
        return None

    def get_history_path() -> None:
        return None

try:
    
    
    from rich.prompt import Prompt
    

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger("JARVIS.TerminalSession")

# ── Prompt context states ─────────────────────────────────────────────────────
PROMPT_NORMAL = "normal"
PROMPT_TASK = "task"
PROMPT_APPROVAL = "approval"
PROMPT_NEEDS_INPUT = "needs_input"


class TerminalSession:
    """Master CLI Terminal Session Controller for BR JARVIS MK41.

    Manages user interaction, REPL lifecycle, live streaming execution,
    plan mode with approval gate, permission prompts, task control,
    tool call visualization, autocomplete, and event telemetry.
    """

    def __init__(
        self,
        runtime: Optional[ApplicationRuntime] = None,
        *,
        mode: str = "general",
        session_id: Optional[str] = None,
        auto_welcome: bool = True,
    ):
        # ── Runtime initialization (graceful degradation) ─────────────────
        try:
            self.runtime: ApplicationRuntime = runtime or get_runtime()
            self.orchestrator = self.runtime.orchestrator
        except Exception as e:
            logger.warning("Runtime init degraded: %s — running in offline mode", e)
            self.runtime = None  # type: ignore
            self.orchestrator = None

        self.renderer: TerminalRenderer = TerminalRenderer()
        self.commands: SlashCommandHandler = SlashCommandHandler(self)

        self.session_id: str = session_id or str(uuid.uuid4())
        if self.orchestrator:
            self.session_id = getattr(self.orchestrator, "session_id", self.session_id)

        self.current_mode: str = mode if mode in VALID_MODES else "general"
        self.session_name: str = ""  # user-assigned session label
        self.output_style: str = "compact"  # compact | detailed | minimal | verbose
        self.verbose: bool = False

        if self.orchestrator:
            self.orchestrator.current_mode = self.current_mode

        self._closed: bool = False
        self.auto_welcome: bool = auto_welcome
        self._is_running: bool = False
        self._interrupt_count: int = 0  # Ctrl+C double-tap counter
        self._last_interrupt: float = 0.0
        self._active_task_id: Optional[str] = None
        self._active_task_label: Optional[str] = None
        self._prompt_state: str = PROMPT_NORMAL

        # ── Terminal State Guard & Mouse Controller ───────────────────────
        self.state_guard: TerminalStateGuard = TerminalStateGuard.get_instance()
        self.state_guard.register_emergency_cleanup()

        env_mouse = os.environ.get("JARVIS_MOUSE_SUPPORT", "0").strip().lower()
        self.mouse_support: bool = env_mouse in ("1", "true", "yes", "on", "enable", "enabled")
        self.mouse_capture_mode: MouseCaptureMode = (
            MouseCaptureMode.MOUSE_INTERACTIVE if self.mouse_support else MouseCaptureMode.MOUSE_OFF
        )
        self.tui: InteractiveTUIController = InteractiveTUIController(
            console=self.renderer.console,
            mouse_mode=self.mouse_capture_mode,
        )

        # ── Canonical AgentSession & AgentLoop ───────────────────────────
        self.agent_session: AgentSession = get_or_create_session(
            session_id=self.session_id,
            mode=self.current_mode,
            model=(
                getattr(self.runtime.config.models, "default_backend", "Gemini")
                if self.runtime and hasattr(self.runtime, "config")
                else "Gemini"
            ),
        )
        self.agent_loop: AgentLoop = AgentLoop(
            session=self.agent_session,
            gateway=self.runtime.gateway if self.runtime else None,
        )

        self.agent_loop.permission_mgr.set_interactive_resolver(self.prompt_permission)

        # ── prompt_toolkit session (with history + autocomplete) ──────────
        self._pt_session: Any = None
        if HAS_PROMPT_TOOLKIT:
            try:
                self._pt_session = build_prompt_session(mouse_support=self.mouse_support)
            except Exception as e:
                logger.debug("prompt_toolkit session init failed: %s", e)

        # Only activate mouse capture if explicitly requested
        if self.mouse_support:
            try:
                self.state_guard.enable_mouse_capture(self.mouse_capture_mode)
            except Exception as e:
                logger.debug("Initial mouse capture setup note: %s", e)

        self._setup_event_listeners()

    def set_mouse_capture_mode(self, mode: MouseCaptureMode) -> None:
        """Set explicit mouse capture mode (off, scroll, interactive, full)."""
        self.mouse_capture_mode = mode
        self.mouse_support = mode != MouseCaptureMode.MOUSE_OFF
        os.environ["JARVIS_MOUSE_SUPPORT"] = "1" if self.mouse_support else "0"
        self.tui.mouse_mode = mode
        self.state_guard.enable_mouse_capture(mode)
        if HAS_PROMPT_TOOLKIT and self._pt_session is not None:
            try:
                self._pt_session.mouse_support = self.mouse_support
            except Exception as e:
                logger.debug("Could not update pt_session mouse_support: %s", e)

    def set_mouse_support(self, enabled: bool) -> None:
        """Dynamically enable or disable mouse support in the CLI terminal session."""
        target_mode = MouseCaptureMode.MOUSE_INTERACTIVE if enabled else MouseCaptureMode.MOUSE_OFF
        self.set_mouse_capture_mode(target_mode)

    # ── Event bus wiring ──────────────────────────────────────────────────────

    def _setup_event_listeners(self) -> None:
        """Subscribe to event bus for real-time background task updates."""
        try:
            event_bus = self.runtime.event_bus if self.runtime else None
            if event_bus:
                event_bus.subscribe("task.completed", self._on_task_event)
                event_bus.subscribe("task.failed", self._on_task_event)
                event_bus.subscribe("task.tool_started", self._on_tool_event)
                event_bus.subscribe("task.tool_completed", self._on_tool_event)
        except Exception as e:
            logger.debug("EventBus listener setup notice: %s", e)

    def _on_task_event(self, event: Any) -> None:
        """Handle background task lifecycle notifications."""
        try:
            status = getattr(event, "status", "updated")
            goal = getattr(event, "goal", "")
            if goal and self._is_running and HAS_RICH and self.renderer.console:
                if "fail" in str(status).lower():
                    self.renderer.console.print(f"\n[bold red]{Glyphs.CROSS} Background task failed:[/] {goal[:60]}")
                elif "complete" in str(status).lower():
                    self.renderer.console.print(
                        f"\n[bold green]{Glyphs.CHECK} Background task complete:[/] {goal[:60]}"
                    )
        except Exception:
            pass

    def _on_tool_event(self, event: Any) -> None:
        """Handle tool execution telemetry (for live step display)."""
        pass  # Consumed by live display in execute_turn

    # ── Header & prompt ───────────────────────────────────────────────────────

    def render_header(self) -> None:
        """Render session status header."""
        try:
            tool_count = 0
            try:
                from brjarvis.tools.registry import TOOL_SCHEMAS

                tool_count = len(TOOL_SCHEMAS)
            except Exception:
                pass

            info = {
                "mode": self.current_mode,
                "model": (
                    getattr(self.runtime.config.models, "default_backend", "Gemini")
                    if self.runtime and hasattr(self.runtime, "config")
                    else "Gemini"
                ),
                "session_id": self.session_id,
                "session_name": self.session_name,
                "permission_mode": os.environ.get("JARVIS_PERMISSION_MODE", "CONFIRM_DESTRUCTIVE"),
                "memory_status": "ACTIVE",
                "tool_count": tool_count,
            }
            self.renderer.render_header(info)
        except Exception as e:
            logger.debug("Header render error: %s", e)

    def get_prompt_text(self) -> str:
        """Return styled prompt string based on current context state."""
        mode = self.current_mode.upper()
        mode_color = MODE_COLORS.get(self.current_mode, "cyan")

        if self._prompt_state == PROMPT_APPROVAL:
            if HAS_RICH:
                return f"\n[bold #ff6d00]approval required[/] [bold {mode_color}]›[/] "
            return "\napproval required › "

        if self._prompt_state == PROMPT_NEEDS_INPUT:
            if HAS_RICH:
                return f"\n[bold #d500f9]JARVIS needs input[/] [bold {mode_color}]›[/] "
            return "\nJARVIS needs input › "

        if self._prompt_state == PROMPT_TASK and self._active_task_label:
            raw_label = self._active_task_label.strip()
            label = (raw_label[:20] + "…") if len(raw_label) > 20 else raw_label
            if HAS_RICH:
                return f"\n[bold #1de9b6]task:{label}[/] [bold {mode_color}]›[/] "
            return f"\ntask:{label} › "

        # Normal prompt
        if mode == "GENERAL":
            if HAS_RICH:
                return f"\n[bold white]you[/] [bold {mode_color}]›[/] "
            return "\nyou › "
        else:
            if HAS_RICH:
                return f"\n[bold white]you[/] [bold {mode_color}][{mode}] ›[/] "
            return f"\nyou [{mode}] › "

    def _get_plain_prompt(self) -> str:
        """Return the bare text prompt string for prompt_toolkit."""
        mode = self.current_mode.upper()

        if self._prompt_state == PROMPT_APPROVAL:
            return "approval required › "
        if self._prompt_state == PROMPT_NEEDS_INPUT:
            return "JARVIS needs input › "
        if self._prompt_state == PROMPT_TASK and self._active_task_label:
            raw_label = self._active_task_label.strip()
            label = (raw_label[:20] + "…") if len(raw_label) > 20 else raw_label
            return f"task:{label} › "
        if mode == "GENERAL":
            return "you › "
        return f"you [{mode}] › "

    def _get_pt_formatted_prompt(self) -> Any:
        """Return prompt_toolkit formatted text for the prompt."""
        if not HAS_PROMPT_TOOLKIT:
            return self._get_plain_prompt()
        try:
            from prompt_toolkit.formatted_text import FormattedText

            mode = self.current_mode.upper()

            if self._prompt_state == PROMPT_APPROVAL:
                return FormattedText(
                    [
                        ("class:prompt.approval", "\napproval required"),
                        ("class:prompt.arrow", " › "),
                    ]
                )
            if self._prompt_state == PROMPT_NEEDS_INPUT:
                return FormattedText(
                    [
                        ("class:prompt.needs", "\nJARVIS needs input"),
                        ("class:prompt.arrow", " › "),
                    ]
                )
            if self._prompt_state == PROMPT_TASK and self._active_task_label:
                raw_label = self._active_task_label.strip()
                label = (raw_label[:20] + "…") if len(raw_label) > 20 else raw_label
                return FormattedText(
                    [
                        ("class:prompt.task", f"\ntask:{label}"),
                        ("class:prompt.arrow", " › "),
                    ]
                )
            if mode == "GENERAL":
                return FormattedText(
                    [
                        ("class:prompt.you", "\nyou"),
                        ("class:prompt.arrow", " › "),
                    ]
                )
            return FormattedText(
                [
                    ("class:prompt.you", "\nyou"),
                    ("class:prompt.bracket", " ["),
                    ("class:prompt.mode", mode),
                    ("class:prompt.bracket", "]"),
                    ("class:prompt.arrow", " › "),
                ]
            )
        except Exception:
            return self._get_plain_prompt()

    # ── REPL loop ─────────────────────────────────────────────────────────────

    def close(self, consolidate: bool = True, message: Optional[str] = None) -> None:
        """Gracefully close the session, consolidate learnings, and preserve active task state."""
        if self._closed:
            return
        self._closed = True
        self._is_running = False

        # 1. Preserve active task state if present
        if self._active_task_id:
            try:
                from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

                mgr = get_task_state_manager()
                task = mgr.get_task(self._active_task_id)
                if task and task.status in (TaskStatus.RUNNING, TaskStatus.CREATED):
                    mgr.update_status(self._active_task_id, TaskStatus.WAITING_FOR_USER)
                    logger.info(
                        "Active task %s preserved with status WAITING_FOR_USER on session close", self._active_task_id
                    )
            except Exception as task_err:
                logger.debug("Task state preservation note on close: %s", task_err)

        # 2. Consolidate learnings via orchestrator / runtime shutdown and AgentSession
        if hasattr(self, "agent_session") and self.agent_session:
            try:
                self.agent_session.close(consolidate=consolidate)
            except Exception as s_err:
                logger.debug("AgentSession close note: %s", s_err)

        if consolidate:
            try:
                orch = self.orchestrator
                if orch and hasattr(orch, "shutdown"):
                    orch.shutdown()
            except Exception as orch_err:
                logger.debug("Orchestrator shutdown note: %s", orch_err)

        # 3. Clean console output
        msg = message or "\n[bold yellow]⚡ BR JARVIS session closed. Learnings consolidated.[/bold yellow]\n"
        if HAS_RICH and self.renderer.console:
            try:
                self.renderer.console.print(msg)
            except Exception:
                pass
        else:
            print("\n⚡ BR JARVIS session closed. Learnings consolidated.")

    def _handle_interrupt(self, force_quit: bool = False) -> Optional[str]:
        """Handle interrupt signal (Esc or Ctrl+C) to cancel active tasks or reset prompt state."""
        self._interrupt_count += 1
        if self._interrupt_count >= 2 or force_quit:
            if HAS_RICH and self.renderer and self.renderer.console:
                self.renderer.console.print("\n[bold yellow]⚡ Session terminated by user.[/bold yellow]")
            else:
                print("\n⚡ Session terminated by user.")
            self.close(consolidate=True)
            return None

        # Reset active prompt state and cancel any active background task
        self._prompt_state = PROMPT_NORMAL
        if self._active_task_id:
            try:
                from brjarvis.agent.task_state import TaskStatus, get_task_state_manager

                mgr = get_task_state_manager()
                mgr.update_status(self._active_task_id, TaskStatus.CANCELLED)
                self._active_task_id = None
                self._active_task_label = None
            except Exception as e:
                logger.debug("Task cancel on interrupt note: %s", e)

        if HAS_RICH and self.renderer and self.renderer.console:
            self.renderer.console.print(
                "\n[dim yellow]⚡ Interrupted. (Press Esc or Ctrl+C again to exit)[/dim yellow]"
            )
        else:
            print("\n⚡ Interrupted. (Press Esc or Ctrl+C again to exit)")
        return ""

    # ── REPL loop ─────────────────────────────────────────────────────────────

    def run_repl(self) -> None:
        """Start the interactive REPL loop."""
        self._is_running = True
        self._interrupt_count = 0

        # Ensure terminal mouse capture is armed
        if self.mouse_support:
            try:
                self.state_guard.enable_mouse_capture(self.mouse_capture_mode)
            except Exception as e:
                logger.debug("REPL mouse capture arming note: %s", e)

        try:
            self.renderer.clear()
        except Exception:
            pass
        self.render_header()

        if self.auto_welcome:
            model_name = (
                getattr(self.runtime.config.models, "default_backend", "Gemini")
                if self.runtime and hasattr(self.runtime, "config")
                else "Gemini"
            )
            self.renderer.render_welcome(
                mode=self.current_mode,
                working_dir=os.getcwd(),
                model_name=model_name,
            )

        exit_aliases = {"exit", "quit", "q", ":q", ":quit", ":exit", "bye", "goodbye"}

        while self._is_running:
            try:
                user_input = self._read_input()
            except (EOFError, KeyboardInterrupt):
                self.close(consolidate=True)
                break

            if not user_input:
                continue

            # Reset interrupt counter on successful input
            self._interrupt_count = 0

            # Slash / exit command dispatch
            lower_input = user_input.lower().strip()
            if user_input.startswith("/") or lower_input in exit_aliases:
                should_continue = self.commands.execute(user_input)
                if not should_continue:
                    self.close(consolidate=True)
                    break
                continue

            # Direct approval keyword handler (e.g. typing 'approve', 'allow', 'yes', 'y')
            if lower_input in ("approve", "allow", "yes", "y", "agree", "accept", "proceed") and (
                self._prompt_state == PROMPT_APPROVAL or self._active_task_id is not None
            ):
                self.commands.execute(f"/approve {self._active_task_id or ''}".strip())
                continue

            # Cognitive turn
            self.execute_turn(user_input)

        if not self._closed:
            self.close(consolidate=True)

    def _read_input(self) -> str:
        """Read user input using prompt_toolkit or rich fallback."""
        if self._pt_session is not None and HAS_PROMPT_TOOLKIT:
            try:
                return self._pt_session.prompt(
                    self._get_pt_formatted_prompt(),
                    style=None,  # style already in session
                    mouse_support=self.mouse_support,
                ).strip()
            except KeyboardInterrupt:
                return self._handle_interrupt(force_quit=False) or ""
            except EOFError:
                raise
        elif HAS_RICH and self.renderer.console:
            try:
                prompt_str = self.get_prompt_text()
                return Prompt.ask(prompt_str).strip()
            except KeyboardInterrupt:
                return self._handle_interrupt(force_quit=False) or ""
            except EOFError:
                raise
        else:
            try:
                return input(self._get_plain_prompt()).strip()
            except KeyboardInterrupt:
                return self._handle_interrupt(force_quit=False) or ""
            except EOFError:
                raise

    def _handle_interrupt(self, force_quit: bool = False) -> Optional[str]:
        """Handle Ctrl+C with double-tap logic or force quit."""
        now = time.monotonic()
        if force_quit or (self._interrupt_count >= 1 and now - self._last_interrupt < 2.0):
            self.close(consolidate=True)
            return None

        self._interrupt_count += 1
        self._last_interrupt = now
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(
                "\n[dim]Interrupted. Press Ctrl+C again or Ctrl+D to quit, or type a command to continue.[/dim]"
            )
        else:
            print("\nInterrupted. Press Ctrl+C again or Ctrl+D to quit.")
        return ""

    # ── Interactive Permissions ───────────────────────────────────────────────

    def prompt_permission(self, req: PermissionRequest) -> PermissionDecision:
        """Render interactive permission prompt card and capture decision."""
        PermissionPromptComponent.render(self.renderer.console, req)
        try:
            choice = (
                input("Authorize action [y=allow once, a/s=allow all/session, d=deny, c=cancel] › ").strip().lower()
            )
            if choice in ("y", "yes", "allow", "1", "ok"):
                return PermissionDecision.ALLOW_ONCE
            elif choice in ("s", "session", "always", "allow_session", "a", "all", "allow_all"):
                return PermissionDecision.ALLOW_SESSION
            elif choice in ("t", "tool", "allow_tool"):
                return PermissionDecision.ALLOW_TOOL
            elif choice in ("c", "cancel"):
                return PermissionDecision.CANCEL
            else:
                return PermissionDecision.DENY
        except (KeyboardInterrupt, EOFError):
            return PermissionDecision.CANCEL

    # ── Cognitive execution ───────────────────────────────────────────────────

    def execute_turn(self, user_input: str) -> None:
        """Execute a cognitive agent turn with live step visualization."""
        t_start = time.monotonic()

        try:
            router = getattr(self.orchestrator, "router", None) if self.orchestrator else None
            # Live spinner during cognitive turn
            if HAS_RICH and self.renderer.console and getattr(sys.stdout, "isatty", lambda: False)():
                spinner_label = self._get_spinner_label()
                with self.renderer.console.status(
                    f"[bold {COLOR_CYAN}]{spinner_label}[/] [dim]({self.current_mode.upper()})[/dim]",
                    spinner="dots",
                ):
                    if hasattr(self, "agent_loop") and self.agent_loop:
                        response = self.agent_loop.run_turn(
                            user_input,
                            router=router,
                            interactive_permission_cb=self.prompt_permission,
                        )
                    elif self.orchestrator is not None:
                        handler_func = getattr(
                            self.orchestrator, "handle_query", getattr(self.orchestrator, "chat", None)
                        )
                        if callable(handler_func):
                            response = handler_func(user_input)
                        else:
                            response = "Orchestrator chat handler is not available."
                    else:
                        response = "No active agent loop or orchestrator runtime available."
            else:
                if hasattr(self, "agent_loop") and self.agent_loop:
                    response = self.agent_loop.run_turn(
                        user_input,
                        router=router,
                        interactive_permission_cb=self.prompt_permission,
                    )
                elif self.orchestrator is not None:
                    handler_func = getattr(self.orchestrator, "handle_query", getattr(self.orchestrator, "chat", None))
                    if callable(handler_func):
                        response = handler_func(user_input)
                    else:
                        response = "Orchestrator chat handler is not available."
                else:
                    response = "No active agent loop or orchestrator runtime available."

            if asyncio.iscoroutine(response):
                response = asyncio.run(response)

            elapsed_ms = (time.monotonic() - t_start) * 1000
            self._render_turn_output(user_input, response, elapsed_ms)

        except KeyboardInterrupt:
            if HAS_RICH and self.renderer.console:
                self.renderer.console.print(
                    f"\n[bold {COLOR_AMBER}]⚠ Turn interrupted. Task state preserved.[/bold {COLOR_AMBER}]"
                )
            else:
                print("\n[Turn interrupted by user]")
        except Exception as e:
            logger.exception("Error executing agent turn: %s", e)
            err_msg = str(e)
            # Truncate traceback unless verbose
            if not self.verbose and len(err_msg) > 400:
                err_msg = err_msg[:400] + "…"
            try:
                self.renderer.render_error(
                    "Agent Execution Error",
                    err_msg,
                    [
                        "Verify API keys in .env (GEMINI_API_KEY, OPENAI_API_KEY)",
                        "Run /doctor to diagnose subsystem health",
                        "Try /verbose on for full error details",
                        "Try switching mode: /mode general",
                    ],
                )
            except Exception:
                print(f"\n[Agent Execution Error] {err_msg}")

    def _get_spinner_label(self) -> str:
        """Context-aware spinner label."""
        mode_labels = {
            "coder": "◆ Coding...",
            "analyst": "◆ Analyzing...",
            "researcher": "◆ Researching...",
            "planner": "◆ Planning...",
            "automation": "◆ Automating...",
            "recon": "◆ Reconnoitering...",
        }
        return mode_labels.get(self.current_mode, "◆ Thinking...")

    def _render_turn_output(self, user_input: str, response: Any, elapsed_ms: float) -> None:
        """Render agent response with mode-colored header and markdown."""
        resp_str = str(response) if not hasattr(response, "text") else response.text
        if not resp_str or not str(resp_str).strip():
            resp_str = "No response generated."
        if HAS_RICH and self.renderer and self.renderer.console:
            try:
                mode_color = MODE_COLORS.get(self.current_mode, "cyan")
                self.renderer.console.print(f"\n[{mode_color} bold]jarvis[/] [dim]({elapsed_ms:.0f}ms)[/]:")
                self.renderer.render_markdown(resp_str)
                self.renderer.console.print()
            except Exception:
                print(f"\njarvis ({elapsed_ms:.0f}ms):\n{resp_str}\n")
        else:
            print(f"\njarvis ({elapsed_ms:.0f}ms):\n{resp_str}\n")

    # ── One-shot query ────────────────────────────────────────────────────────

    def run_query(self, query: str) -> int:
        """Execute a single one-shot query and exit cleanly."""
        self.render_header()
        if HAS_RICH and self.renderer.console:
            self.renderer.console.print(f"[bold {COLOR_CYAN}]⚡ Query:[/] [white]{query}[/]\n")
        else:
            print(f"Query: {query}\n")
        self.execute_turn(query)
        return 0

    # ── Session state helpers ─────────────────────────────────────────────────

    def set_active_task(self, task_id: str, label: str) -> None:
        """Mark a task as active (changes prompt to task: style)."""
        self._active_task_id = task_id
        self._active_task_label = label
        self._prompt_state = PROMPT_TASK

    def clear_active_task(self) -> None:
        """Clear active task prompt state."""
        self._active_task_id = None
        self._active_task_label = None
        self._prompt_state = PROMPT_NORMAL

    def set_prompt_state(self, state: str) -> None:
        """Set prompt context state (normal/task/approval/needs_input)."""
        self._prompt_state = state
