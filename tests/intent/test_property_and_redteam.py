# tests/intent/test_property_and_redteam.py — Property-Based & Red-Team Adversarial Test Suite
"""
Tests critical architectural invariants and adversarial red-team injection attacks
to ensure NO partial match or modified utterance can trigger unauthorized or premature side-effects.
"""

from unittest.mock import patch

import pytest

from brjarvis.core.canonical_runtime import CanonicalRequestRuntime
from brjarvis.core.intent_models import AtomicityType
from brjarvis.core.request_understanding import RequestUnderstandingEngine
from brjarvis.core.side_effect_barrier import SideEffectBarrier


class TestPropertyBasedInvariants:
    """Verifies invariant properties across transformed inputs (Section 55)."""

    @pytest.mark.parametrize(
        "base_command",
        [
            "open Chrome",
            "open Excel",
            "launch notepad",
            "start calculator",
        ],
    )
    def test_invariant_appending_and_then_prevents_premature_completion(self, base_command):
        """Appending 'and then...' or a second command MUST prevent fast-path execution."""
        u_base = RequestUnderstandingEngine.understand(base_command)
        assert u_base.deterministic_eligible is True

        transformed = f"{base_command} and then show system properties"
        u_trans = RequestUnderstandingEngine.understand(transformed)
        assert u_trans.deterministic_eligible is False
        assert u_trans.atomicity == AtomicityType.COMPOSITE
        assert u_trans.action_count == 2

    @pytest.mark.parametrize(
        "base_command",
        [
            "open Chrome",
            "open Excel",
            "launch notepad",
        ],
    )
    def test_invariant_adding_negation_prevents_execution(self, base_command):
        """Adding 'don't' to any command must prevent execution."""
        negated = f"don't {base_command}"
        u = RequestUnderstandingEngine.understand(negated)
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.NEGATED
        assert u.action_count == 0

    @pytest.mark.parametrize(
        "base_command",
        [
            "open Chrome",
            "open Excel",
            "launch notepad",
        ],
    )
    def test_invariant_turning_into_question_prevents_execution(self, base_command):
        """Turning any command into a question must prevent deterministic execution."""
        question = f"how do I {base_command.lower()}?"
        u = RequestUnderstandingEngine.understand(question)
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.INFORMATIONAL

    @pytest.mark.parametrize(
        "base_command",
        [
            "open Chrome",
            "open Excel",
            "delete the folder",
        ],
    )
    def test_invariant_embedding_in_quotes_prevents_execution(self, base_command):
        """Embedding any command inside quotes must prevent execution."""
        quoted = f"Tell me what this means: '{base_command}'"
        u = RequestUnderstandingEngine.understand(quoted)
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.INFORMATIONAL


class TestRedTeamAdversarialCases:
    """Verifies all Red-Team test patterns from Section 56."""

    def test_redteam_open_chrome_and_then_truncated(self):
        """'open Chrome and then...' must not trigger execution."""
        u = RequestUnderstandingEngine.understand("open Chrome and then...")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.AMBIGUOUS

    def test_redteam_open_chrome_but_dont_truncated(self):
        """'open Chrome but don't...' must not trigger execution."""
        u = RequestUnderstandingEngine.understand("open Chrome but don't...")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.AMBIGUOUS

    def test_redteam_open_chrome_if_truncated(self):
        """'open Chrome if...' must not trigger execution."""
        u = RequestUnderstandingEngine.understand("open Chrome if...")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.CONDITIONAL

    def test_redteam_open_chrome_question_actually(self):
        """'open Chrome? Actually...' must not trigger execution."""
        u = RequestUnderstandingEngine.understand("open Chrome? Actually...")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.AMBIGUOUS

    def test_redteam_tell_me_whether_i_should_open_chrome(self):
        """'tell me whether I should open Chrome' -> INFORMATIONAL."""
        u = RequestUnderstandingEngine.understand("tell me whether I should open Chrome")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.INFORMATIONAL

    def test_redteam_what_happens_if_you_open_chrome(self):
        """'what happens if you open Chrome' -> INFORMATIONAL."""
        u = RequestUnderstandingEngine.understand("what happens if you open Chrome")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.INFORMATIONAL

    def test_redteam_say_the_words_open_chrome(self):
        """'say the words \"open Chrome\"' -> quote analysis / INFORMATIONAL."""
        u = RequestUnderstandingEngine.understand("say the words 'open Chrome'")
        assert u.deterministic_eligible is False
        assert u.atomicity == AtomicityType.INFORMATIONAL

    def test_redteam_open_chrome_and_dont_do_anything_else(self):
        """'open Chrome and don't do anything else' -> Chrome only."""
        u = RequestUnderstandingEngine.understand("open Chrome and don't do anything else")
        assert u.atomicity == AtomicityType.ATOMIC
        assert u.action_count == 1

    def test_redteam_open_chrome_wait_edge(self):
        """'open Chrome — wait — Edge' -> only Edge."""
        u = RequestUnderstandingEngine.understand("open Chrome — wait — Edge")
        assert "edge" in u.normalized_input.lower()
        assert "chrome" not in u.normalized_input.lower()
        assert u.atomicity == AtomicityType.ATOMIC

    def test_redteam_open_chrome_and_delete_the_folder_requires_confirmation(self):
        """'open Chrome and delete the folder' must require confirmation because of delete."""
        u = RequestUnderstandingEngine.understand("open Chrome and delete the folder")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.action_count == 2
        assert u.requires_confirmation is True
        assert u.risk_level in ("HIGH", "CRITICAL")

    def test_redteam_open_chrome_after_checking(self):
        """'open Chrome after checking disk space' -> ordered composite, no premature Chrome open."""
        u = RequestUnderstandingEngine.understand("open Chrome after checking disk space")
        assert u.atomicity == AtomicityType.COMPOSITE
        assert u.deterministic_eligible is False
        assert u.action_count == 2

    def test_zero_side_effects_on_adversarial_queries(self):
        """Verify CanonicalRequestRuntime triggers 0 side effects on all red-team inputs."""
        red_team_inputs = [
            "open Chrome and then...",
            "open Chrome but don't...",
            "open Chrome if...",
            "tell me whether I should open Chrome",
            "what happens if you open Chrome",
            "say the words 'open Chrome'",
        ]
        with patch.object(SideEffectBarrier, "execute") as mock_exec:
            for query in red_team_inputs:
                res = CanonicalRequestRuntime.handle(query)
                assert res.fast_path is False
                assert len(res.records) == 0
            mock_exec.assert_not_called()
