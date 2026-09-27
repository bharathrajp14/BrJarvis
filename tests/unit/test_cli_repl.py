# tests/unit/test_cli_repl.py — Comprehensive Unit Tests for BR JARVIS MK41 CLI
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from brjarvis.agent.task_state import TaskAction, TaskState, TaskStatus
from brjarvis.core.terminal.autocomplete import (
    SLASH_COMMANDS,
    JarvisCompleter,
)
from brjarvis.core.terminal.commands import SlashCommandHandler
from brjarvis.core.terminal.renderer import TerminalRenderer
from brjarvis.core.terminal.session import (
    PROMPT_APPROVAL,
    PROMPT_NORMAL,
    TerminalSession,
)


class TestJarvisCompleter(unittest.TestCase):
    """Test autocomplete engine and suggestions."""

    def setUp(self):
        self.completer = JarvisCompleter()

    def test_empty_input(self):
        self.assertEqual(self.completer.get_completions_for(""), [])
        self.assertEqual(self.completer.get_completions_for("hello"), [])

    def test_slash_prefix_completions(self):
        results = self.completer.get_completions_for("/")
        self.assertGreaterEqual(len(results), len(SLASH_COMMANDS))

    def test_partial_command_completions(self):
        results = self.completer.get_completions_for("/mo")
        cmds = [r["text"] for r in results]
        self.assertIn("/mode", cmds)
        self.assertIn("/model", cmds)

    def test_mode_argument_completions(self):
        results = self.completer.get_completions_for("/mode c")
        modes = [r["text"] for r in results]
        self.assertIn("coder", modes)

    def test_model_argument_completions(self):
        results = self.completer.get_completions_for("/model g")
        models = [r["text"] for r in results]
        self.assertTrue(any("gemini" in m or "gpt" in m or "gateway" in m for m in models))

    def test_permission_argument_completions(self):
        results = self.completer.get_completions_for("/permission a")
        perms = [r["text"] for r in results]
        self.assertIn("auto", perms)
        self.assertIn("accept_edits", perms)

    def test_tools_argument_completions(self):
        results = self.completer.get_completions_for("/tools h")
        subs = [r["text"] for r in results]
        self.assertIn("health", subs)

    def test_mouse_argument_completions(self):
        results = self.completer.get_completions_for("/mouse o")
        subs = [r["text"] for r in results]
        self.assertTrue("on" in subs or "off" in subs)


