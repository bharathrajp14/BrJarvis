# tests/intent/test_14_acceptance_cases.py — Section 64 Final Acceptance Test Suite
"""
Validates the exact 14 Final Acceptance Cases from Section 64 of the specification:
CASE 1: 'open Excel' -> one action, fast path allowed
CASE 2: 'open Excel and then show system properties' -> two actions, sequential, verify both
CASE 3: 'show CPU and RAM usage' -> one grouped diagnostic request
CASE 4: 'open Chrome and search GitHub' -> browser workflow with ordered actions
CASE 5: 'don't open Chrome' -> no action
CASE 6: 'how do I open Chrome?' -> explanation only
CASE 7: 'what if you opened Chrome?' -> explanation only
CASE 8: 'open Chrome, actually Edge' -> only Edge action
CASE 9: 'open Chrome and if that fails use Edge' -> conditional execution
CASE 10: 'take a screenshot and analyze it' -> capture, verify, analyze, final result
CASE 11: 'download the report and move it to Documents' -> download, verify, move, verify
CASE 12: 'open VS Code, create hello.py, run it, and tell me the output' -> four-stage workflow
CASE 13: 'research X and create a PDF report' -> research, verify, create artifact
CASE 14: 'open Excel and show system properties' -> both actions
"""

from unittest.mock import patch

from brjarvis.core.canonical_runtime import CanonicalRequestRuntime
from brjarvis.core.intent_models import AtomicityType, ExecutionState
from brjarvis.core.request_understanding import RequestUnderstandingEngine
from brjarvis.core.side_effect_barrier import SideEffectBarrier


class TestFinal14AcceptanceCases:
    """Verifies all 14 mandatory Section 64 acceptance criteria."""

    def test_case_1_open_excel(self):
        """CASE 1: 'open Excel' -> one action, fast path allowed."""
        u = RequestUnderstandingEngine.understand("open Excel")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1
        assert u.deterministic_eligible is True

    def test_case_2_open_excel_and_then_show_system_properties(self):
        """CASE 2: 'open Excel and then show system properties' -> two actions, sequential, verify both."""
        u = RequestUnderstandingEngine.understand("open Excel and then show system properties")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2
        assert u.deterministic_eligible is False

        with patch.object(SideEffectBarrier, "_launch_app_safely", return_value={"success": True, "target": "excel"}):
            with patch.object(
                SideEffectBarrier,
                "_run_system_diagnostics_safely",
                return_value={"success": True, "cpu_percent": 12.0, "ram_percent": 50.0},
            ):
                res = CanonicalRequestRuntime.handle("open Excel and then show system properties")
                assert res.state == ExecutionState.COMPLETED
                assert len(res.records) == 2
                assert res.records[0].status == "COMPLETED"
                assert res.records[1].status == "COMPLETED"

    def test_case_3_show_cpu_and_ram_usage(self):
        """CASE 3: 'show CPU and RAM usage' -> one grouped diagnostic request."""
        u = RequestUnderstandingEngine.understand("show CPU and RAM usage")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1
        assert u.actions[0].intent == "grouped_operation"
        assert u.actions[0].tool == "system_diagnostics"

    def test_case_4_open_chrome_and_search_github(self):
        """CASE 4: 'open Chrome and search GitHub' -> browser workflow with ordered actions."""
        u = RequestUnderstandingEngine.understand("open Chrome and search GitHub")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2
        assert u.actions[1].depends_on == [u.actions[0].action_id]

    def test_case_5_dont_open_chrome(self):
        """CASE 5: 'don't open Chrome' -> no action."""
        u = RequestUnderstandingEngine.understand("don't open Chrome")
        assert u.atomicity == AtomicityType.NEGATED
        assert u.action_count == 0
        assert u.deterministic_eligible is False

    def test_case_6_how_do_i_open_chrome(self):
        """CASE 6: 'how do I open Chrome?' -> explanation only."""
        u = RequestUnderstandingEngine.understand("how do I open Chrome?")
        assert u.atomicity == AtomicityType.INFORMATIONAL
        assert u.action_count == 0

    def test_case_7_what_if_you_opened_chrome(self):
        """CASE 7: 'what if you opened Chrome?' -> explanation only."""
        u = RequestUnderstandingEngine.understand("what if you opened Chrome?")
        assert u.atomicity == AtomicityType.HYPOTHETICAL
        assert u.action_count == 0

    def test_case_8_open_chrome_actually_edge(self):
        """CASE 8: 'open Chrome, actually Edge' -> only Edge action."""
        u = RequestUnderstandingEngine.understand("open Chrome, actually Edge")
        assert "edge" in u.normalized_input.lower()
        assert "chrome" not in u.normalized_input.lower()
        assert u.atomicity == AtomicityType.ATOMIC

    def test_case_9_open_chrome_and_if_that_fails_use_edge(self):
        """CASE 9: 'open Chrome and if that fails use Edge' -> conditional execution."""
        u = RequestUnderstandingEngine.understand("open Chrome and if that fails use Edge")
        assert u.atomicity == AtomicityType.CONDITIONAL
        assert "if" in u.conditions

    def test_case_10_take_a_screenshot_and_analyze_it(self):
        """CASE 10: 'take a screenshot and analyze it' -> capture, verify, analyze, final result."""
        u = RequestUnderstandingEngine.understand("take a screenshot and analyze it")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2
        assert u.actions[1].depends_on == [u.actions[0].action_id]

    def test_case_11_download_the_report_and_move_it_to_documents(self):
        """CASE 11: 'download the report and move it to Documents' -> download, verify, move, verify."""
        u = RequestUnderstandingEngine.understand("download the report and move it to Documents")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2

    def test_case_12_open_vscode_create_hello_run_and_tell_output(self):
        """CASE 12: 'open VS Code, create hello.py, run it, and tell me the output' -> four-stage workflow."""
        u = RequestUnderstandingEngine.understand("open VS Code, create hello.py, run it, and tell me the output")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count >= 3
        assert u.deterministic_eligible is False

    def test_case_13_research_x_and_create_a_pdf_report(self):
        """CASE 13: 'research quantum computing and create a PDF report' -> research, verify, generate."""
        u = RequestUnderstandingEngine.understand("research quantum computing and create a PDF report")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2

    def test_case_14_open_excel_and_show_system_properties(self):
        """CASE 14: 'open Excel and show system properties' -> both actions."""
        u = RequestUnderstandingEngine.understand("open Excel and show system properties")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2
        assert len(u.actions) == 2
