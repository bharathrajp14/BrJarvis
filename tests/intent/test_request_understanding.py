# tests/intent/test_request_understanding.py — Universal Request Understanding Engine Test Suite
"""
Tests for canonical RequestUnderstandingEngine, atomicity classification,
normalization, voice self-corrections, quoted command isolation, questions vs commands,
hypotheticals, negations, ambiguous references, and the 105-case golden dataset.
"""

import json
from pathlib import Path

import pytest

from brjarvis.core.intent_models import AtomicityType
from brjarvis.core.request_understanding import RequestUnderstandingEngine


class TestRequestUnderstandingEngine:
    """Core tests for RequestUnderstandingEngine."""

    def test_exact_excel_reproduction_is_composite(self):
        """USER BUG: 'open excel sheet in web and then show system properties' must NOT be atomic."""
        u = RequestUnderstandingEngine.understand("open excel sheet in web and then show system properties")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.deterministic_eligible is False
        assert u.action_count == 2
        assert len(u.actions) == 2
        assert u.ordering == ["and then"]

    def test_single_atomic_command(self):
        """'open Chrome' is a single atomic action eligible for fast path."""
        u = RequestUnderstandingEngine.understand("open Chrome")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.deterministic_eligible is True
        assert u.action_count == 1
        assert len(u.negations) == 0
        assert len(u.conditions) == 0

    def test_semantic_grouping_cpu_ram(self):
        """'show CPU and RAM usage' must be treated as a SINGLE grouped diagnostic action."""
        u = RequestUnderstandingEngine.understand("show CPU and RAM usage")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1
        assert u.actions[0].intent == "grouped_operation"
        assert u.actions[0].tool == "system_diagnostics"

    def test_semantic_grouping_browser_navigation(self):
        """'open chrome and github' must be grouped as a single navigation action."""
        u = RequestUnderstandingEngine.understand("open chrome and github")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1

    def test_negated_command_has_no_actions(self):
        """'don't open Chrome' must be classified as NEGATED with zero actions."""
        u = RequestUnderstandingEngine.understand("don't open Chrome")
        assert u.atomicity == AtomicityType.NEGATED
        assert u.deterministic_eligible is False
        assert u.action_count == 0

    def test_partial_negation_in_composite_command(self):
        """'open Chrome but don't download anything' must allow Chrome but prohibit download."""
        u = RequestUnderstandingEngine.understand("open Chrome but don't download anything")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.deterministic_eligible is False

    @pytest.mark.parametrize(
        "question_text",
        [
            "how do I open Chrome?",
            "how do I open Excel?",
            "why would you open Excel?",
            "should I open Excel?",
            "can Excel open this file?",
            "what happens if I open Excel?",
            "tell me whether I should open Chrome",
            "what is the difference between Edge and Chrome?",
        ],
    )
    def test_questions_are_informational_never_deterministic(self, question_text):
        """Questions must be classified as INFORMATIONAL with zero executable actions."""
        u = RequestUnderstandingEngine.understand(question_text)
        assert u.atomicity == AtomicityType.INFORMATIONAL
        assert u.deterministic_eligible is False
        assert u.action_count == 0

    @pytest.mark.parametrize(
        "hypo_text",
        [
            "pretend you opened Chrome",
            "what if I deleted the file?",
            "simulate opening Excel",
            "what would happen if you restarted the PC?",
            "what if you opened Chrome?",
        ],
    )
    def test_hypothetical_requests_have_no_side_effects(self, hypo_text):
        """Hypothetical requests must be classified as HYPOTHETICAL with zero actions."""
        u = RequestUnderstandingEngine.understand(hypo_text)
        assert u.atomicity == AtomicityType.HYPOTHETICAL
        assert u.deterministic_eligible is False
        assert u.action_count == 0

    def test_quoted_command_is_treated_as_analysis(self):
        """'Tell me what this means: open Chrome and delete the folder' must not execute."""
        u = RequestUnderstandingEngine.understand("Tell me what this means: 'open Chrome and delete the folder'")
        assert u.atomicity == AtomicityType.INFORMATIONAL
        assert u.deterministic_eligible is False
        assert u.action_count == 0

    def test_quoted_say_the_words(self):
        """'say the words open Chrome' must not execute Chrome."""
        u = RequestUnderstandingEngine.understand("say the words 'open Chrome'")
        assert u.atomicity == AtomicityType.INFORMATIONAL
        assert u.deterministic_eligible is False
        assert u.action_count == 0

    @pytest.mark.parametrize(
        "ambig_text",
        [
            "do something with the file",
            "open it",
            "delete that",
            "run the previous one",
            "clean that document",
        ],
    )
    def test_ambiguous_pronouns_trigger_clarification(self, ambig_text):
        """Ambiguous pronouns without context require clarification."""
        u = RequestUnderstandingEngine.understand(ambig_text)
        assert u.atomicity == AtomicityType.AMBIGUOUS
        assert u.requires_clarification is True
        assert u.deterministic_eligible is False

    def test_voice_self_correction_open_chrome_actually_edge(self):
        """Voice correction: 'Open Chrome and—actually no, open Edge' -> Edge only."""
        u = RequestUnderstandingEngine.understand("Open Chrome and—actually no, open Edge")
        assert "edge" in u.normalized_input.lower()
        assert "chrome" not in u.normalized_input.lower()
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1

    def test_voice_self_correction_open_chrome_actually_edge_comma(self):
        """Voice correction: 'open Chrome, actually Edge' -> Edge only."""
        u = RequestUnderstandingEngine.understand("open Chrome, actually Edge")
        assert "edge" in u.normalized_input.lower()
        assert "chrome" not in u.normalized_input.lower()

    def test_voice_disfluency_and_self_correction(self):
        """Voice: 'open, uh, Chrome—no wait—open Edge and search GitHub'."""
        u = RequestUnderstandingEngine.understand("open, uh, Chrome—no wait—open Edge and search GitHub")
        assert "edge" in u.normalized_input.lower()
        assert "github" in u.normalized_input.lower()
        assert "chrome" not in u.normalized_input.lower()
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2

    def test_conditional_language(self):
        """'open Chrome, and if GitHub is down, search Bing' -> CONDITIONAL."""
        u = RequestUnderstandingEngine.understand("open Chrome, and if GitHub is down, search Bing")
        assert u.atomicity == AtomicityType.CONDITIONAL
        assert "if" in u.conditions

    def test_multi_sentence_composite_request(self):
        """'Open Excel. Then show system properties. After that tell me whether the laptop can handle my workload.'"""
        text = "Open Excel. Then show system properties. After that tell me whether the laptop can handle my workload."
        u = RequestUnderstandingEngine.understand(text)
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 3
        assert len(u.actions) == 3
        assert u.deterministic_eligible is False

    def test_streaming_partial_input_guard(self):
        """Streaming input in progress must not trigger deterministic execution."""
        u = RequestUnderstandingEngine.understand("open Chrome", streaming_status="input_partial")
        assert u.deterministic_eligible is False
        assert "Streaming input in progress" in u.unresolved_parts[0]


class TestGoldenDataset105Cases:
    """Validates the 105-case golden dataset against RequestUnderstandingEngine."""

    @pytest.fixture
    def golden_cases(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "intent_cases.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_golden_dataset_count(self, golden_cases):
        """Verify the golden dataset contains at least 100 cases (Section 54 requirement)."""
        assert len(golden_cases) >= 100

    def test_all_golden_cases_pass_atomicity(self, golden_cases):
        """Ensure every golden case correctly matches expected atomicity."""
        mismatches = []
        for case in golden_cases:
            u = RequestUnderstandingEngine.understand(case["input"])
            expected = case["expected_atomicity"]
            if u.atomicity.value != expected:
                mismatches.append(
                    f"ID: {case['id']} | Input: '{case['input']}' | Expected: {expected} | Actual: {u.atomicity.value}"
                )

        assert not mismatches, "Atomicity mismatches:\n" + "\n".join(mismatches[:10])