class TestTerminalRenderer(unittest.TestCase):
    """Test rendering methods (non-raising assertions)."""

    def setUp(self):
        self.renderer = TerminalRenderer()

    def test_render_header(self):
        info = {
            "mode": "coder",
            "model": "gemini-2.5-flash",
            "session_id": "test-session-1234",
            "permission_mode": "CONFIRM_DESTRUCTIVE",
            "memory_status": "ACTIVE",
            "tool_count": 127,
        }
        # Should not raise
        self.renderer.render_header(info)

    def test_render_welcome(self):
        self.renderer.render_welcome()

    def test_render_plan_panel(self):
        steps = [
            "Inspect profile",
            "Inspect projects",
            "Generate portfolio files",
            "Validate HTML",
            "Git commit",
            "Push to GitHub",
        ]
        self.renderer.render_plan_panel(
            goal="Create and publish portfolio",
            steps=steps,
            risk="Medium",
            external_actions=["GitHub push"],
            plan_id="plan_test123",
        )

    def test_render_plan_vs_actual(self):
        planned = ["Inspect profile", "Build portfolio", "Git commit", "Push GitHub"]
        completed = ["Inspect profile", "Build portfolio", "Git commit"]
        failed = ["Push GitHub"]
        skipped = []
        self.renderer.render_plan_vs_actual(
            planned_steps=planned,
            completed_steps=completed,
            failed_steps=failed,
            skipped_steps=skipped,
            final_status="PARTIAL_SUCCESS",
            task_id="task_0192",
        )

    def test_render_task_detail(self):
        task = TaskState(
            task_id="task_0192",
            goal="Create portfolio",
            status=TaskStatus.RUNNING,
            actions=[
                TaskAction(action_id="a1", step_index=1, tool="file_reader", status="completed"),
                TaskAction(action_id="a2", step_index=2, tool="code_helper", status="completed"),
            ],
            artifacts=[{"name": "index.html", "path": "portfolio/index.html", "verified": True}],
        )
        self.renderer.render_task_detail(task)

    def test_render_artifact_panel(self):
        artifacts = [
            {"name": "index.html", "path": "portfolio/index.html", "verified": True},
            {"name": "style.css", "path": "portfolio/style.css", "verified": True},
        ]
        self.renderer.render_artifact_panel(artifacts, verified=True)

    def test_render_doctor_report(self):
        checks = [
            {"name": "Python 3.12", "ok": True, "detail": "Active"},
            {"name": "Tool Registry", "ok": True, "detail": "127 tools"},
            {"name": "Gmail Auth", "ok": False, "detail": "Token expired"},
        ]
        self.renderer.render_doctor_report(checks, overall="DEGRADED — Gmail Auth")

    def test_render_connectors_table(self):
        connectors = [
            {"name": "GitHub", "status": "connected", "capabilities": ["push", "read"]},
            {"name": "Gmail", "status": "auth_required", "capabilities": ["send", "read"]},
        ]
        self.renderer.render_connectors_table(connectors)

    def test_render_model_table(self):
        models = [
            {
                "name": "gemini",
                "model": "gemini-2.5-flash",
                "status": "available",
                "context": "1M",
                "capabilities": ["vision", "code"],
            },
            {"name": "gpt", "model": "gpt-4o", "status": "available", "context": "128K", "capabilities": ["code"]},
        ]
        self.renderer.render_model_table(models, active="gemini")

    def test_render_usage_stats(self):
        stats = {
            "Session Duration": "12.5 minutes",
            "Conversation Turns": "8 turns",
            "Active Backend": "gemini",
        }
        self.renderer.render_usage_stats(stats)

    def test_render_success_banner(self):
        self.renderer.render_success_banner(
            title="SUCCESS_VERIFIED",
            details={"Portfolio": "https://bharthraj1412.github.io/portfolio", "Files": "3 created"},
        )


