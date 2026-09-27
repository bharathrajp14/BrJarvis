# agent/executor_engine.py — Multi-Worker Parallel Execution Engine for BR JARVIS
from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from brjarvis.core.runtime import get_runtime
from brjarvis.events.bus import get_event_bus
from brjarvis.events.types import TaskEvent
from brjarvis.security.permissions import ActionDecision, RiskLevel, evaluate_action_policy

from .task_state import get_task_state_manager
from .types import ExecutionReport, GoalGraph, StepStatus, TaskStepNode

logger = logging.getLogger("JARVIS.ExecutorEngine")


class ParallelExecutionEngine:
    """Multi-Worker Parallel Task Execution Engine with WAL Persistence & Safety Interlocks."""

    def __init__(self, max_workers: Optional[int] = None):
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()
        self.task_state_mgr = get_task_state_manager()
        self.max_workers = max_workers or self.runtime.config.system.max_workers
        self._cancelled = False

        # Register self in DI container
        self.runtime.container.register_instance(ParallelExecutionEngine, self)
        logger.info("⚡ ParallelExecutionEngine initialized with %d parallel workers", self.max_workers)

    def cancel_all(self) -> None:
        """Emergency stop: Cancel all active and queued goal executions."""
        self._cancelled = True
        logger.warning("🛑 Emergency Stop Signal Issued: Cancelling ExecutionEngine")

    async def execute_step(
        self,
        step: TaskStepNode,
        tool_resolver_fn: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
        task_id: Optional[str] = None,
    ) -> TaskStepNode:
        """Execute a single DAG task step with safety interlock, WAL logging, and retry backoff."""
        if self._cancelled:
            step.status = StepStatus.CANCELLED
            return step

        tid = task_id or "task_default"

        # 1. Deterministic Security Policy Evaluation
        risk_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }
        step_risk = risk_map.get(getattr(step.risk_level, "value", "low").lower(), RiskLevel.LOW)
        policy_decision = evaluate_action_policy(
            action=step.tool,
            resource=str(step.parameters.get("path") or step.parameters.get("TargetFile") or ""),
            risk=step_risk,
            args=step.parameters,
        )

        # 2. Human-in-the-Loop Approval Interlock
        from brjarvis.security.permissions import PERMISSIONS, PermissionMode

        env_mode = os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower()
        is_allow_all = (
            PERMISSIONS.mode == PermissionMode.ALLOW_ALL
            or env_mode in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall")
            or policy_decision in (ActionDecision.ALLOW, ActionDecision.ALLOW_FOR_SESSION)
        )
        if (
            (not is_allow_all)
            and (step.requires_approval or policy_decision == ActionDecision.CONFIRM)
            and step.status != StepStatus.SUCCESS
        ):
            step.status = StepStatus.WAITING_FOR_APPROVAL
            logger.warning(
                "⚠️ Human Approval Interlock: Step #%s [%s] requires confirmation!", step.step_id, step.description
            )

            # Record approval gate in TaskStateManager
            self.task_state_mgr.request_approval(
                task_id=tid,
                action_id=str(step.step_id),
                description=step.description,
                risk_level=step_risk.value,
                details={"tool": step.tool, "parameters": step.parameters},
            )

            self.event_bus.publish(
                TaskEvent(
                    topic="task.step.approval_required",
                    task_id=str(step.step_id),
                    goal=step.description,
                    status="WAITING_FOR_APPROVAL",
                    payload={"tool": step.tool, "risk_level": step_risk.value},
                )
            )
            return step

        if policy_decision == ActionDecision.DENY:
            step.status = StepStatus.FAILED
            step.error = f"Policy Denied: Action '{step.tool}' blocked by security rules."
            logger.error("❌ Step #%s Denied by Policy Engine", step.step_id)
            return step

        # 3. WAL Log: Step Start
        self.task_state_mgr.record_step_wal(
            task_id=tid, step_index=step.step_id, capability=step.tool, parameters=step.parameters, status="in_progress"
        )

        step.status = StepStatus.IN_PROGRESS
        step.start_time = time.time()

        self.event_bus.publish(
            TaskEvent(topic="task.step.start", task_id=str(step.step_id), goal=step.description, status="IN_PROGRESS")
        )

        # 4. Step Execution Loop with Exponential Backoff Retries
        max_retries = 2 if not step.critical else 1
        attempt = 0
        last_error = None

        while attempt <= max_retries:
            try:
                logger.info(
                    "▶ Executing Step #%s (Attempt %d): %s (Tool: %s)",
                    step.step_id,
                    attempt + 1,
                    step.description,
                    step.tool,
                )

                # Execute tool via provided resolver or fallback to canonical ToolRuntime
                if tool_resolver_fn:
                    if inspect.iscoroutinefunction(tool_resolver_fn):
                        res = await asyncio.wait_for(tool_resolver_fn(step.tool, step.parameters), timeout=60.0)
                    else:
                        res = await asyncio.to_thread(tool_resolver_fn, step.tool, step.parameters)
                    step.result = res.data if hasattr(res, "data") and res.data is not None else res
                else:
                    from brjarvis.tools.runtime import get_canonical_tool_runtime

                    tool_res = await get_canonical_tool_runtime().execute_tool_async(
                        name=step.tool,
                        args=step.parameters,
                        task_id=tid,
                        step_id=f"step_{step.step_id}",
                    )
                    step.result = tool_res.data if tool_res.data is not None else tool_res.output
                    if not tool_res.success:
                        raise RuntimeError(tool_res.error or f"Tool '{step.tool}' execution failed.")

                step.status = StepStatus.SUCCESS
                step.end_time = time.time()
                step_duration = step.end_time - (step.start_time or step.end_time)

                # WAL Log: Step Success
                self.task_state_mgr.record_step_wal(
                    task_id=tid,
                    step_index=step.step_id,
                    capability=step.tool,
                    parameters=step.parameters,
                    status="completed",
                    result=step.result,
                    duration=step_duration,
                    verified=True,
                )

                self.event_bus.publish(
                    TaskEvent(
                        topic="task.step.completed",
                        task_id=str(step.step_id),
                        goal=step.description,
                        status="SUCCESS",
                        payload={"result": str(step.result)},
                    )
                )
                return step

            except Exception as e:
                attempt += 1
                last_error = e
                logger.warning("⚠️ Step #%s Attempt %d failed: %s", step.step_id, attempt, e)
                if attempt <= max_retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)

        # Step Failure after all retries
        step.status = StepStatus.FAILED
        step.error = str(last_error)
        step.end_time = time.time()
        step_duration = step.end_time - (step.start_time or step.end_time)
        logger.error("❌ Step #%s Failed Permanently: %s", step.step_id, last_error)

        # WAL Log: Step Failure
        self.task_state_mgr.record_step_wal(
            task_id=tid,
            step_index=step.step_id,
            capability=step.tool,
            parameters=step.parameters,
            status="failed",
            error=str(last_error),
            duration=step_duration,
        )

        self.event_bus.publish(
            TaskEvent(
                topic="task.step.failed",
                task_id=str(step.step_id),
                goal=step.description,
                status="FAILED",
                payload={"error": str(last_error)},
            )
        )

        return step

    async def execute_graph(
        self,
        graph: GoalGraph,
        tool_resolver_fn: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
        task_id: Optional[str] = None,
    ) -> ExecutionReport:
        """Execute an entire GoalGraph DAG respecting step dependencies, WAL, and parallelism."""
        self._cancelled = False
        start_t = time.time()
        completed_count = 0
        total_steps = len(graph.steps)
        tid = task_id or graph.goal_id or f"goal_{int(start_t)}"

        logger.info("🚀 Executing GoalGraph [%s] (%d steps, Task ID: %s)", graph.goal, total_steps, tid)

        # DAG resolution loop
        while completed_count < total_steps and not self._cancelled:
            ready_steps = [
                s
                for s in graph.steps
                if s.status == StepStatus.PENDING
                and all(graph.steps[dep - 1].status == StepStatus.SUCCESS for dep in s.depends_on)
            ]

            if not ready_steps:
                # Check for failed or blocked steps
                if any(s.status == StepStatus.FAILED for s in graph.steps):
                    break
                if any(s.status == StepStatus.WAITING_FOR_APPROVAL for s in graph.steps):
                    logger.info("⏸ Graph execution paused waiting for user approval.")
                    break
                # No progress possible
                break

            # Execute ready steps (parallel workers up to max_workers)
            batch = ready_steps[: self.max_workers]
            tasks = [self.execute_step(step, tool_resolver_fn, task_id=tid) for step in batch]
            results = await asyncio.gather(*tasks)

            for step in results:
                if step.status == StepStatus.SUCCESS:
                    completed_count += 1
                elif step.status == StepStatus.FAILED and step.critical:
                    logger.error("Critical Step #%s failed. Halting graph execution.", step.step_id)
                    break

        duration = time.time() - start_t
        overall_status = "SUCCESS" if completed_count == total_steps else "PARTIAL" if completed_count > 0 else "FAILED"

        return ExecutionReport(
            goal_id=graph.goal_id,
            status=overall_status,
            completed_steps=completed_count,
            total_steps=total_steps,
            duration_s=duration,
        )


_global_executor_engine: Optional[ParallelExecutionEngine] = None


def get_executor_engine() -> ParallelExecutionEngine:
    global _global_executor_engine
    if _global_executor_engine is None:
        _global_executor_engine = ParallelExecutionEngine()
    return _global_executor_engine
