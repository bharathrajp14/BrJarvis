"""
Unit tests for Atomic vs. Composite Intent Classification and Execution.
Verifies the fix for premature 0-token execution on multi-step user requests.
Covers:
  - Required Cases A through K (Section 19)
  - 20+ Representative Regression Utterances (Section 20)
  - Execution Trace Recording (Section 21)
  - Dependency and Partial Completion Reporting (Section 12, 13)
  - Deduplication Guard Preservation (Section 18)
  - Final Acceptance Test (Section 28)
"""

from __future__ import annotations

import pytest

from brjarvis.core.composite_executor import CompositeIntentExecutor
from brjarvis.core.intent_classifier import IntentClassifier, IntentTraceStore
from brjarvis.core.intent_engine import DeterministicIntentEngine
from brjarvis.core.intent_models import AtomicIntentResult, CompositeIntent

# ==============================================================================
# SECTION 19: REQUIRED CASES A THROUGH K
# ==============================================================================


@pytest.mark.unit
def test_case_a_open_excel_online():
    """Case A: 'open excel online' -> atomic, deterministic, executed immediately."""
    query = "open excel online"
    classification = IntentClassifier.classify(query)

    assert isinstance(classification, AtomicIntentResult)
    assert classification.atomic is True
    assert classification.requires_planner is False
    assert classification.consumed_text != ""
    assert classification.remaining_text == ""

    # Must execute deterministically
    res = DeterministicIntentEngine.parse_and_execute(query)
    assert res is not None
    assert res.get("executed") is True
    assert res.get("intent") in ("open_online_app", "open_online_excel")
    assert "excel.new" in res.get("target", "")


@pytest.mark.unit
def test_case_b_open_excel_online_and_then_show_system_properties():
    """Case B: 'open excel online and then show system properties' -> composite, NOT deterministic, 2 ordered steps."""
    query = "open excel online and then show system properties"

    # Deterministic shortcut MUST NOT execute
    fast_res = DeterministicIntentEngine.parse_and_execute(query)
    assert fast_res is None, "Deterministic fast-path must NOT execute composite multi-action request!"

    # Classifier must identify composite intent with 2 ordered steps
    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) == 2
    assert classification.actions[0].order == 1
    assert classification.actions[0].intent == "open_online_excel"
    assert classification.actions[1].order == 2
    assert classification.actions[1].intent == "show_system_properties"
    assert 1 in classification.actions[1].depends_on

    # Sequential execution must execute both in order
    comp_res = CompositeIntentExecutor.execute(classification)
    assert comp_res.get("executed") is True
    assert comp_res.get("status") == "completed"
    assert len(comp_res.get("step_results", [])) == 2
    assert "Step 1 completed" in comp_res["result"]
    assert "Step 2 completed" in comp_res["result"]


@pytest.mark.unit
def test_case_c_open_chrome_and_github():
    """Case C: 'open chrome and github' -> grouped browser navigation intent, NEVER premature termination."""
    query = "open chrome and github"
    classification = IntentClassifier.classify(query)

    # Must be recognized as an atomic grouped navigation intent
    assert isinstance(classification, AtomicIntentResult)
    assert classification.atomic is True

    # Must execute targeting github in chrome
    res = DeterministicIntentEngine.parse_and_execute(query)
    assert res is not None
    assert res.get("executed") is True
    assert "github" in res.get("target", "")


@pytest.mark.unit
def test_case_d_show_cpu_and_ram_usage():
    """Case D: 'show CPU and RAM usage' -> single grouped system-health intent."""
    query = "show CPU and RAM usage"
    classification = IntentClassifier.classify(query)

    assert isinstance(classification, AtomicIntentResult)
    assert classification.atomic is True

    res = DeterministicIntentEngine.parse_and_execute(query)
    assert res is not None
    assert res.get("executed") is True
    assert res.get("intent") == "system_health"


@pytest.mark.unit
def test_case_e_open_calculator_and_then_open_notepad():
    """Case E: 'open calculator and then open notepad' -> two sequential actions."""
    query = "open calculator and then open notepad"

    # Must NOT execute deterministically
    assert DeterministicIntentEngine.parse_and_execute(query) is None

    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) == 2
    assert classification.actions[0].intent == "open_calculator"
    assert classification.actions[1].intent == "open_notepad"


@pytest.mark.unit
def test_case_f_take_screenshot_and_save_it_to_documents():
    """Case F: 'take screenshot and save it to documents' -> composite workflow."""
    query = "take screenshot and save it to documents"

    # Must NOT execute deterministically
    assert DeterministicIntentEngine.parse_and_execute(query) is None

    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) >= 2


