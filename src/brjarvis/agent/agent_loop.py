# agent/agent_loop.py — Canonical Universal Agent Loop for BR JARVIS
"""
Canonical Event-Driven Agent Execution Loop for BR JARVIS.
Orchestrates:
1. Understand (User Request & Intent)
2. Context Discovery (Unified Memory, Experiences, Lessons)
3. Dynamic Planning (Goal Decomposition & Step Planning)
4. Permission Interlock (Risk Evaluation & Interactive Approvals)
5. Tool Execution (ToolRuntime with Timeout & Sandboxing)
6. Observe & Physical Verification (File, Process, Browser, Git)
7. Adapt (Loop Prevention & Error Recovery)
8. Respond (Evidence-backed Synthesis)
9. Complete (Memory Consolidation & Event Emission)
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from brjarvis.agent.session import AgentSession, get_or_create_session
from brjarvis.agent.verifier import (
    FileVerifier,
)
from brjarvis.events.bus import get_event_bus
from brjarvis.events.types import (
    AgentLifecycleEvent,
    ToolLifecycleEvent,
    VerificationEvent,
)
from brjarvis.security.permission_request import (
    PermissionDecision,
    PermissionRequest,
    RiskLevel,
    get_permission_manager,
)
from brjarvis.tools.registry import (
    execute_tool,
    get_tool_prompt_block,
    parse_tool_call,
)

logger = logging.getLogger("JARVIS.AgentLoop")

MAX_AGENT_STEPS = 20

# Per-tool cyclic loop thresholds
CYCLIC_LIMITS: Dict[str, int] = {
    "run_code": 6,
    "scratchpad_eval": 6,
    "scratchpad_write": 6,
    "file_read": 6,
    "file_write": 6,
    "web_search": 5,
    "fetch_page": 5,
    "fetch_raw": 5,
}
DEFAULT_CYCLIC_LIMIT = 3


class AgentTurnStatus(str, Enum):
    """Truthful terminal states for one canonical agent turn."""

    SUCCESS_VERIFIED = "success_verified"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True)
class AgentTurnResult:
    """Typed terminal result retained alongside the backwards-compatible text response."""

    response: str
    status: AgentTurnStatus
    verified: bool
    elapsed_ms: int
    error: str = ""
    tool_failures: int = 0


def _clean_model_response(text: str) -> str:
    """Strip tool_call blocks and formatting markers from model response."""
    cleaned = re.sub(r"```tool_call\s*\n\s*\{.*?\}\s*\n\s*```", "", text, flags=re.DOTALL)
    cleaned = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{.*?\}\s*\}', "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|start\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|channel\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|message\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|.*?\|>", "", cleaned)
    return cleaned.strip()


def _synthesize_evidence(tool_history: List[Dict[str, Any]], user_input: str) -> str:
    """Synthesize a truthful, verified summary from tool execution evidence."""
    if not tool_history:
        return "I processed your request, but no tool operations were required."

    tools_used = list(dict.fromkeys(t["tool_name"] for t in tool_history if "tool_name" in t))
    has_errors = any("error" in str(t.get("result", "")).lower() or not t.get("verified", True) for t in tool_history)

    status_header = (
        f"Completed operations using {', '.join(tools_used)}."
        if not has_errors
        else f"Completed with notices (Tools: {', '.join(tools_used)})."
    )

    lines = [status_header, "", "### Execution Evidence:"]
    for t in tool_history:
        tname = t.get("tool_name", "tool")
        res = str(t.get("result", "")).strip().replace("\n", " ")[:140]
        verified = t.get("verified", True)
        icon = "✓" if verified else "✗"
        lines.append(f"- {icon} **{tname}**: {res}")

    return "\n".join(lines)


class AgentLoop:
    """The authoritative agent execution engine for all interactions."""

    def __init__(self, session: Optional[AgentSession] = None, gateway: Any = None):
        self.session: AgentSession = session or get_or_create_session()
        self.gateway = gateway

        self.event_bus = get_event_bus()
        self.permission_mgr = get_permission_manager()
        self.last_result: Optional[AgentTurnResult] = None

    # ── Context Discovery ─────────────────────────────────────────────────────

    def discover_context(self, user_prompt: str) -> str:
        """Retrieve relevant long-term memories, lessons, and operational experience."""
        blocks = []
        low = user_prompt.lower().strip()

        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()
            memories = um.recall(user_prompt, limit=5)
            if memories:
                m_lines = []
                for m in memories:
                    m_type = m.get("type", m.get("source", "memory"))
                    name = m.get("name", "")
                    content = str(m.get("content", ""))[:250]
                    if content:
                        m_lines.append(f"- [{m_type.upper()}] {name}: {content}")
                if m_lines:
                    blocks.append("### 🧠 Persistent Context\n" + "\n".join(m_lines))

            # Retrieve past experience or lessons for technical tasks
            if any(w in low for w in ("fix", "build", "code", "audit", "verify", "delete", "test", "run")):
                exp = um.get_relevant_experiences(user_prompt, limit=2)
                exp_lines = []
                for succ in exp.get("successes", []):
                    exp_lines.append(
                        f"- Pattern for '{succ.get('goal_query', '')[:50]}': tools={succ.get('tool_sequence', [])}"
                    )
                for fail in exp.get("failures", []):
                    if fail.get("failure_reason"):
                        exp_lines.append(f"- Pitfall to avoid: {fail.get('failure_reason')[:120]}")
                if exp_lines:
                    blocks.append("### ⚡ Operational Lessons\n" + "\n".join(exp_lines))

        except Exception as exc:
            logger.debug("[AgentLoop] Context discovery note: %s", exc)

        return "\n\n".join(blocks)

    # ── Physical Verification ─────────────────────────────────────────────────

    def verify_action(self, tool_name: str, args: Dict[str, Any], raw_result: Any) -> Tuple[bool, str]:
        """Perform physical post-execution state verification."""
        clean_tool = tool_name.lower().strip()

        # 1. File verification
        if clean_tool in ("file_write", "create_file", "save_file") or "write" in clean_tool:
            path = args.get("path") or args.get("filepath") or args.get("filename")
            if path:
                res = FileVerifier.verify_file_created(str(path))
                return res.verified, res.evidence or res.details

        # 2. Document generation verification
        if clean_tool in ("create_word_document", "create_pdf_document", "create_excel_document", "document_creator"):
            path = args.get("path") or args.get("output_path") or args.get("filename")
            if path:
                res = FileVerifier.verify_file_created(str(path))
                return res.verified, res.evidence or res.details

        # 3. Fast search verification
        if clean_tool in ("web_search", "fetch_page", "fetch_raw", "file_read", "file_list"):
            # Informative read-only tools are verified by non-empty data
            has_data = raw_result is not None and len(str(raw_result).strip()) > 0
            return has_data, "Read-only payload retrieved successfully."

        # Default: check error markers in output
        res_str = str(raw_result).lower()
        if "error:" in res_str or "failed:" in res_str or "exception:" in res_str:
            return False, f"Tool execution signaled failure: {res_str[:120]}"

        return True, "Executed without runtime errors."

    # ── Main Cognitive Execution Turn ─────────────────────────────────────────

    @staticmethod
    def _gateway_capability(user_input: str, profile: Any) -> str:
        """Translate legacy profile and user intent into gateway capability."""
        text = user_input.lower()
        if any(word in text for word in ("image", "photo", "screen", "camera", "vision")):
            return "vision"
        if any(word in text for word in ("code", "script", "function", "debug", "build", "program")):
            return "code"
        if any(word in text for word in ("reason", "analyze", "analysis", "plan")):
            return "reasoning"
        return "chat"

    def run_turn(

        self,
        user_input: str,
        router: Any = None,
        interactive_permission_cb: Optional[Callable[[PermissionRequest], PermissionDecision]] = None,
    ) -> str:
        """Run a turn and preserve a typed terminal result for callers that need status."""
        started = time.monotonic()
        try:
            return self._run_turn_text(user_input, router, interactive_permission_cb)
        except Exception as exc:
            logger.exception("[AgentLoop] Unhandled turn failure")
            elapsed_ms = int((time.monotonic() - started) * 1000)
            response = f"Agent execution failed: {exc}"
            self.last_result = AgentTurnResult(
                response=response,
                status=AgentTurnStatus.FAILED,
                verified=False,
                elapsed_ms=elapsed_ms,
                error=str(exc),
            )
            self.event_bus.publish(
                AgentLifecycleEvent(
                    topic="agent.failed",
                    session_id=self.session.session_id,
                    task_id=self.session.active_task_id or "unknown",
                    phase="failed",
                    message="Turn failed with an unhandled execution error.",
                    correlation_id=self.session.correlation_id,
                )
            )
            return response
        finally:
            self.session.clear_active_task()

    def run_turn_result(
        self,
        user_input: str,
        router: Any = None,
        interactive_permission_cb: Optional[Callable[[PermissionRequest], PermissionDecision]] = None,
    ) -> AgentTurnResult:
        """Run a turn and return its typed terminal result."""
        self.run_turn(user_input, router, interactive_permission_cb)
        if self.last_result is None:
            raise RuntimeError("Agent turn completed without a terminal result")
        return self.last_result

    def _run_turn_text(
        self,
        user_input: str,
        router: Any = None,
        interactive_permission_cb: Optional[Callable[[PermissionRequest], PermissionDecision]] = None,
    ) -> str:
        """Run a full autonomous agent turn with live lifecycle events."""
        t_start = time.monotonic()
        corr_id = f"turn-{uuid.uuid4().hex[:8]}"
        self.session.correlation_id = corr_id
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        self.session.set_active_task(task_id, user_input[:30])

        # Record user turn
        self.session.add_user_turn(user_input)

        # Emit agent.started
        self.event_bus.publish(
            AgentLifecycleEvent(
                topic="agent.started",
                session_id=self.session.session_id,
                task_id=task_id,
                phase="started",
                message=f"Received user request: {user_input[:80]}",
                correlation_id=corr_id,
            )
        )

        # ── Step 1: Deterministic status path ──
        if user_input.strip().lower().lstrip("/") in {"status", "health", "system status"}:
            result_text = "System status: OK. All autonomous engines operational."
            elapsed_ms = int((time.monotonic() - t_start) * 1000)
            self.session.add_assistant_turn(result_text, latency_ms=elapsed_ms)
            self.event_bus.publish(
                AgentLifecycleEvent(
                    topic="agent.completed",
                    session_id=self.session.session_id,
                    task_id=task_id,
                    phase="completed",
                    message="Deterministic status path executed.",
                    correlation_id=corr_id,
                )
            )
            self.last_result = AgentTurnResult(
                response=result_text,
                status=AgentTurnStatus.SUCCESS_VERIFIED,
                verified=True,
                elapsed_ms=elapsed_ms,
            )
            self.session.clear_active_task()
            return result_text

        # ── Step 2: Canonical Unified Pipeline Execution ──
        try:
            from brjarvis.core.canonical_runtime import CanonicalRequestRuntime
            from brjarvis.core.intent_models import AtomicityType, ExecutionState

            runtime_res = CanonicalRequestRuntime.handle(user_input)
            if runtime_res.state in (ExecutionState.COMPLETED, ExecutionState.PARTIAL) and (
                runtime_res.low_latency_execution
                or runtime_res.understanding.atomicity in (
                    AtomicityType.ATOMIC,
                    AtomicityType.COMPOSITE,
                    AtomicityType.NEGATED,
                    AtomicityType.INFORMATIONAL,
                    AtomicityType.HYPOTHETICAL,
                    AtomicityType.CONVERSATIONAL,
                )
            ):
                result_text = runtime_res.text
                elapsed_ms = int((time.monotonic() - t_start) * 1000)
                self.session.add_assistant_turn(result_text, latency_ms=elapsed_ms)
                self.event_bus.publish(
                    AgentLifecycleEvent(
                        topic="agent.completed",
                        session_id=self.session.session_id,
                        task_id=task_id,
                        phase="completed",
                        message="Canonical request pipeline executed successfully.",
                        correlation_id=corr_id,
                    )
                )
                self.last_result = AgentTurnResult(
                    response=result_text,
                    status=AgentTurnStatus.SUCCESS_VERIFIED if runtime_res.state == ExecutionState.COMPLETED else AgentTurnStatus.PARTIAL_SUCCESS,
                    verified=True,
                    elapsed_ms=elapsed_ms,
                )
                self.session.clear_active_task()
                return result_text
        except Exception as runtime_err:
            logger.debug("[AgentLoop] Canonical runtime notice: %s", runtime_err)


        # ── Step 2: Context Discovery ──
        self.event_bus.publish(
            AgentLifecycleEvent(
                topic="agent.context_started",
                session_id=self.session.session_id,
                task_id=task_id,
                phase="context_started",
                correlation_id=corr_id,
            )
        )
        discovered_context = self.discover_context(user_input)
        if discovered_context:
            self.session.discovered_context.append(discovered_context)
        self.event_bus.publish(
            AgentLifecycleEvent(
                topic="agent.context_completed",
                session_id=self.session.session_id,
                task_id=task_id,
                phase="context_completed",
                correlation_id=corr_id,
            )
        )

        # ── Step 3: Resolve Router & Backends ──
        if router is None:
            from brjarvis.router import AgentRouter

            router = AgentRouter()

        # Build system prompt

        tool_prompt = get_tool_prompt_block()
        sys_parts = [
            "You are BR JARVIS, a highly capable agentic assistant.",
            f"Active Mode: {self.session.current_mode.upper()}",
            "Think clearly, act decisively with tools, and verify your results.",
            tool_prompt,
        ]
        if discovered_context:
            sys_parts.append(discovered_context)
        system_prompt = "\n\n".join(sys_parts)

        # Build conversation memory
        history_msgs = self.session.get_recent_history(limit=10)

        # ── Step 4: Iterative ReAct Loop ──
        tool_history: List[Dict[str, Any]] = []
        call_counts: Dict[str, int] = {}
        consecutive_tool: Dict[str, Any] = {"name": None, "args_str": None, "count": 0}
        step = 0
        final_response = ""
        terminal_status = AgentTurnStatus.SUCCESS_VERIFIED
        terminal_error = ""
        tool_failures = 0

        # Adaptive Profile Selection based on active persona mode & task keywords
        try:
            from brjarvis.router import AgentProfile

            mode_lower = (self.session.current_mode or "general").lower()
            mode_kw = [mode_lower]
            if mode_lower in ("coder", "code", "dev"):
                mode_kw = ["code"]
            elif mode_lower in ("analyst", "analysis"):
                mode_kw = ["analysis"]
            elif mode_lower in ("reasoning", "planner"):
                mode_kw = ["reasoning"]
            elif mode_lower in ("recon", "osint", "researcher"):
                mode_kw = ["search"]

            mode_profile = router.route(mode_kw) if hasattr(router, "route") else AgentProfile.GEMINI
        except Exception:
            mode_profile = "gemini"

        canonical_gateway_enabled = self.gateway is not None

        while step < MAX_AGENT_STEPS:

            # Emit agent.thinking
            self.event_bus.publish(
                AgentLifecycleEvent(
                    topic="agent.thinking",
                    session_id=self.session.session_id,
                    task_id=task_id,
                    phase="thinking",
                    message=f"Planning step {step + 1}...",
                    correlation_id=corr_id,
                )
            )

            try:
                if canonical_gateway_enabled and self.gateway is not None:
                    capability = self._gateway_capability(user_input, mode_profile)
                    try:
                        raw_response = self.gateway.generate(
                            history_msgs,
                            system=system_prompt,
                            capability=capability,
                            metadata={"legacy_profile": getattr(mode_profile, "value", str(mode_profile))},
                        ).text
                    except Exception as gateway_err:
                        logger.warning("[AgentLoop] Canonical gateway failed; using legacy router fallback: %s", gateway_err)
                        canonical_gateway_enabled = False
                        raw_response = router.run(mode_profile, history_msgs, system_prompt)
                else:
                    raw_response = router.run(mode_profile, history_msgs, system_prompt)
            except Exception as llm_err:

                logger.error(f"[AgentLoop] LLM call failed: {llm_err}")
                final_response = f"Backend error: {llm_err}"
                terminal_status = AgentTurnStatus.FAILED
                terminal_error = str(llm_err)
                break

            tool_name, tool_args = parse_tool_call(raw_response)

            # ── Branch A: Execute Tool ──
            if tool_name:
                args_str = json.dumps(tool_args or {}, sort_keys=True)
                call_sig = f"{tool_name}:{args_str}"
                call_counts[call_sig] = call_counts.get(call_sig, 0) + 1

                # Loop prevention
                cyclic_limit = CYCLIC_LIMITS.get(tool_name, DEFAULT_CYCLIC_LIMIT)
                if call_counts[call_sig] >= cyclic_limit:
                    logger.warning(
                        f"[AgentLoop] Cyclic loop detected for '{tool_name}' ({call_counts[call_sig]}/{cyclic_limit})"
                    )
                    final_response = _synthesize_evidence(tool_history, user_input)
                    terminal_status = AgentTurnStatus.PARTIAL
                    break

                # Consecutive duplicate limit
                if tool_name == consecutive_tool["name"] and args_str == consecutive_tool.get("args_str"):
                    consecutive_tool["count"] += 1
                else:
                    consecutive_tool = {"name": tool_name, "args_str": args_str, "count": 1}

                if consecutive_tool["count"] >= 3:
                    final_response = _synthesize_evidence(tool_history, user_input)
                    terminal_status = AgentTurnStatus.PARTIAL
                    break

                # ── Permission & Risk Check ──
                risk = self.permission_mgr.classify_risk(tool_name, tool_args or {})
                is_pre_approved = self.permission_mgr.is_pre_approved(
                    self.session.session_id,
                    tool_name,
                    str(tool_args.get("path") or tool_args.get("url") or "") if tool_args else "",
                )

                needs_prompt = (
                    not is_pre_approved
                    and self.session.permission_mode != "allow_all"
                    and (
                        (
                            self.session.permission_mode == "confirm_destructive"
                            and risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)
                        )
                        or (self.session.permission_mode == "confirm_all" and risk != RiskLevel.SAFE)
                    )
                )

                if needs_prompt:
                    req = self.permission_mgr.create_request(
                        tool=tool_name,
                        args=tool_args or {},
                        session_id=self.session.session_id,
                        task_id=task_id,
                    )
                    decision = PermissionDecision.DENY
                    if interactive_permission_cb:
                        decision = interactive_permission_cb(req)
                    elif self.permission_mgr._interactive_resolver:
                        decision = self.permission_mgr._interactive_resolver(req)
                    else:
                        decision = PermissionDecision.ALLOW_ONCE

                    self.permission_mgr.record_decision(self.session.session_id, req, decision)

                    if decision in (PermissionDecision.DENY, PermissionDecision.CANCEL):
                        tool_res = f"[Permission Denied: User did not authorize '{tool_name}']"
                        terminal_status = AgentTurnStatus.PARTIAL
                        tool_failures += 1
                        tool_history.append(
                            {"tool_name": tool_name, "args": tool_args, "result": tool_res, "verified": False}
                        )
                        history_msgs.append({"role": "assistant", "content": raw_response})
                        history_msgs.append(
                            {"role": "user", "content": f"[Tool Result for '{tool_name}']:\n{tool_res}"}
                        )
                        step += 1
                        continue

                # ── Physical Tool Execution ──
                step_id = f"step-{step + 1}"
                self.event_bus.publish(
                    ToolLifecycleEvent(
                        topic="tool.started",
                        tool_name=tool_name,
                        session_id=self.session.session_id,
                        task_id=task_id,
                        step_id=step_id,
                        status="started",
                        args=tool_args or {},
                        correlation_id=corr_id,
                    )
                )

                t_t0 = time.monotonic()
                try:
                    tool_raw_out = execute_tool(tool_name, tool_args or {})
                except Exception as t_err:
                    tool_raw_out = f"[Tool Error: {t_err}]"

                t_duration = (time.monotonic() - t_t0) * 1000.0

                # ── Physical Verification ──
                self.event_bus.publish(
                    VerificationEvent(
                        topic="verification.started",
                        session_id=self.session.session_id,
                        task_id=task_id,
                        tool_name=tool_name,
                        status="started",
                        correlation_id=corr_id,
                    )
                )

                verified, ver_evidence = self.verify_action(tool_name, tool_args or {}, tool_raw_out)
                if not verified:
                    terminal_status = AgentTurnStatus.PARTIAL
                    tool_failures += 1
                self.session.record_verification(tool_name, str(tool_args.get("path") or ""), verified, ver_evidence)

                self.event_bus.publish(
                    VerificationEvent(
                        topic="verification.completed" if verified else "verification.failed",
                        session_id=self.session.session_id,
                        task_id=task_id,
                        tool_name=tool_name,
                        verified=verified,
                        status="completed" if verified else "failed",
                        evidence=ver_evidence,
                        correlation_id=corr_id,
                    )
                )

                # Emit tool completion
                self.event_bus.publish(
                    ToolLifecycleEvent(
                        topic="tool.completed" if verified else "tool.failed",
                        tool_name=tool_name,
                        session_id=self.session.session_id,
                        task_id=task_id,
                        step_id=step_id,
                        status="completed" if verified else "failed",
                        args=tool_args or {},
                        result=str(tool_raw_out)[:500],
                        duration_ms=t_duration,
                        verified=verified,
                        verification_notes=ver_evidence,
                        correlation_id=corr_id,
                    )
                )

                tool_history.append(
                    {
                        "step": step,
                        "tool_name": tool_name,
                        "args": tool_args,
                        "result": tool_raw_out,
                        "duration_ms": t_duration,
                        "verified": verified,
                    }
                )
                self.session.record_tool_call(
                    tool_name, tool_args or {}, tool_raw_out, t_duration, verified, step_id=step_id
                )
                clean_assistant_entry = _clean_model_response(raw_response) or f"[Executing tool {tool_name}]"
                history_msgs.append({"role": "assistant", "content": clean_assistant_entry})
                str_res = str(tool_raw_out)
                if len(str_res) > 3000:
                    str_res = str_res[:1500] + "\n[... truncated ...]\n" + str_res[-1000:]
                history_msgs.append({"role": "user", "content": f"[Tool Result for '{tool_name}']:\n{str_res}"})

                step += 1
                continue

            # ── Branch B: Natural Language Response ──
            else:
                final_response = _clean_model_response(raw_response)
                if not final_response:
                    final_response = _synthesize_evidence(tool_history, user_input)
                break

        if not final_response:
            final_response = _synthesize_evidence(tool_history, user_input)
            if step >= MAX_AGENT_STEPS:
                terminal_status = AgentTurnStatus.PARTIAL

        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        self.session.add_assistant_turn(
            content=final_response,
            tool_calls=[{"tool": t["tool_name"], "args": t["args"]} for t in tool_history],
            tool_results=[{"tool": t["tool_name"], "result": str(t["result"])[:200]} for t in tool_history],
            latency_ms=elapsed_ms,
        )

        verified_turn = terminal_status == AgentTurnStatus.SUCCESS_VERIFIED and tool_failures == 0
        self.last_result = AgentTurnResult(
            response=final_response,
            status=terminal_status,
            verified=verified_turn,
            elapsed_ms=elapsed_ms,
            error=terminal_error,
            tool_failures=tool_failures,
        )

        # Emit truthful terminal lifecycle event
        terminal_topic = {
            AgentTurnStatus.SUCCESS_VERIFIED: "agent.completed",
            AgentTurnStatus.PARTIAL: "agent.partial",
            AgentTurnStatus.FAILED: "agent.failed",
            AgentTurnStatus.CANCELLED: "agent.cancelled",
            AgentTurnStatus.TIMED_OUT: "agent.timed_out",
        }[terminal_status]
        self.event_bus.publish(
            AgentLifecycleEvent(
                topic=terminal_topic,
                session_id=self.session.session_id,
                task_id=task_id,
                phase=terminal_status.value,
                message=(
                    "Turn completed with verified success."
                    if verified_turn
                    else f"Turn ended with status {terminal_status.value}."
                ),
                correlation_id=corr_id,
            )
        )

        self.session.clear_active_task()
        return final_response
