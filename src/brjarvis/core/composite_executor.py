# core/composite_executor.py — Multi-Step Sequential Composite Intent Execution Engine
"""
Sequential, dependency-aware Execution Engine for predictable Composite Requests.
Preserves user execution order, executes step-by-step, verifies each step via ActionVerifier,
handles dependencies, reports truthful partial completions, and records full execution traces.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from brjarvis.agent.verifier import ActionVerifier
from brjarvis.core.intent_classifier import IntentTraceStore
from brjarvis.core.intent_models import CompositeIntent, ExecutionTrace

logger = logging.getLogger("JARVIS.CompositeExecutor")


class CompositeIntentExecutor:
    """
    Executes ordered, multi-action composite requests with step-level verification.
    Satisfies Requirements 10, 11, 12, 13, 21, 22, 28.
    """

    @classmethod
    def can_handle(cls, composite: CompositeIntent) -> bool:
        """Return True if this composite task consists of known predictable actions."""
        if not composite.actions:
            return False
        known_intents = {
            "open_online_excel",
            "open_online_word",
            "show_system_properties",
            "open_calculator",
            "open_notepad",
            "open_task_manager",
            "open_chrome",
            "open_url",
            "take_screenshot",
            "open_vscode",
            "system_health_grouped",
            "browser_open_url_grouped",
        }
        # Check if at least the core actions are known
        executable_actions = [a for a in composite.actions if not a.is_negated]
        if not executable_actions:
            return False
        return all(a.intent in known_intents or a.action_type in ("browser_open", "app_launch", "system_diagnostic", "open_url", "screenshot") for a in executable_actions)

    @classmethod
    def execute(cls, composite: CompositeIntent, orchestrator: Any = None) -> Dict[str, Any]:
        """
        Execute actions in exact order with strict dependency enforcement and ActionVerifier verification.
        """
        t_start = time.time()
        from brjarvis.core.side_effect_barrier import SideEffectBarrier

        trace = ExecutionTrace(
            user_input=composite.original_text,
            classification="composite",
            atomic=False,
            deterministic=False,
            intent="composite_workflow",
            steps=[a.intent for a in composite.actions],
            planner_required=True,
            execution_started=t_start,
        )

        # Plan / acknowledge message (Requirement 22)
        intro_phrases: List[str] = []
        for a in composite.actions:
            if a.is_negated:
                continue
            if a.intent == "open_online_excel":
                intro_phrases.append("open Excel first")
            elif a.intent == "show_system_properties":
                intro_phrases.append("then show the system properties")
            elif a.intent == "open_calculator":
                intro_phrases.append("open Calculator")
            elif a.intent == "open_notepad":
                intro_phrases.append("open Notepad")
            elif a.intent == "open_chrome":
                intro_phrases.append("open Chrome")
            elif a.intent == "open_url":
                intro_phrases.append(f"go to {a.parameters.get('url', 'URL')}")
            elif a.intent == "take_screenshot":
                intro_phrases.append("take a screenshot")
            else:
                intro_phrases.append(a.raw_text)

        intro_text = ""
        if len(intro_phrases) >= 2:
            intro_text = f"I'll {intro_phrases[0]}, {intro_phrases[1]}.\n\n"
        elif len(intro_phrases) == 1:
            intro_text = f"I'll {intro_phrases[0]}.\n\n"

        step_results: List[Dict[str, Any]] = []
        overall_success = True
        failed_step_order: Optional[int] = None

        for action in composite.actions:
            step_num = action.order

            # If this action is negated (Requirement K: "open Excel and don't show system properties")
            if action.is_negated:
                logger.info("[CompositeExecutor] Step %d is explicitly negated ('%s'). Skipping execution.", step_num, action.raw_text)
                step_results.append({
                    "step": step_num,
                    "intent": action.intent,
                    "status": "skipped_negated",
                    "message": f"Step {step_num} skipped (negated by user request: '{action.raw_text}').",
                })
                continue

            # Check dependencies: if a prerequisite failed, do not blindly execute dependent steps (Requirement 12)
            has_failed_dep = any(dep == failed_step_order for dep in action.depends_on)
            if has_failed_dep:
                logger.warning("[CompositeExecutor] Step %d skipped because prerequisite step %d failed.", step_num, failed_step_order)
                step_results.append({
                    "step": step_num,
                    "intent": action.intent,
                    "status": "skipped_dependency",
                    "message": f"Step {step_num} skipped due to failure of prerequisite step {failed_step_order}.",
                })
                overall_success = False
                continue

            # Execute Step via canonical SideEffectBarrier
            step_ok, step_output = cls._execute_single_action(action)

            # Verify with ActionVerifier (Requirement 12)
            verification = ActionVerifier.verify_action(
                action.action_type or action.intent,
                action.parameters,
                step_output,
            )

            if step_ok and verification.verified:
                step_results.append({
                    "step": step_num,
                    "intent": action.intent,
                    "status": "completed",
                    "output": step_output,
                    "message": f"Step {step_num} completed: {step_output}",
                })
            else:
                overall_success = False
                failed_step_order = step_num
                err_detail = verification.error or verification.details or step_output
                step_results.append({
                    "step": step_num,
                    "intent": action.intent,
                    "status": "failed",
                    "output": step_output,
                    "message": f"Step {step_num} failed: {err_detail}",
                })
                logger.warning("[CompositeExecutor] Step %d (%s) failed verification: %s", step_num, action.intent, err_detail)

        t_end = time.time()
        trace.execution_completed = t_end
        trace.success = overall_success
        trace.details["step_results"] = step_results
        IntentTraceStore.record(trace)

        # Build Truthful Final Response (Requirements 13, 22, 28)
        response_lines: List[str] = []
        if intro_text:
            response_lines.append(intro_text.strip())
            response_lines.append("")

        for res in step_results:
            st = res.get("status")
            msg = res.get("message", "")
            if st == "completed":
                response_lines.append(f"✅ {msg}")
            elif st == "failed":
                response_lines.append(f"❌ {msg}")
            elif st == "skipped_negated":
                response_lines.append(f"🚫 {msg}")
            elif st == "skipped_dependency":
                response_lines.append(f"⚠️ {msg}")

        summary = "\n".join(response_lines)

        return {
            "executed": True,
            "status": "completed" if overall_success else "partial" if any(r.get("status") == "completed" for r in step_results) else "failed",
            "result": summary,
            "step_results": step_results,
            "trace": trace.to_dict(),
        }

    @classmethod
    def _execute_single_action(cls, action: Any, engine: Any = None) -> Tuple[bool, str]:
        """Dispatch a single structured action through the canonical SideEffectBarrier."""
        from brjarvis.core.intent_models import AuthorizedActionPlan, ProposedAction, RiskLevel
        from brjarvis.core.side_effect_barrier import SideEffectBarrier

        intent = getattr(action, "intent", str(action))
        params = getattr(action, "parameters", {})

        try:
            prop_action = ProposedAction(
                action_id=f"act_comp_{uuid.uuid4().hex[:8]}",
                intent=intent,
                tool="native_os",
                parameters=dict(params),
                raw_text=getattr(action, "raw_text", intent),
                order=getattr(action, "order", 1),
                risk_level=RiskLevel.LOW,
            )

            auth_plan = AuthorizedActionPlan(
                plan_id=f"plan_comp_{uuid.uuid4().hex[:8]}",
                authorized=True,
                actions=[prop_action],
                authorization_token=f"auth_comp_{uuid.uuid4().hex[:10]}",
            )

            rec = SideEffectBarrier.execute(
                action=prop_action,
                auth_plan=auth_plan,
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                request_id=f"req_comp_{uuid.uuid4().hex[:8]}",
            )

            if rec.status == "COMPLETED":
                if rec.observation and isinstance(rec.observation, dict):
                    if "cpu_percent" in rec.observation:
                        return True, f"System Properties & Diagnostics:\nCPU {rec.observation['cpu_percent']}%, RAM {rec.observation.get('ram_percent', 0)}%"
                    if "url" in rec.observation:
                        return True, f"Opened {rec.observation['url']} in browser"
                    if "target" in rec.observation:
                        return True, f"Launched {rec.observation['target']}"
                return True, f"Successfully executed {intent}"
            return False, rec.error or f"Failed to execute {intent}"

        except Exception as exc:
            logger.error("[CompositeExecutor] Exception executing action %s: %s", intent, exc)
            return False, str(exc)