@pytest.mark.unit
def test_case_g_open_vscode_create_test_py_and_run_it():
    """Case G: 'open vscode, create test.py, and run it' -> multi-step workflow."""
    query = "open vscode, create test.py, and run it"

    # Must NOT execute deterministically
    assert DeterministicIntentEngine.parse_and_execute(query) is None

    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) == 3


@pytest.mark.unit
def test_case_h_why_should_i_open_excel():
    """Case H: 'why should I open Excel?' -> NO deterministic execution."""
    query = "why should I open Excel?"

    assert DeterministicIntentEngine.parse_and_execute(query) is None
    classification = IntentClassifier.classify(query)
    assert classification.requires_planner is True


@pytest.mark.unit
def test_case_i_do_not_open_excel():
    """Case I: 'do not open Excel' -> NO deterministic execution."""
    query = "do not open Excel"

    assert DeterministicIntentEngine.parse_and_execute(query) is None
    classification = IntentClassifier.classify(query)
    assert classification.requires_planner is True


@pytest.mark.unit
def test_case_j_tell_me_how_to_open_excel():
    """Case J: 'tell me how to open Excel' -> NO deterministic execution."""
    query = "tell me how to open Excel"

    assert DeterministicIntentEngine.parse_and_execute(query) is None
    classification = IntentClassifier.classify(query)
    assert classification.requires_planner is True


@pytest.mark.unit
def test_case_k_open_excel_and_dont_show_system_properties():
    """Case K: 'open Excel and don't show system properties' -> must not execute the second action."""
    query = "open Excel and don't show system properties"

    # Must NOT execute deterministically
    assert DeterministicIntentEngine.parse_and_execute(query) is None

    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) == 2
    assert classification.actions[1].is_negated is True

    # Sequential execution must execute step 1 and SKIP negated step 2
    comp_res = CompositeIntentExecutor.execute(classification)
    assert comp_res.get("executed") is True
    step2 = [r for r in comp_res.get("step_results", []) if r["step"] == 2][0]
    assert step2["status"] == "skipped_negated"
    assert "skipped (negated" in step2["message"]


# ==============================================================================
# SECTION 20: 20+ REPRESENTATIVE REGRESSION UTTERANCES
# ==============================================================================

REGRESSION_UTTERANCES = [
    # query, expected_is_atomic, expected_deterministic, expected_step_count
    ("open excel online", True, True, 1),
    ("open notepad", True, True, 1),
    ("open calculator", True, True, 1),
    ("open chrome", True, True, 1),
    ("mute volume", True, True, 1),
    ("volume up", True, True, 1),
    ("take screenshot", True, True, 1),
    ("show cpu usage", True, True, 1),
    ("show ram usage", True, True, 1),
    ("system health", True, True, 1),
    ("show cpu and ram usage", True, True, 1),
    ("open chrome and github", True, True, 1),
    ("open excel sheet in web and then show system properties", False, False, 2),
    ("open calculator and then open notepad", False, False, 2),
    ("open chrome and go to github", False, False, 2),
    ("open excel and show system information", False, False, 2),
    ("take screenshot and save it to documents", False, False, 2),
    ("open vscode, create test.py, and run it", False, False, 3),
    ("check my CPU and then launch Task Manager", False, False, 2),
    ("why should I open Excel?", False, False, 0),
    ("do not open Excel", False, False, 0),
    ("tell me how to open Excel", False, False, 0),
    ("how do I launch calculator?", False, False, 0),
    ("never shut down my computer", False, False, 0),
    ("open Excel and don't show system properties", False, False, 2),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    "query,expected_is_atomic,expected_deterministic,expected_step_count",
    REGRESSION_UTTERANCES,
)
def test_regression_utterance_suite(query, expected_is_atomic, expected_deterministic, expected_step_count):
    """Test classification, atomicity, execution path, and step count on 25 representative utterances."""
    classification = IntentClassifier.classify(query)

    if expected_is_atomic:
        assert isinstance(classification, AtomicIntentResult), f"Expected atomic for '{query}'"
        assert classification.atomic is True
        assert classification.requires_planner is False
        if expected_deterministic:
            res = DeterministicIntentEngine.parse_and_execute(query)
            assert res is not None, f"Expected deterministic execution for '{query}'"
            assert res.get("executed") is True
    else:
        # Must NOT execute deterministically
        res = DeterministicIntentEngine.parse_and_execute(query)
        assert res is None, f"Expected deterministic shortcut to return None for '{query}'"

        if expected_step_count > 0:
            assert isinstance(classification, CompositeIntent), f"Expected composite for '{query}'"
            assert len(classification.actions) == expected_step_count
        else:
            # Conversational / negated query
            assert classification.requires_planner is True