class TestSlashCommandHandler(unittest.TestCase):
    """Test all slash commands."""

    def setUp(self):
        # Create a mock session
        self.session = MagicMock(spec=TerminalSession)
        self.session.renderer = TerminalRenderer()
        self.session.current_mode = "general"
        self.session.session_id = "test-session"
        self.session.session_name = ""
        self.session.output_style = "compact"
        self.session.verbose = False
        self.session.runtime = None
        self.session.orchestrator = MagicMock()
        self.session.orchestrator.current_mode = "general"
        self.session._active_task_id = None
        self.session._active_task_label = None

        self.handler = SlashCommandHandler(self.session)

    def test_exit_commands(self):
        self.assertFalse(self.handler.execute("/quit"))
        self.assertFalse(self.handler.execute("/exit"))
        self.assertFalse(self.handler.execute("quit"))
        self.assertFalse(self.handler.execute("exit"))

    def test_help_command(self):
        self.assertTrue(self.handler.execute("/help"))

    def test_status_command(self):
        self.assertTrue(self.handler.execute("/status"))

    def test_version_command(self):
        self.assertTrue(self.handler.execute("/version"))

    def test_mode_command(self):
        self.assertTrue(self.handler.execute("/mode coder"))
        self.assertEqual(self.session.current_mode, "coder")

        # Invalid mode should not crash
        self.assertTrue(self.handler.execute("/mode non_existent_mode"))

    def test_model_command(self):
        self.assertTrue(self.handler.execute("/model"))
        # Invalid backend should not crash
        self.assertTrue(self.handler.execute("/model invalid_backend_xyz"))

    def test_permission_command(self):
        self.assertTrue(self.handler.execute("/permission"))
        self.assertTrue(self.handler.execute("/permission auto"))
        self.assertEqual(os.environ.get("JARVIS_PERMISSION_MODE"), "ALLOW_ALL")
        self.assertTrue(self.handler.execute("/permission confirm_destructive"))
        self.assertEqual(os.environ.get("JARVIS_PERMISSION_MODE"), "CONFIRM_DESTRUCTIVE")

    def test_style_command(self):
        self.assertTrue(self.handler.execute("/style"))
        self.assertTrue(self.handler.execute("/style detailed"))
        self.assertEqual(self.session.output_style, "detailed")
        self.assertTrue(self.handler.execute("/style compact"))
        self.assertEqual(self.session.output_style, "compact")

    def test_verbose_command(self):
        self.assertTrue(self.handler.execute("/verbose"))
        self.assertTrue(self.handler.execute("/verbose on"))
        self.assertTrue(self.session.verbose)
        self.assertTrue(self.handler.execute("/verbose off"))
        self.assertFalse(self.session.verbose)

    def test_mouse_command(self):
        self.session.mouse_support = False
        self.assertTrue(self.handler.execute("/mouse"))
        self.assertTrue(self.session.set_mouse_support.called)

        self.assertTrue(self.handler.execute("/mouse on"))
        self.session.set_mouse_support.assert_called_with(True)

        self.assertTrue(self.handler.execute("/mouse off"))
        self.session.set_mouse_support.assert_called_with(False)

        self.assertTrue(self.handler.execute("/mouse status"))

    def test_approve_command_auto_detect(self):
        mock_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.task_id = "task_auto_appr"
        mock_task.approval_request = MagicMock()
        mock_task.approval_request.request_id = "req_123"
        mock_task.goal = "Build portfolio"
        mock_mgr.get_task.return_value = mock_task
        mock_mgr.list_tasks.return_value = [mock_task]
        mock_mgr.resolve_approval.return_value = mock_task

        with patch("brjarvis.agent.task_state.get_task_state_manager", return_value=mock_mgr):
            # 1. With explicit task_id
            self.assertTrue(self.handler.execute("/approve task_auto_appr"))
            mock_mgr.resolve_approval.assert_called_with("task_auto_appr", "req_123", approved=True)

            # 2. Auto-detect without task_id
            self.session._active_task_id = "task_auto_appr"
            self.assertTrue(self.handler.execute("/approve"))
            mock_mgr.resolve_approval.assert_called_with("task_auto_appr", "req_123", approved=True)

    def test_rename_command(self):
        self.assertTrue(self.handler.execute("/rename Portfolio Sprint"))
        self.assertEqual(self.session.session_name, "Portfolio Sprint")

    def test_context_command(self):
        self.assertTrue(self.handler.execute("/context"))

    def test_tools_command(self):
        self.assertTrue(self.handler.execute("/tools"))
        self.assertTrue(self.handler.execute("/tools health"))
        self.assertTrue(self.handler.execute("/tools failed"))

    def test_connectors_command(self):
        self.assertTrue(self.handler.execute("/connectors"))
        self.assertTrue(self.handler.execute("/connectors github"))

    def test_doctor_command(self):
        self.assertTrue(self.handler.execute("/doctor"))

    def test_usage_command(self):
        self.assertTrue(self.handler.execute("/usage"))

    def test_palette_command(self):
        self.assertTrue(self.handler.execute("/"))
        self.assertTrue(self.handler.execute("/ plan"))

    def test_plan_command_with_mock_approval(self):
        with patch.object(self.session.renderer, "prompt_plan_approval", return_value="cancel"):
            self.assertTrue(self.handler.execute("/plan Build a portfolio website"))


