# tests/runtime/test_canonical_runtime.py — Master Canonical Request Runtime Test Suite
"""
Tests for CanonicalRequestRuntime lifecycle, truthful state transitions,
dependency DAG execution, partial execution handling, cancellation,
and side-effect isolation across interfaces.
"""

from unittest.mock import patch

from brjarvis.core.canonical_runtime import CanonicalRequestRuntime
from brjarvis.core.intent_models import (
    ActionExecutionRecord,
    AtomicityType,
    ExecutionState,
)
from brjarvis.core.side_effect_barrier import SideEffectBarrier


class TestCanonicalRequestRuntimeLifecycle:
    """Validates the complete execution lifecycle in CanonicalRequestRuntime."""

    def test_cancellation_command_interrupts_immediately(self):
        """User input 'cancel' or 'stop' immediately halts with CANCELLED state."""
        res = CanonicalRequestRuntime.handle("cancel")
        assert res.state == ExecutionState.CANCELLED
        assert "cancelled" in res.text.lower()
        assert len(res.records) == 0

    def test_informational_request_causes_zero_side_effects(self):
        """Informational question produces zero side effects and zero execution records."""
        with patch.object(SideEffectBarrier, "execute") as mock_exec:
            res = CanonicalRequestRuntime.handle("how do I open Excel?")
            assert res.state == ExecutionState.COMPLETED
            assert res.understanding.atomicity == AtomicityType.INFORMATIONAL
            assert len(res.records) == 0
            mock_exec.assert_not_called()

    def test_hypothetical_request_causes_zero_side_effects(self):
        """Hypothetical query produces zero physical mutations."""
        with patch.object(SideEffectBarrier, "execute") as mock_exec:
            res = CanonicalRequestRuntime.handle("what if you opened Chrome?")
            assert res.state == ExecutionState.COMPLETED
            assert res.understanding.atomicity == AtomicityType.HYPOTHETICAL
            assert "[Simulation Mode]" in res.text
            assert len(res.records) == 0
            mock_exec.assert_not_called()

    def test_negated_request_causes_zero_side_effects(self):
        """Negated command produces zero side effects."""
        with patch.object(SideEffectBarrier, "execute") as mock_exec:
            res = CanonicalRequestRuntime.handle("don't open Chrome")
            assert res.state == ExecutionState.COMPLETED
            assert res.understanding.atomicity == AtomicityType.NEGATED
            assert "negated" in res.text.lower()
            assert len(res.records) == 0
            mock_exec.assert_not_called()

    def test_ambiguous_request_requests_clarification(self):
        """Ambiguous reference halts at WAITING_FOR_APPROVAL for user clarification."""
        res = CanonicalRequestRuntime.handle("open it")
        assert res.state == ExecutionState.WAITING_FOR_APPROVAL
        assert res.understanding.requires_clarification is True
        assert len(res.records) == 0

    def test_atomic_fast_path_execution(self):
        """Single atomic request executes via fast-path with verification."""
        with patch.object(SideEffectBarrier, "_launch_app_safely", return_value={"success": True, "target": "chrome"}):
            res = CanonicalRequestRuntime.handle("open Chrome")
            assert res.state == ExecutionState.COMPLETED
            assert res.fast_path is True
            assert len(res.records) == 1
            assert "Verified" in res.text
            assert "0-Token" not in res.text

    def test_exact_excel_reproduction_two_step_execution(self):
        """
        USER BUG REPRODUCTION FIX:
        'open excel sheet in web and then show system properties'
        Must execute BOTH actions sequentially with per-step verification.
        """
        with patch.object(SideEffectBarrier, "_open_url_safely", return_value={"success": True, "url": "https://excel.new"}):
            with patch.object(
                SideEffectBarrier,
                "_run_system_diagnostics_safely",
                return_value={"success": True, "cpu_percent": 14.2, "ram_percent": 45.0},
            ):
                res = CanonicalRequestRuntime.handle("open excel sheet in web and then show system properties")
                assert res.state == ExecutionState.COMPLETED
                assert res.fast_path is False
                assert len(res.records) == 2
                assert res.records[0].status == "COMPLETED"
                assert res.records[1].status == "COMPLETED"
                assert "Executed 2 actions successfully" in res.text
                assert "open" in res.records[0].intent.lower()
                assert "excel" in res.records[0].parameters.get("raw_clause", "").lower()
                assert "show" in res.records[1].intent.lower()

    def test_partial_completion_reporting_when_step_two_fails(self):
        """
        Requirement 27:
        If Action 1 succeeds and Action 2 fails, the task status must remain PARTIAL
        and truthful reporting must be delivered to the user.
        """
        step1_rec = ActionExecutionRecord(
            request_id="req_test",
            task_id="task_test",
            action_id="act_1",
            intent="open_1",
            tool="native_os",
            authorization=True,
            status="COMPLETED",
            observation={"success": True, "target": "excel"},
        )
        step2_rec = ActionExecutionRecord(
            request_id="req_test",
            task_id="task_test",
            action_id="act_2",
            intent="show_2",
            tool="native_os",
            authorization=True,
            status="FAILED",
            error="Diagnostic telemetry timeout",
        )

        with patch.object(SideEffectBarrier, "execute", side_effect=[step1_rec, step2_rec]):
            res = CanonicalRequestRuntime.handle("open excel sheet in web and then show system properties")
            assert res.state == ExecutionState.PARTIAL
            assert "Partial task execution: Completed 1 of 2 steps" in res.text
            assert "FAILED" in res.text

    def test_dependent_actions_skipped_if_parent_fails(self):
        """
        Requirement 28:
        If action 1 fails, dependent action 2 must be SKIPPED.
        """
        step1_fail = ActionExecutionRecord(
            request_id="req_test",
            task_id="task_test",
            action_id="act_1",
            intent="open_1",
            tool="native_os",
            authorization=True,
            status="FAILED",
            error="Browser binary not found",
        )

        with patch.object(SideEffectBarrier, "execute", return_value=step1_fail) as mock_exec:
            res = CanonicalRequestRuntime.handle("open excel sheet in web and then show system properties")
            # Only action 1 was sent to execute; action 2 was skipped because act_1 failed
            assert mock_exec.call_count == 1
            assert res.state == ExecutionState.FAILED or res.state == ExecutionState.PARTIAL
            # Record 2 is marked SKIPPED
            assert len(res.records) == 2
            assert res.records[1].status == "SKIPPED"
            assert "Unsatisfied dependencies" in res.records[1].error

    def test_legacy_deterministic_shortcut_compatibility(self):
        """DeterministicIntentEngine.parse_and_execute() compatibility shim."""
        with patch.object(SideEffectBarrier, "_launch_app_safely", return_value={"success": True, "target": "notepad"}):
            legacy_res = CanonicalRequestRuntime.handle_deterministic_shortcut("launch notepad")
            assert legacy_res is not None
            assert legacy_res["executed"] is True
            assert legacy_res["verified"] is True
            assert "tokens_saved" not in legacy_res

        # Multi-step requests must return None through legacy shortcut
        composite_legacy = CanonicalRequestRuntime.handle_deterministic_shortcut(
            "open excel sheet in web and then show system properties"
        )
        assert composite_legacy is None
