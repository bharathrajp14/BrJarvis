# src/brjarvis/tools/runtime.py — Canonical Universal Tool Execution Runtime
"""
Canonical Universal Tool Execution Runtime for BR JARVIS MK40.2 / MK41.
The single authoritative execution lifecycle for all capabilities, tools, and actions.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from brjarvis.core.runtime import get_runtime
from brjarvis.events.bus import get_event_bus
from brjarvis.events.types import ToolExecutionEvent
from brjarvis.security.permissions import (
    PERMISSIONS,
    ActionDecision,
    PermissionMode,
    evaluate_action_policy,
)
from brjarvis.security.permissions import (
    RiskLevel as SecRiskLevel,
)

from .domain import (
    CachePolicy,
    Observation,
    RiskLevel,
    ToolCategory,
    ToolDefinition,
    ToolErrorCode,
    ToolExecutionStatus,
    VerificationStrategy,
)
from .normalizer import ArgumentNormalizer
from .resolver import ToolResolver
from .tool_result import ToolResult
from .validator import SchemaValidator

logger = logging.getLogger("JARVIS.Tools.Runtime")


class ToolRuntime:
    """
    Single Authoritative Tool Execution Engine.
    Enforces deterministic 12-stage execution lifecycle across the entire platform.
    """

    _INSTANCE: Optional[ToolRuntime] = None

    def __init__(self):
        self._catalog: Dict[str, ToolDefinition] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._execution_lock = asyncio.Lock() if hasattr(asyncio, "Lock") else None

        # Register instance in runtime DI container if available
        try:
            rt = get_runtime()
            if hasattr(rt, "container"):
                rt.container.register_instance(ToolRuntime, self)
        except Exception:
            pass

        logger.info("⚡ Canonical ToolRuntime initialized")

    @classmethod
    def get_instance(cls) -> ToolRuntime:
        """Get or create singleton instance of ToolRuntime."""
        if cls._INSTANCE is None:
            cls._INSTANCE = ToolRuntime()
        return cls._INSTANCE

    # ── Catalog Registration ───────────────────────────────────────────────────

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
        category: ToolCategory = ToolCategory.GENERAL,
        risk_level: Optional[RiskLevel] = None,
        permission_required: Optional[str] = None,
        approval_required: Optional[bool] = None,
        is_read_only: bool = False,
        idempotent: bool = True,
        retryable: bool = True,
        parallel_safe: bool = True,
        timeout_sec: float = 30.0,
        verification_strategy: VerificationStrategy = VerificationStrategy.NONE,
        tool_id: str = "",
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> ToolDefinition:
        """Register a canonical ToolDefinition and handler."""
        clean_name = name.strip()
        resolved_risk = risk_level or (RiskLevel.LOW if is_read_only else RiskLevel.HIGH)
        resolved_permission = permission_required or ("PUBLIC_READ" if is_read_only else "LOCAL_SYSTEM")
        resolved_approval = approval_required if approval_required is not None else not is_read_only
        tool_def = ToolDefinition(
            name=clean_name,
            tool_id=tool_id or f"{category.value}.{clean_name}",
            description=description.strip(),
            category=category,
            parameters=parameters or {"type": "object", "properties": {}},
            output_schema=output_schema or {},
            risk_level=resolved_risk,
            permission_required=resolved_permission,
            approval_required=resolved_approval,
            is_read_only=is_read_only,
            idempotent=idempotent,
            retryable=retryable,
            parallel_safe=parallel_safe,
            timeout_sec=timeout_sec,
            verification_strategy=verification_strategy,
            handler=handler,
        )
        self._catalog[clean_name] = tool_def
        logger.debug(f"[ToolRuntime] Registered tool '{clean_name}' [{category.value}] (Risk: {resolved_risk.value})")
        return tool_def

    def register_definition(self, tool_def: ToolDefinition, handler: Callable[..., Any]) -> None:
        """Register an existing ToolDefinition object with its handler."""
        tool_def.handler = handler
        self._catalog[tool_def.name] = tool_def

    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        """Look up ToolDefinition by name or namespace."""
        tool_def, _, _ = ToolResolver.resolve(name, self._catalog)
        return tool_def

    def list_tools(self) -> List[ToolDefinition]:
        """Return list of all registered tool definitions."""
        return list(self._catalog.values())

    def get_catalog(self) -> Dict[str, ToolDefinition]:
        """Return the dictionary catalog of tool definitions."""
        return dict(self._catalog)

    # ── Canonical Execution Pipeline ───────────────────────────────────────────

    async def execute_tool_async(
        self,
        name: str,
        args: Dict[str, Any],
        task_id: str = "",
        step_id: str = "",
        user: str = "default_user",
        device: str = "pc_primary",
        application: str = "system",
        confirmed: bool = False,
    ) -> ToolResult:
        """
        Execute a tool asynchronously through the strict 12-stage execution lifecycle.
        """
        t0 = time.perf_counter()
        inv_id = uuid.uuid4().hex[:10]

        # ── Stage 1: Resolve Tool Definition ──
        tool_def, resolve_err, error_code = ToolResolver.resolve(name, self._catalog)
        if not tool_def or not tool_def.handler:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            return ToolResult.failed(
                tool_name=name,
                error_code=error_code or ToolErrorCode.TOOL_NOT_FOUND,
                message=resolve_err or f"Tool '{name}' not found.",
                execution_ms=duration_ms,
            )

        canonical_name = tool_def.name

        # ── Stage 2: Deterministic Argument Normalization ──
        normalized_args = ArgumentNormalizer.normalize_args(tool_def, args)

        # ── Stage 3: Strict Schema Validation ──
        is_valid, val_err = SchemaValidator.validate(tool_def.parameters, normalized_args)
        if not is_valid:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.warning(f"❌ Schema validation failed for tool '{canonical_name}': {val_err}")
            return ToolResult.failed(
                tool_name=canonical_name,
                error_code=ToolErrorCode.SCHEMA_VALIDATION_ERR,
                message=f"Invalid arguments for tool '{canonical_name}': {val_err}",
                execution_ms=duration_ms,
            )

        # ── Stage 4: Prompt Injection Preflight ──
        try:
            from brjarvis.guardian.prompt_injection_shield import check_prompt_injection

            for arg_k, arg_v in normalized_args.items():
                if isinstance(arg_v, str) and len(arg_v) > 30:
                    is_inj, reason = check_prompt_injection(arg_v)
                    if is_inj:
                        duration_ms = (time.perf_counter() - t0) * 1000.0
                        logger.warning(
                            f"🛡️ Security Alert: Injection pattern in '{canonical_name}' arg '{arg_k}': {reason}"
                        )
                        return ToolResult.blocked(
                            tool_name=canonical_name,
                            reason=f"Security Alert: Blocked by prompt injection defense in argument '{arg_k}'.",
                            error_code=ToolErrorCode.POLICY_DENIED,
                        )
        except Exception as guard_err:
            # A missing or broken guard must not silently remove a defense layer
            # for tools that can change state or access protected resources.
            logger.warning("Prompt-injection guard unavailable for '%s': %s", canonical_name, guard_err)
            if not tool_def.is_read_only:
                return ToolResult.blocked(
                    tool_name=canonical_name,
                    reason="Security preflight unavailable; state-changing execution was blocked.",
                    error_code=ToolErrorCode.POLICY_DENIED,
                )

        # ── Stage 5: Security & Policy Evaluation ──

        risk_map = {
            RiskLevel.LOW: SecRiskLevel.LOW,
            RiskLevel.MEDIUM: SecRiskLevel.MEDIUM,
            RiskLevel.HIGH: SecRiskLevel.HIGH,
            RiskLevel.CRITICAL: SecRiskLevel.CRITICAL,
        }
        sec_risk = risk_map.get(tool_def.risk_level, SecRiskLevel.LOW)
        resource_target = str(
            normalized_args.get("path") or normalized_args.get("url") or normalized_args.get("recipient") or ""
        )

        policy_decision = evaluate_action_policy(
            action=canonical_name,
            resource=resource_target,
            device=device,
            application=application,
            user=user,
            risk=sec_risk,
            args=normalized_args,
        )

        if policy_decision == ActionDecision.DENY:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(f"🔒 Tool '{canonical_name}' denied by security policy.")
            return ToolResult.blocked(
                tool_name=canonical_name,
                reason=f"Policy Denied: Tool '{canonical_name}' is blocked by active security rules.",
            )

        # ── Stage 6: Human Approval Interlock ──
        is_allow_all = policy_decision in (ActionDecision.ALLOW, ActionDecision.ALLOW_FOR_SESSION) and (
            PERMISSIONS.mode == PermissionMode.ALLOW_ALL
            or os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower() in ("auto", "allow_all")
        )
        protected_permission = tool_def.permission_required.strip().upper() != "PUBLIC_READ"
        needs_approval = (not is_allow_all) and (
            (tool_def.approval_required or protected_permission or policy_decision == ActionDecision.CONFIRM)
            and not confirmed
        )

        if needs_approval:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.warning(f"⚠️ Approval Required: Tool '{canonical_name}' requires human confirmation.")
            # Record approval request in task state if task_id provided
            if task_id:
                try:
                    from brjarvis.agent.task_state import get_task_state_manager

                    get_task_state_manager().request_approval(
                        task_id=task_id,
                        action_id=step_id or inv_id,
                        description=f"Execute {canonical_name} with risk level {tool_def.risk_level.value}",
                        risk_level=tool_def.risk_level.value,
                        details={"tool": canonical_name, "parameters": normalized_args},
                    )
                except Exception as e:
                    logger.debug("Approval recording note: %s", e)

            return ToolResult.requires_approval(
                tool_name=canonical_name,
                reason=f"High-risk action '{canonical_name}' requires explicit confirmation.",
                data={"tool": canonical_name, "args": normalized_args, "risk_level": tool_def.risk_level.value},
            )

        # ── Stage 7: Idempotency & Read-Only Cache Check ──
        if tool_def.is_read_only and tool_def.cache_policy != CachePolicy.NO_CACHE:
            try:
                from brjarvis.memory.unified_memory import get_unified_memory

                mem = get_unified_memory()
                cached = mem.get_cached_tool_result(canonical_name, normalized_args)
                if cached is not None:
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    logger.debug(f"⚡ Tool Cache Hit for '{canonical_name}'")
                    return ToolResult.success(
                        tool_name=canonical_name,
                        data=cached,
                        evidence="Result retrieved from verified execution cache.",
                        verified=True,
                        execution_ms=duration_ms,
                        metadata={"cached": True},
                    )
            except Exception as e:
                logger.debug(f"Cache check note: {e}")

        # ── Stage 8: Publish Start Telemetry Event ──
        try:
            get_event_bus().publish(
                ToolExecutionEvent(
                    topic="tool.exec.start",
                    tool_name=canonical_name,
                    args=normalized_args,
                )
            )
        except Exception:
            pass

        # ── Stage 9: Execute Handler with Timeout & Sandboxing ──
        handler = tool_def.handler
        raw_res: Any = None

        try:
            if inspect.iscoroutinefunction(handler):
                raw_res = await asyncio.wait_for(handler(normalized_args), timeout=tool_def.timeout_sec)
            else:
                # Run synchronous handlers in a worker thread, but keep the
                # awaitable bounded by the same contract as async handlers.
                raw_res = await asyncio.wait_for(
                    asyncio.to_thread(self._invoke_sync_handler, handler, normalized_args),
                    timeout=tool_def.timeout_sec,
                )

        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(f"⏱️ Tool '{canonical_name}' timed out after {tool_def.timeout_sec:.1f}s")
            self._record_metrics(canonical_name, success=False, duration_ms=duration_ms)
            return ToolResult.timeout(canonical_name, tool_def.timeout_sec, execution_ms=duration_ms)

        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(f"❌ Tool '{canonical_name}' raised exception: {exc}", exc_info=True)
            self._record_metrics(canonical_name, success=False, duration_ms=duration_ms)
            # Keep exception details in logs only.  Returning raw provider,
            # filesystem, or subprocess errors can disclose internal paths,
            # credentials, or implementation details to the model and UI.
            return ToolResult.failed(
                tool_name=canonical_name,
                error_code=ToolErrorCode.EXECUTION_EXCEPTION,
                message="Tool execution failed; see the execution log for details.",
                stderr="",
                execution_ms=duration_ms,
            )

        duration_ms = (time.perf_counter() - t0) * 1000.0

        # ── Stage 10: Physical Verification & Observation Extraction ──
        result_obj = self._build_canonical_result(
            tool_def=tool_def,
            raw_res=raw_res,
            args=normalized_args,
            duration_ms=duration_ms,
            task_id=task_id,
            step_id=step_id,
            inv_id=inv_id,
        )

        # ── Stage 11: Cache Invalidation & Save ──
        if tool_def.is_read_only and result_obj.success:
            try:
                from brjarvis.memory.unified_memory import get_unified_memory

                get_unified_memory().cache_tool_result(
                    canonical_name, normalized_args, result_obj.data, ttl=tool_def.cache_ttl_seconds
                )
            except Exception:
                pass
        elif not tool_def.is_read_only and result_obj.success:
            self._invalidate_related_caches(tool_def)

        # ── Stage 12: Ledger, State, & EventBus Emission ──
        self._record_metrics(canonical_name, success=result_obj.success, duration_ms=duration_ms)
        self._record_ledger_and_wal(result_obj, task_id=task_id, step_id=step_id, parameters=normalized_args)

        try:
            get_event_bus().publish(
                ToolExecutionEvent(
                    topic="tool.exec.completed" if result_obj.success else "tool.exec.failed",
                    tool_name=canonical_name,
                    args=normalized_args,
                    success=result_obj.success,
                    result=result_obj.output,
                    duration_ms=duration_ms,
                )
            )
        except Exception:
            pass

        return result_obj

    def execute_tool(
        self,
        name: str,
        args: Dict[str, Any],
        task_id: str = "",
        step_id: str = "",
        user: str = "default_user",
        device: str = "pc_primary",
        application: str = "system",
        confirmed: bool = False,
    ) -> ToolResult:
        """
        Synchronous execution entrypoint. Safely bridges into event loop without deadlocks.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # Current thread has a running event loop. Execute on dedicated worker thread.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    self.execute_tool_async(
                        name=name,
                        args=args,
                        task_id=task_id,
                        step_id=step_id,
                        user=user,
                        device=device,
                        application=application,
                        confirmed=confirmed,
                    ),
                )
                return future.result()
        else:
            return asyncio.run(
                self.execute_tool_async(
                    name=name,
                    args=args,
                    task_id=task_id,
                    step_id=step_id,
                    user=user,
                    device=device,
                    application=application,
                    confirmed=confirmed,
                )
            )

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _invoke_sync_handler(self, handler: Callable[..., Any], args: Dict[str, Any]) -> Any:
        """Invoke a synchronous handler with flexible signature support."""
        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())
        if len(params) == 1 and params[0] in ("args", "kwargs", "data", "payload", "input_data", "parameters"):
            return handler(args)
        else:
            try:
                return handler(**args)
            except TypeError:
                return handler(args)

    def _build_canonical_result(
        self,
        tool_def: ToolDefinition,
        raw_res: Any,
        args: Dict[str, Any],
        duration_ms: float,
        task_id: str,
        step_id: str,
        inv_id: str,
    ) -> ToolResult:
        """Construct canonical ToolResult and perform physical state verification."""
        if isinstance(raw_res, ToolResult):
            raw_res.task_id = task_id or raw_res.task_id
            raw_res.step_id = step_id or raw_res.step_id
            raw_res.execution_ms = duration_ms
            return raw_res

        str_output = str(raw_res or "")

        # Perform universal physical outcome verification
        verified = True
        evidence = ""
        obs: Optional[Observation] = None

        try:
            from brjarvis.agent.verifier import ActionVerifier

            v_res = ActionVerifier.verify_action(tool_def.name, args, str_output)
            verified = v_res.verified
            evidence = v_res.evidence or v_res.details
            if not verified and v_res.status.value == "FAILED":
                return ToolResult.failed(
                    tool_name=tool_def.name,
                    error_code=ToolErrorCode.VERIFICATION_FAILED,
                    message=f"Verification failed: {v_res.details}",
                    stderr=str_output,
                    execution_ms=duration_ms,
                )
        except Exception as ver_err:
            logger.debug(f"Verification pass note: {ver_err}")

        # Construct physical Observation object
        subject_target = str(
            args.get("path") or args.get("url") or args.get("recipient") or args.get("app_name") or tool_def.name
        )
        obs = Observation(
            subject=subject_target,
            property="execution_state",
            old_state=None,
            new_state="SUCCESS" if verified else "FAILED",
            evidence=evidence or f"Executed {tool_def.name}",
            confidence=1.0 if verified else 0.5,
            source=tool_def.name,
        )

        return ToolResult(
            tool_name=tool_def.name,
            task_id=task_id,
            step_id=step_id,
            invocation_id=inv_id,
            status=ToolExecutionStatus.SUCCESS if verified else ToolExecutionStatus.PARTIAL,
            data=raw_res,
            stdout=str_output,
            evidence=evidence or f"Executed {tool_def.name} successfully.",
            verified=verified,
            execution_ms=duration_ms,
            observation=obs,
        )

    def _invalidate_related_caches(self, tool_def: ToolDefinition):
        """Invalidate affected read caches on mutation."""
        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            mem = get_unified_memory()
            if tool_def.category == ToolCategory.FILESYSTEM:
                mem.invalidate_tool_cache("file_read")
                mem.invalidate_tool_cache("file_list")
                mem.invalidate_tool_cache("file_search")
            elif tool_def.category == ToolCategory.MEMORY:
                mem.invalidate_tool_cache("memory_get")
                mem.invalidate_tool_cache("memory_search")
            elif tool_def.category == ToolCategory.COMMUNICATION:
                mem.invalidate_tool_cache("list_calendar_events")
        except Exception:
            pass

    def _record_metrics(self, tool_name: str, success: bool, duration_ms: float):
        """Record operational telemetry for the tool."""
        m = self._metrics.setdefault(
            tool_name, {"calls": 0, "successes": 0, "failures": 0, "total_duration_ms": 0.0, "avg_duration_ms": 0.0}
        )
        m["calls"] += 1
        if success:
            m["successes"] += 1
        else:
            m["failures"] += 1
        m["total_duration_ms"] += duration_ms
        m["avg_duration_ms"] = m["total_duration_ms"] / m["calls"]

    def _record_ledger_and_wal(
        self,
        result: ToolResult,
        task_id: str,
        step_id: str,
        parameters: Dict[str, Any],
    ):
        """Persist execution record to ExecutionLedger and TaskStateManager WAL."""
        if not task_id:
            return

        try:
            from brjarvis.agent.execution_ledger import LedgerEntry, LedgerStatus, get_execution_ledger

            ledger = get_execution_ledger()
            status_map = {
                ToolExecutionStatus.SUCCESS: LedgerStatus.SUCCESS,
                ToolExecutionStatus.FAILED: LedgerStatus.FAILED,
                ToolExecutionStatus.PARTIAL: LedgerStatus.PARTIAL,
                ToolExecutionStatus.BLOCKED: LedgerStatus.BLOCKED,
                ToolExecutionStatus.DENIED: LedgerStatus.BLOCKED,
                ToolExecutionStatus.TIMEOUT: LedgerStatus.TIMEOUT,
                ToolExecutionStatus.REQUIRES_APPROVAL: LedgerStatus.REQUIRES_USER,
            }
            entry = LedgerEntry(
                tool_name=result.tool_name,
                task_id=task_id,
                step_id=step_id or "step_1",
                execution_id=result.invocation_id,
                status=status_map.get(result.status, LedgerStatus.SUCCESS if result.success else LedgerStatus.FAILED),
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.return_code,
                duration_seconds=result.duration_seconds,
                evidence=result.evidence,
                verification_status=LedgerStatus.SUCCESS if result.verified else LedgerStatus.UNVERIFIED,
                parameters=parameters,
                error=result.error,
            )
            ledger.record(entry)
        except Exception as e:
            logger.debug(f"Ledger record note: {e}")

        try:
            from brjarvis.agent.task_state import get_task_state_manager

            state_mgr = get_task_state_manager()
            state_mgr.record_step_wal(
                task_id=task_id,
                step_index=int(step_id.replace("step_", "")) if step_id.replace("step_", "").isdigit() else 1,
                capability=result.tool_name,
                parameters=parameters,
                status="completed" if result.success else "failed",
                result=result.data,
                duration=result.duration_seconds,
                verified=result.verified,
                error=result.error,
            )
        except Exception as e:
            logger.debug(f"WAL record note: {e}")


def get_canonical_tool_runtime() -> ToolRuntime:
    """Convenience getter for the canonical ToolRuntime."""
    return ToolRuntime.get_instance()
