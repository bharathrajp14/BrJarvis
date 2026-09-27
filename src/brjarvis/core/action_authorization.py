# core/action_authorization.py — Canonical Action Authorization Engine
"""
ActionAuthorizationEngine for BR JARVIS.
Validates proposed ActionPlans against security policies, system permissions,
dependency graph integrity, parameter completeness, and capability availability.

Rule: Parsers UNDERSTAND and PROPOSE; only ActionAuthorizationEngine AUTHORIZES.
No side-effect may occur without explicit authorization.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from brjarvis.core.intent_models import (
    ActionPlan,
    AuthorizedActionPlan,
    ProposedAction,
    RequestUnderstanding,
    RiskLevel,
)

logger = logging.getLogger("JARVIS.ActionAuthorization")


class ActionAuthorizationEngine:
    """
    Canonical Action Authorization Layer.
    Validates:
      1. Policy & Permissions (auto, allow_all, plan, accept_edits, confirm_destructive, confirm_all, deny)
      2. Risk Assessment (LOW, MEDIUM, HIGH, CRITICAL)
      3. Parameter Completeness
      4. Dependency DAG Integrity & Cycle Detection
      5. Verification Method Assignment
    """

    POLICY_AUTO = "auto"
    POLICY_ALLOW_ALL = "allow_all"
    POLICY_CONFIRM_DESTRUCTIVE = "confirm_destructive"
    POLICY_CONFIRM_ALL = "confirm_all"
    POLICY_DENY = "deny"

    @classmethod
    def build_plan_from_understanding(cls, understanding: RequestUnderstanding) -> ActionPlan:
        """Construct a validated ActionPlan DAG from RequestUnderstanding."""
        dag: Dict[str, List[str]] = {}
        for action in understanding.actions:
            dag[action.action_id] = list(action.depends_on)

        plan = ActionPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            request_id=understanding.request_id,
            original_text=understanding.raw_input,
            actions=understanding.actions,
            execution_mode=understanding.actions[0].execution_mode if understanding.actions else "SEQUENTIAL",  # type: ignore
            dag=dag,
            atomicity=understanding.atomicity,
            requires_confirmation=understanding.requires_confirmation,
            is_valid=True,
        )

        # Validate DAG has no cycles
        if cls._has_cycles(dag):
            plan.is_valid = False
            logger.error("[ActionAuthorization] Dependency cycle detected in ActionPlan DAG.")

        return plan

    @classmethod
    def _has_cycles(cls, dag: Dict[str, List[str]]) -> bool:
        """Topological cycle detection for ActionPlan DAG."""
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node: str) -> bool:
            visited[node] = 1
            for neighbor in dag.get(node, []):
                if visited.get(neighbor) == 1:
                    return True
                if visited.get(neighbor) == 0 and dfs(neighbor):
                    return True
            visited[node] = 2
            return False

        for n in dag:
            visited[n] = 0
        for n in dag:
            if visited[n] == 0:
                if dfs(n):
                    return True
        return False

    @classmethod
    def authorize(
        cls,
        plan: ActionPlan,
        policy: str = "auto",
        context: Optional[Dict[str, Any]] = None,
    ) -> AuthorizedActionPlan:
        """
        Authorize an ActionPlan for execution.
        Returns AuthorizedActionPlan with authorization token and approved actions.
        """
        denial_reasons: List[str] = []
        authorized_actions: List[ProposedAction] = []
        requires_user_approval = False

        env_mode = os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower()
        is_allow_all = (
            policy in (cls.POLICY_AUTO, cls.POLICY_ALLOW_ALL, "allow", "yolo", "allowall")
            and (
                policy in (cls.POLICY_ALLOW_ALL, "allow", "yolo", "allowall")
                or env_mode in ("allow_all", "auto", "allow", "off", "none", "yolo", "allowall")
            )
        )

        if not plan.is_valid:
            return AuthorizedActionPlan(
                plan_id=plan.plan_id,
                authorized=False,
                actions=[],
                denial_reasons=["ActionPlan DAG is invalid or contains circular dependencies"],
            )

        if policy == cls.POLICY_DENY:
            return AuthorizedActionPlan(
                plan_id=plan.plan_id,
                authorized=False,
                actions=[],
                denial_reasons=["Execution policy is set to DENY all actions"],
            )

        # Evaluate each proposed action
        for act in plan.actions:
            # 1. Prohibited / Negated Action Check
            if act.is_negated:
                denial_reasons.append(f"Action '{act.intent}' is explicitly negated or prohibited by user request")
                continue

            # 2. Risk Evaluation against Policy
            if is_allow_all:
                act.parameters["requires_approval"] = False
            elif act.risk_level == RiskLevel.CRITICAL:
                if policy in (cls.POLICY_CONFIRM_DESTRUCTIVE, cls.POLICY_CONFIRM_ALL):
                    requires_user_approval = True
                    act.parameters["requires_approval"] = True
                elif policy not in (cls.POLICY_AUTO, cls.POLICY_ALLOW_ALL):
                    denial_reasons.append(f"Action '{act.intent}' has CRITICAL risk and is blocked by policy '{policy}'")
                    continue

            elif act.risk_level == RiskLevel.HIGH and policy == cls.POLICY_CONFIRM_ALL:
                requires_user_approval = True
                act.parameters["requires_approval"] = True

            # 3. Parameter Completeness Check
            if not act.intent:
                denial_reasons.append(f"Action '{act.action_id}' missing required intent identifier")
                continue

            # 4. Dependency Existence Check
            missing_deps = [dep for dep in act.depends_on if dep not in plan.dag]
            if missing_deps:
                denial_reasons.append(f"Action '{act.intent}' references non-existent dependencies: {missing_deps}")
                continue

            # Assign concrete verification strategy if unset
            if not act.verification_strategy or act.verification_strategy == "default":
                if "open" in act.intent or "launch" in act.intent:
                    act.verification_strategy = "process_or_window_verifier"
                elif "browser" in act.intent or "visit" in act.intent:
                    act.verification_strategy = "browser_tab_verifier"
                elif "diagnostic" in act.intent or "health" in act.intent:
                    act.verification_strategy = "telemetry_verifier"
                else:
                    act.verification_strategy = "universal_verifier"

            authorized_actions.append(act)

        # Final authorization status
        authorized = len(authorized_actions) > 0 and len(denial_reasons) == 0

        final_requires_approval = False if is_allow_all else requires_user_approval
        final_approval_granted = True if is_allow_all else (not requires_user_approval)

        return AuthorizedActionPlan(
            plan_id=plan.plan_id,
            authorized=authorized,
            actions=authorized_actions,
            denial_reasons=denial_reasons,
            requires_user_approval=final_requires_approval,
            approval_granted=final_approval_granted,
            authorization_token=f"auth_{uuid.uuid4().hex[:12]}" if authorized else "",
        )
