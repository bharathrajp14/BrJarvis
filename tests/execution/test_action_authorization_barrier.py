# tests/execution/test_action_authorization_barrier.py — Action Authorization & Side-Effect Barrier Tests
"""
Tests for ActionAuthorizationEngine governance, dependency DAG cycle detection,
policy and risk gating, SideEffectBarrier transactional execution, and audit logging.
"""

from unittest.mock import patch

import pytest

from brjarvis.core.action_authorization import ActionAuthorizationEngine
from brjarvis.core.intent_models import (
    ActionPlan,
    AuthorizedActionPlan,
    ProposedAction,
    RiskLevel,
)
from brjarvis.core.side_effect_barrier import (
    ActionExecutionRecordStore,
    SideEffectBarrier,
    UnauthorizedActionError,
)


class TestActionAuthorizationEngine:
    """Tests for ActionAuthorizationEngine policy and DAG validation."""

    def test_cycle_detection_in_action_plan_dag(self):
        """ActionPlan with cyclical dependencies must be rejected as invalid."""
        act1 = ProposedAction(action_id="act_1", intent="open_1", depends_on=["act_2"])
        act2 = ProposedAction(action_id="act_2", intent="show_2", depends_on=["act_1"])

        plan = ActionPlan(
            plan_id="plan_cycle",
            request_id="req_cycle",
            original_text="cycle test",
            actions=[act1, act2],
            dag={"act_1": ["act_2"], "act_2": ["act_1"]},
            is_valid=False,
        )

        auth = ActionAuthorizationEngine.authorize(plan, policy="auto")
        assert auth.authorized is False
        assert any("circular" in r.lower() or "invalid" in r.lower() for r in auth.denial_reasons)

    def test_missing_dependency_reference_is_denied(self):
        """Action referencing a non-existent action ID is denied."""
        act1 = ProposedAction(action_id="act_1", intent="open_1", depends_on=["act_missing"])
        plan = ActionPlan(
            plan_id="plan_missing",
            request_id="req_missing",
            original_text="missing dep",
            actions=[act1],
            dag={"act_1": ["act_missing"]},
            is_valid=True,
        )

        auth = ActionAuthorizationEngine.authorize(plan, policy="auto")
        assert auth.authorized is False
        assert any("non-existent" in r.lower() for r in auth.denial_reasons)

    def test_deny_policy_blocks_all_actions(self):
        """Execution policy 'deny' blocks even harmless actions."""
        act1 = ProposedAction(action_id="act_1", intent="show_1", risk_level=RiskLevel.LOW)
        plan = ActionPlan(
            plan_id="plan_deny",
            request_id="req_deny",
            original_text="show properties",
            actions=[act1],
            dag={"act_1": []},
            is_valid=True,
        )

        auth = ActionAuthorizationEngine.authorize(plan, policy="deny")
        assert auth.authorized is False
        assert any("deny" in r.lower() for r in auth.denial_reasons)

    def test_confirm_destructive_policy_requires_approval(self):
        """Critical destructive action requires explicit user approval under confirm_destructive."""
        act_crit = ProposedAction(
            action_id="act_del",
            intent="delete_database",
            risk_level=RiskLevel.CRITICAL,
        )
        plan = ActionPlan(
            plan_id="plan_crit",
            request_id="req_crit",
            original_text="delete database",
            actions=[act_crit],
            dag={"act_del": []},
            is_valid=True,
        )

        auth = ActionAuthorizationEngine.authorize(plan, policy="confirm_destructive")
        assert auth.requires_user_approval is True
        assert auth.approval_granted is False

    def test_negated_action_is_denied(self):
        """Action marked is_negated=True is omitted and denied."""
        act_neg = ProposedAction(
            action_id="act_neg",
            intent="download_file",
            is_negated=True,
        )
        plan = ActionPlan(
            plan_id="plan_neg",
            request_id="req_neg",
            original_text="don't download",
            actions=[act_neg],
            dag={"act_neg": []},
            is_valid=True,
        )

        auth = ActionAuthorizationEngine.authorize(plan, policy="auto")
        assert auth.authorized is False
        assert any("negated" in r.lower() for r in auth.denial_reasons)


class TestSideEffectBarrier:
    """Tests for SideEffectBarrier transaction barrier and audit ledger."""

    def test_unauthorized_action_raises_error(self):
        """Executing an action without valid authorization token raises UnauthorizedActionError."""
        act = ProposedAction(action_id="act_unauth", intent="open_chrome")
        unauth_plan = AuthorizedActionPlan(
            plan_id="plan_fake",
            authorized=False,
            actions=[],
            authorization_token="",
        )

        with pytest.raises(UnauthorizedActionError):
            SideEffectBarrier.execute(
                action=act,
                auth_plan=unauth_plan,
                task_id="task_123",
                request_id="req_123",
            )

    def test_authorized_execution_records_audit_ledger(self):
        """Authorized action records entry in ActionExecutionRecordStore with verification."""
        ActionExecutionRecordStore.clear()
        act = ProposedAction(
            action_id="act_valid",
            intent="open_notepad",
            parameters={"app_name": "notepad"},
        )
        auth_plan = AuthorizedActionPlan(
            plan_id="plan_valid",
            authorized=True,
            actions=[act],
            authorization_token="auth_valid_token_123",
        )

        with patch.object(SideEffectBarrier, "_launch_app_safely", return_value={"success": True, "target": "notepad"}):
            rec = SideEffectBarrier.execute(
                action=act,
                auth_plan=auth_plan,
                task_id="task_456",
                request_id="req_456",
            )

            assert rec.status == "COMPLETED"
            assert rec.authorization is True
            assert rec.completed_at is not None
            assert rec.verification.get("verified") is True

            # Verify it is in the audit ledger
            recent = ActionExecutionRecordStore.get_records_for_request("req_456")
            assert len(recent) == 1
            assert recent[0].action_id == "act_valid"
