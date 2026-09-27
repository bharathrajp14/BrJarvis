# core/canonical_runtime.py — Master Canonical Request Runtime Engine
"""
Master Canonical Request Runtime Engine for BR JARVIS.
Serves as the single unified convergence entry point across CLI, Web, Voice,
Desktop, Orchestrator, AgentLoop, and Background tasks.

Enforces the full lifecycle:
  PERCEPTION -> NORMALIZATION -> SAFETY CLASSIFICATION -> FULL INTENT UNDERSTANDING ->
  INTENT ARBITRATION -> ATOMICITY ANALYSIS -> ACTION PLAN -> ACTION AUTHORIZATION ->
  EXECUTION -> OBSERVATION -> VERIFICATION -> NEXT STEP -> COMPLETION
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional

from brjarvis.core.action_authorization import ActionAuthorizationEngine
from brjarvis.core.intent_models import (
    ActionExecutionRecord,
    ActionPlan,
    AtomicityType,
    AuthorizedActionPlan,
    ExecutionState,
    RequestResult,
    RequestUnderstanding,
)
from brjarvis.core.request_understanding import RequestUnderstandingEngine
from brjarvis.core.side_effect_barrier import SideEffectBarrier

logger = logging.getLogger("JARVIS.CanonicalRequestRuntime")


@dataclass
class CanonicalRuntimeResponse:
    """Standardized response from CanonicalRequestRuntime.handle()."""

    text: str
    state: ExecutionState
    understanding: RequestUnderstanding
    plan: Optional[ActionPlan] = None
    authorized_plan: Optional[AuthorizedActionPlan] = None
    records: List[ActionExecutionRecord] = field(default_factory=list)
    low_latency_execution: bool = False
    latency_ms: float = 0.0
    error: Optional[str] = None
    task_id: str = ""
    provider_usage: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    memory_updates: Dict[str, Any] = field(default_factory=dict)

    @property
    def fast_path(self) -> bool:
        """Backward-compatibility alias for low_latency_execution."""
        return self.low_latency_execution

    @property
    def request_id(self) -> str:
        return self.understanding.request_id

    @property
    def response(self) -> str:
        return self.text

    @property
    def actions(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]

    @property
    def execution_trace(self) -> Dict[str, Any]:
        return {
            "request_id": self.understanding.request_id,
            "task_id": self.task_id,
            "status": self.state.value,
            "action_count": len(self.records),
            "latency_ms": self.latency_ms,
        }

    @property
    def verification(self) -> Dict[str, Any]:
        return {
            "verified": all(r.status == "COMPLETED" for r in self.records) if self.records else True,
            "records_verified": [r.action_id for r in self.records if r.status == "COMPLETED"],
        }

    def to_result(self) -> RequestResult:
        """Converts to the canonical RequestResult data contract."""
        return RequestResult(
            request_id=self.understanding.request_id,
            task_id=self.task_id or f"task_{self.understanding.request_id[-8:]}",
            status=self.state.value,
            response=self.text,
            actions=[r.to_dict() for r in self.records],
            execution_trace=self.execution_trace,
            verification=self.verification,
            artifacts=self.artifacts,
            memory_updates=self.memory_updates,
            latency_ms=self.latency_ms,
            provider_usage=self.provider_usage,
            error=self.error,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "state": self.state.value,
            "understanding": self.understanding.to_dict(),
            "plan": self.plan.to_dict() if self.plan else None,
            "authorized_plan": self.authorized_plan.to_dict() if self.authorized_plan else None,
            "records": [r.to_dict() for r in self.records],
            "low_latency_execution": self.low_latency_execution,
            "fast_path": self.low_latency_execution,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "request_id": self.request_id,
            "task_id": self.task_id,
        }


class CanonicalRequestRuntime:
    """
    Authoritative Universal Runtime governing all request understanding,
    authorization, execution, and verification in BR JARVIS.
    """

    CANCELLATION_COMMANDS = {
        "cancel", "stop", "abort", "pause", "never mind", "nevermind",
        "don't continue", "dont continue", "halt",
    }

    @classmethod
    def _notify_status(
        cls,
        status_callback: Optional[Callable[[str, Dict[str, Any]], None]],
        phase: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Helper to invoke optional streaming status callback."""
        if status_callback:
            try:
                status_callback(phase, data or {})
            except Exception as e:
                logger.debug("[CanonicalRuntime] Status callback notice: %s", e)

    @classmethod
    def handle(
        cls,
        user_input: str,
        streaming_status: str = "input_final",
        context: Optional[Dict[str, Any]] = None,
        surface: str = "orchestrator",
        policy: str = "auto",
        orchestrator: Optional[Any] = None,
        status_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> CanonicalRuntimeResponse:
        """
        Master canonical entry point for all user requests.
        Ensures identical semantic understanding and execution governance across all surfaces.
        """
        t0 = time.time()
        ctx = context or {}
        raw_text = (user_input or "").strip()
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # ── Step 0: Immediate Cancellation / Interrupt Check ─────────────────
        if raw_text.lower() in cls.CANCELLATION_COMMANDS:
            logger.info("[CanonicalRuntime] User interrupt received: %s", raw_text)
            cls._notify_status(status_callback, "CANCELLED", {"raw_input": raw_text})
            understanding = RequestUnderstanding(
                request_id=f"req_{uuid.uuid4().hex[:10]}",
                raw_input=raw_text,
                normalized_input=raw_text.lower(),
                atomicity=AtomicityType.NEGATED,
                confidence=1.0,
                completeness_score=1.0,
            )
            return CanonicalRuntimeResponse(
                text="Task execution cancelled. Pending operations halted.",
                state=ExecutionState.CANCELLED,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 1-4: Perception, Normalization, Safety & Full Understanding ──
        cls._notify_status(status_callback, "UNDERSTANDING", {"raw_input": raw_text})
        understanding = RequestUnderstandingEngine.understand(
            raw_input=raw_text,
            streaming_status=streaming_status,
            context=ctx,
        )

        logger.info(
            "[CanonicalRuntime] Request '%s' understood: atomicity=%s, actions=%d, low_latency_eligible=%s",
            understanding.request_id,
            understanding.atomicity.value,
            understanding.action_count,
            understanding.deterministic_eligible,
        )

        # ── Step 5: Streaming Perception Incomplete Guard ──────────────────────
        if streaming_status != "input_final":
            return CanonicalRuntimeResponse(
                text="Listening...",
                state=ExecutionState.UNDERSTANDING,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 6: Clarification Gate for Ambiguity ───────────────────────────
        if understanding.requires_clarification or understanding.atomicity == AtomicityType.AMBIGUOUS:
            return CanonicalRuntimeResponse(
                text="I'm not sure which target you are referring to. Please specify the exact application, file, or destination.",
                state=ExecutionState.WAITING_FOR_APPROVAL,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 7: Informational / Question Guard ────────────────────────────
        if understanding.atomicity == AtomicityType.INFORMATIONAL:
            # Informational requests must never trigger side effects
            return CanonicalRuntimeResponse(
                text=f"Informational query received: '{understanding.normalized_input}'. To open or control applications, state the direct command (e.g. 'open Excel').",
                state=ExecutionState.COMPLETED,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 8: Hypothetical Request Guard ─────────────────────────────────
        if understanding.atomicity == AtomicityType.HYPOTHETICAL:
            # Hypothetical requests must not produce physical side effects
            return CanonicalRuntimeResponse(
                text=f"[Simulation Mode] Hypothetically evaluating: '{understanding.normalized_input}'. No real system actions were performed.",
                state=ExecutionState.COMPLETED,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 9: Negated Request Guard ──────────────────────────────────────
        if understanding.atomicity == AtomicityType.NEGATED:
            return CanonicalRuntimeResponse(
                text=f"Action negated: Skipped '{understanding.normalized_input}' as requested.",
                state=ExecutionState.COMPLETED,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 10: Conversational Guard ──────────────────────────────────────
        if understanding.atomicity == AtomicityType.CONVERSATIONAL:
            return CanonicalRuntimeResponse(
                text="Hello! How can I assist you with your system or tasks today, Sir?",
                state=ExecutionState.COMPLETED,
                understanding=understanding,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 11: Action Plan DAG Construction ─────────────────────────────
        cls._notify_status(status_callback, "PLANNING", {"understanding": understanding.to_dict()})
        plan = ActionAuthorizationEngine.build_plan_from_understanding(understanding)

        # ── Step 12: Action Authorization ─────────────────────────────────────
        auth_plan = ActionAuthorizationEngine.authorize(plan, policy=policy, context=ctx)
        if not auth_plan.authorized:
            reasons = "; ".join(auth_plan.denial_reasons) or "Plan authorization denied"
            return CanonicalRuntimeResponse(
                text=f"Action authorization declined: {reasons}",
                state=ExecutionState.FAILED,
                understanding=understanding,
                plan=plan,
                authorized_plan=auth_plan,
                error=reasons,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        if auth_plan.requires_user_approval and not auth_plan.approval_granted:
            return CanonicalRuntimeResponse(
                text=f"Action requires confirmation: {plan.original_text}",
                state=ExecutionState.WAITING_FOR_APPROVAL,
                understanding=understanding,
                plan=plan,
                authorized_plan=auth_plan,
                task_id=task_id,
                latency_ms=(time.time() - t0) * 1000,
            )

        # ── Step 13: Execution Phase ──────────────────────────────────────────
        cls._notify_status(status_callback, "EXECUTING", {"plan_id": auth_plan.plan_id, "actions": len(auth_plan.actions)})
        records: List[ActionExecutionRecord] = []
        overall_state = ExecutionState.COMPLETED
        step_outputs: List[str] = []

        completed_action_ids: set[str] = set()

        for action in auth_plan.actions:
            # Check dependencies
            unsatisfied = [dep for dep in action.depends_on if dep not in completed_action_ids]
            if unsatisfied:
                logger.warning(
                    "[CanonicalRuntime] Skipping action %s because dependencies %s failed or were skipped",
                    action.action_id, unsatisfied,
                )
                rec = ActionExecutionRecord(
                    request_id=understanding.request_id,
                    task_id=task_id,
                    action_id=action.action_id,
                    intent=action.intent,
                    tool=action.tool,
                    authorization=True,
                    status="SKIPPED",
                    error=f"Unsatisfied dependencies: {unsatisfied}",
                )
                records.append(rec)
                overall_state = ExecutionState.PARTIAL
                continue

            # Execute through SideEffectBarrier (EXECUTE -> OBSERVE -> VERIFY -> RECORD)
            cls._notify_status(status_callback, "EXECUTING", {"action_id": action.action_id, "intent": action.intent})
            rec = SideEffectBarrier.execute(
                action=action,
                auth_plan=auth_plan,
                task_id=task_id,
                request_id=understanding.request_id,
            )
            records.append(rec)

            cls._notify_status(status_callback, "VERIFYING", {"action_id": action.action_id, "status": rec.status})

            if rec.status == "COMPLETED":
                completed_action_ids.add(action.action_id)
                step_desc = f"Action {action.order} ({action.intent}): Success"
                if rec.observation and isinstance(rec.observation, dict):
                    if "cpu_percent" in rec.observation:
                        step_desc = f"System Diagnostics: CPU {rec.observation['cpu_percent']}%, RAM {rec.observation.get('ram_percent', 0)}%"
                    elif "url" in rec.observation:
                        step_desc = f"Opened {rec.observation['url']} in browser"
                    elif "target" in rec.observation:
                        step_desc = f"Launched {rec.observation['target']}"
                step_outputs.append(step_desc)
            else:
                overall_state = ExecutionState.PARTIAL if len(completed_action_ids) > 0 else ExecutionState.FAILED
                step_outputs.append(f"Action {action.order} ({action.intent}): FAILED — {rec.error}")

        # Build Truthful Execution Response without false token claims
        low_latency = (understanding.deterministic_eligible and len(records) == 1 and records[0].status == "COMPLETED")
        if overall_state == ExecutionState.COMPLETED:
            if low_latency:
                resp_text = f"{step_outputs[0]} (Verified)"
            else:
                resp_text = f"Executed {len(completed_action_ids)} actions successfully:\n" + "\n".join(f"• {s}" for s in step_outputs)
        elif overall_state == ExecutionState.PARTIAL:
            resp_text = (
                f"Partial task execution: Completed {len(completed_action_ids)} of {len(auth_plan.actions)} steps.\n"
                + "\n".join(f"• {s}" for s in step_outputs)
            )
        else:
            resp_text = "Task execution failed.\n" + "\n".join(f"• {s}" for s in step_outputs)

        elapsed_ms = (time.time() - t0) * 1000
        cls._notify_status(status_callback, "COMPLETED", {"state": overall_state.value, "latency_ms": elapsed_ms})

        return CanonicalRuntimeResponse(
            text=resp_text,
            state=overall_state,
            understanding=understanding,
            plan=plan,
            authorized_plan=auth_plan,
            records=records,
            low_latency_execution=low_latency,
            task_id=task_id,
            latency_ms=elapsed_ms,
        )

    @classmethod
    def stream_handle(
        cls,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        surface: str = "orchestrator",
        policy: str = "auto",
        orchestrator: Optional[Any] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Streaming generator version of CanonicalRequestRuntime.handle().
        Yields structured status events: UNDERSTANDING -> PLANNING -> EXECUTING -> VERIFYING -> COMPLETED.
        """
        events: List[Dict[str, Any]] = []

        def capture(phase: str, data: Dict[str, Any]):
            events.append({"phase": phase, "data": data, "timestamp": time.time()})

        # Yield understanding event start
        yield {"type": "status", "phase": "UNDERSTANDING", "timestamp": time.time()}

        res = cls.handle(
            user_input=user_input,
            context=context,
            surface=surface,
            policy=policy,
            orchestrator=orchestrator,
            status_callback=capture,
        )

        for ev in events:
            if ev["phase"] not in ("UNDERSTANDING", "COMPLETED"):
                yield {"type": "status", "phase": ev["phase"], "data": ev["data"], "timestamp": ev["timestamp"]}

        yield {
            "type": "result",
            "phase": "COMPLETED",
            "result": res.to_result().to_dict(),
            "timestamp": time.time(),
        }

    @classmethod
    def handle_deterministic_shortcut(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Backward compatibility entry point for legacy callers.
        Routes through full understanding, atomicity, authorization, and verification.
        Zero-token execution has been removed; returns truthful performance metadata.
        """
        response = cls.handle(text, surface="low_latency")
        if response.low_latency_execution and response.state == ExecutionState.COMPLETED and response.records:
            rec = response.records[0]
            return {
                "executed": True,
                "intent": rec.intent,
                "target": rec.parameters.get("app_name") or rec.parameters.get("verb", "action"),
                "result": response.text,
                "latency_ms": response.latency_ms,
                "verified": True,
                "records": [r.to_dict() for r in response.records],
            }
        return None