# ==============================================================================
# SECTION 21: EXECUTION TRACE OBSERVABILITY
# ==============================================================================


@pytest.mark.unit
def test_execution_trace_recording():
    """Verify ExecutionTrace records user_input, classification, steps, and deterministic flag."""
    IntentTraceStore.clear()

    # 1. Atomic query trace
    DeterministicIntentEngine.parse_and_execute("open calculator")
    trace = IntentTraceStore.get_last_trace()
    assert trace is not None
    assert trace.user_input == "open calculator"
    assert trace.classification == "atomic"
    assert trace.deterministic is True
    assert trace.planner_required is False

    # 2. Composite query trace
    query = "open excel sheet in web and then show system properties"
    DeterministicIntentEngine.parse_and_execute(query)
    comp_trace = IntentTraceStore.get_last_trace()
    assert comp_trace is not None
    assert comp_trace.user_input == query
    assert comp_trace.classification == "composite"
    assert comp_trace.deterministic is False
    assert comp_trace.planner_required is True


# ==============================================================================
# SECTION 12 & 13: STEP VERIFICATION & PARTIAL COMPLETION
# ==============================================================================


@pytest.mark.unit
def test_composite_partial_completion_reporting(monkeypatch):
    """Verify that if Step 1 succeeds and Step 2 fails, truthful partial status is reported."""
    query = "open excel online and then show system properties"
    composite = IntentClassifier.classify(query)

    # Monkeypatch Step 2 to fail
    def mock_fail_step(action, engine):
        if action.order == 1:
            return True, "Opened Online Excel Sheets at https://excel.new"
        return False, "Failed to query system properties: access denied"

    monkeypatch.setattr(CompositeIntentExecutor, "_execute_single_action", mock_fail_step)

    res = CompositeIntentExecutor.execute(composite)
    assert res["status"] == "partial"
    assert "Step 1 completed" in res["result"]
    assert "Step 2 failed" in res["result"]
    assert "Completed." not in res["result"]


# ==============================================================================
# SECTION 18: DEDUPLICATION GUARD PRESERVATION
# ==============================================================================


@pytest.mark.unit
def test_dedup_guard_preserved():
    """Verify deduplication guard prevents duplicate app execution within TTL window."""
    DeterministicIntentEngine._DEDUP_CACHE.clear()
    assert DeterministicIntentEngine._dedup_check("test_target_app") is False
    assert DeterministicIntentEngine._dedup_check("test_target_app") is True


# ==============================================================================
# SECTION 28: EXACT REPRODUCTION ACCEPTANCE TEST
# ==============================================================================


@pytest.mark.unit
def test_acceptance_excel_and_system_properties():
    """
    CRITICAL ACCEPTANCE TEST (Section 28):
    USER: 'open excel sheet in web and then show system properties'
    RUNTIME EXPECTATION:
      1. COMPOSITE DETECTION
      2. 2 ACTIONS IDENTIFIED (open_online_excel + show_system_properties)
      3. PLAN PRESERVED (Step 1 -> Step 2)
      4. STEP 1: OPEN EXCEL ONLINE (VERIFIED)
      5. STEP 2: SHOW SYSTEM PROPERTIES (VERIFIED)
      6. FINAL RESPONSE: Reports both actions, never premature first-action termination.
    """
    query = "open excel sheet in web and then show system properties"

    # Step 1: Must NOT prematurely execute and terminate at deterministic engine
    fast_res = DeterministicIntentEngine.parse_and_execute(query)
    assert fast_res is None, "BUG DETECTED: Premature 0-token execution occurred!"

    # Step 2: Composite detection
    classification = IntentClassifier.classify(query)
    assert isinstance(classification, CompositeIntent)
    assert len(classification.actions) == 2
    assert classification.actions[0].intent == "open_online_excel"
    assert classification.actions[1].intent == "show_system_properties"

    # Step 3: Sequential execution of both actions
    result = CompositeIntentExecutor.execute(classification)
    assert result["executed"] is True
    assert result["status"] == "completed"
    assert len(result["step_results"]) == 2

    # Step 4: Step 1 verified
    assert result["step_results"][0]["status"] == "completed"
    assert "excel.new" in result["step_results"][0]["output"]

    # Step 5: Step 2 verified
    assert result["step_results"][1]["status"] == "completed"
    assert "System Properties" in result["step_results"][1]["output"]

    # Step 6: Truthful acknowledgment and combined output
    assert "I'll open Excel first, then show the system properties." in result["result"]
    assert "Step 1 completed" in result["result"]
    assert "Step 2 completed" in result["result"]