class TestTerminalSessionPrompts(unittest.TestCase):
    """Test smart prompt formatting across different states."""

    def setUp(self):
        self.session = TerminalSession(auto_welcome=False)

    def test_agent_loop_receives_runtime_gateway(self):
        self.assertIsNotNone(self.session.runtime)
        self.assertIs(self.session.agent_loop.gateway, self.session.runtime.gateway)

    def test_general_prompt(self):
        self.session.current_mode = "general"
        self.session._prompt_state = PROMPT_NORMAL
        prompt = self.session.get_prompt_text()
        self.assertIn("you", prompt)
        self.assertIn("›", prompt)

    def test_coder_prompt(self):
        self.session.current_mode = "coder"
        self.session._prompt_state = PROMPT_NORMAL
        prompt = self.session.get_prompt_text()
        self.assertIn("CODER", prompt)
        self.assertIn("›", prompt)

    def test_task_prompt(self):
        self.session.set_active_task("task_0192", "portfolio")
        prompt = self.session.get_prompt_text()
        self.assertIn("task:portfolio", prompt)
        self.assertIn("›", prompt)

    def test_approval_prompt(self):
        self.session.set_prompt_state(PROMPT_APPROVAL)
        prompt = self.session.get_prompt_text()
        self.assertIn("approval required", prompt)
        self.assertIn("›", prompt)


class TestTerminalSafeExit(unittest.TestCase):
    """Test safe exit handling, Ctrl+D (EOFError), exit aliases, and state preservation."""

    def setUp(self):
        self.session = TerminalSession(auto_welcome=False)
        self.handler = SlashCommandHandler(self.session)

    def test_exit_command_aliases(self):
        aliases = ["/quit", "/exit", "quit", "exit", "/q", "q", ":q", ":quit", ":exit", "bye", "goodbye"]
        for alias in aliases:
            with patch.object(self.session, "close") as mock_close:
                res = self.handler.execute(alias)
                self.assertFalse(res, f"Expected execute('{alias}') to return False")
                mock_close.assert_called_with(consolidate=True)

    def test_repl_eof_error_triggers_safe_close(self):
        with (
            patch.object(self.session, "_read_input", side_effect=EOFError),
            patch.object(self.session, "close", wraps=self.session.close) as mock_close,
        ):
            self.session.run_repl()
            mock_close.assert_called_with(consolidate=True)
            self.assertTrue(self.session._closed)
            self.assertFalse(self.session._is_running)

    def test_repl_keyboard_interrupt_force_quit(self):
        with (
            patch.object(self.session, "_read_input", side_effect=KeyboardInterrupt),
            patch.object(self.session, "close", wraps=self.session.close) as mock_close,
        ):
            self.session.run_repl()
            mock_close.assert_called_with(consolidate=True)
            self.assertTrue(self.session._closed)

    def test_active_task_preserved_on_close(self):
        mock_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.status = TaskStatus.RUNNING
        mock_mgr.get_task.return_value = mock_task

        with patch("brjarvis.agent.task_state.get_task_state_manager", return_value=mock_mgr):
            self.session.set_active_task("task_test_preserve", "portfolio")
            self.session.close(consolidate=True)
            mock_mgr.update_status.assert_called_with("task_test_preserve", TaskStatus.WAITING_FOR_USER)

    def test_prompt_approval_safe_cancel_on_eof(self):
        renderer = TerminalRenderer()
        with patch("rich.prompt.Prompt.ask", side_effect=EOFError):
            choice = renderer.prompt_plan_approval()
            self.assertEqual(choice, "cancel")

    def test_permission_prompt_safe_deny_on_eof(self):
        renderer = TerminalRenderer()
        with patch("rich.prompt.Prompt.ask", side_effect=EOFError):
            decision = renderer.render_permission_prompt("file_writer", "test.py", "write")
            self.assertEqual(decision, "deny")

    def test_cli_main_catches_eof_and_returns_zero(self):
        from brjarvis.core.cli import main as cli_main

        with patch("sys.argv", ["cli"]), patch.object(TerminalSession, "run_repl", side_effect=EOFError):
            ret = cli_main()
            self.assertEqual(ret, 0)

    def test_terminal_session_mouse_support(self):
        session = TerminalSession(auto_welcome=False)
        self.assertTrue(hasattr(session, "mouse_support"))
        session.set_mouse_support(True)
        self.assertTrue(session.mouse_support)
        self.assertEqual(os.environ.get("JARVIS_MOUSE_SUPPORT"), "1")
        session.set_mouse_support(False)
        self.assertFalse(session.mouse_support)
        self.assertEqual(os.environ.get("JARVIS_MOUSE_SUPPORT"), "0")


if __name__ == "__main__":
    unittest.main()
