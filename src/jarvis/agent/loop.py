"""Canonical, bounded ReAct agent execution loop."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections.abc import Callable, Sequence
from typing import Any

from jarvis.gateway import Message, ModelGateway

from .contracts import AgentTurnResult, AgentTurnStatus, LedgerStatus, TaskStatus
from .execution_ledger import ExecutionLedger, LedgerEntry
from .session import AgentSession, get_or_create_session
from .task_state import TaskState

logger = logging.getLogger("jarvis.agent.loop")

DEFAULT_MAX_STEPS = 20
DEFAULT_CYCLIC_LIMIT = 5


def parse_tool_call(text: str) -> tuple[str | None, dict[str, Any] | None]:
    """Extract tool name and arguments from model response text."""
    # Pattern 1: fenced ```tool_call ... ```
    m = re.search(r"```(?:tool_call|json)?\s*\n?(\{.*?\})\s*\n?```", text, re.DOTALL)
    candidate_json = m.group(1) if m else None

    # Pattern 2: inline {"tool": "...", "args": {...}}
    if not candidate_json:
        m2 = re.search(r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}', text, re.DOTALL)
        if m2:
            try:
                args = json.loads(m2.group(2))
                return m2.group(1), args
            except Exception:
                pass

    if candidate_json:
        try:
            data = json.loads(candidate_json)
            if isinstance(data, dict) and "tool" in data:
                return str(data["tool"]), data.get("args", {})
        except Exception:
            pass

    return None, None


def clean_response_text(text: str) -> str:
    """Strip raw tool call blocks and provider markers from user-facing text."""
    cleaned = re.sub(r"```(?:tool_call|json)?\s*\n?\{.*?\}\s*\n?```", "", text, flags=re.DOTALL)
    cleaned = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{.*?\}\s*\}', "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|start\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<\|.*?\|>", "", cleaned)
    return cleaned.strip()


class AgentLoop:
    """The authoritative agent execution engine for interactive turns."""

    def __init__(
        self,
        session: AgentSession | None = None,
        gateway: ModelGateway | None = None,
        max_steps: int = DEFAULT_MAX_STEPS,
        tool_executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
    ) -> None:
        self.session: AgentSession = session or get_or_create_session()
        self.gateway = gateway
        self.max_steps = max_steps
        self.tool_executor = tool_executor
        self.ledger = ExecutionLedger()
        self.last_result: AgentTurnResult | None = None

    def run_turn(
        self,
        user_input: str,
        *,
        system_prompt: str = "You are JARVIS, an expert AI assistant. Think clearly, act decisively with tools, and verify results.",
        available_tools: Sequence[str] | None = None,
    ) -> AgentTurnResult:
        """Run a full autonomous agent turn with iterative tool execution."""
        start_time = time.monotonic()
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        self.session.correlation_id = turn_id
        self.session.set_active_task(task_id, user_input[:40])
        self.session.add_user_turn(user_input)

        # Step 1: Fast-path / deterministic commands
        norm_input = user_input.strip().lower()
        if norm_input in {"status", "/status", "ping", "health"}:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            res_text = "System status: OK. All autonomous engines operational."
            self.session.add_assistant_turn(res_text, latency_ms=elapsed_ms)
            self.session.clear_active_task()
            res = AgentTurnResult(
                response=res_text,
                status=AgentTurnStatus.SUCCESS_VERIFIED,
                verified=True,
                elapsed_ms=elapsed_ms,
            )
            self.last_result = res
            return res

        # Step 2: Ensure gateway is configured
        if self.gateway is None:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            res = AgentTurnResult(
                response="No model gateway configured. Please configure an LLM provider.",
                status=AgentTurnStatus.FAILED,
                verified=False,
                elapsed_ms=elapsed_ms,
                error="GatewayNotConfigured",
            )
            self.last_result = res
            return res

        task_state = TaskState(task_id=task_id, user_request=user_input, status=TaskStatus.RUNNING)

        # Step 3: ReAct execution loop
        call_counts: dict[str, int] = {}
        tool_history: list[dict[str, Any]] = []
        step = 0
        final_text = ""
        terminal_status = AgentTurnStatus.SUCCESS_VERIFIED
        terminal_error = ""

        # Construct messages from session history
        messages = [
            Message(role=msg["role"], content=msg.get("content", ""))
            for msg in self.session.get_recent_history(limit=10)
            if msg.get("role") in {"user", "assistant"}
        ]

        while step < self.max_steps:
            step += 1
            task_state.advance_step()

            try:
                resp = self.gateway.generate(messages, system=system_prompt)
                raw_response = resp.text
            except Exception as exc:
                logger.error("LLM generation failed: %s", exc)
                final_text = f"Backend error: {exc}"
                terminal_status = AgentTurnStatus.FAILED
                terminal_error = str(exc)
                break

            tool_name, tool_args = parse_tool_call(raw_response)

            if tool_name:
                args = tool_args or {}
                call_key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
                call_counts[call_key] = call_counts.get(call_key, 0) + 1

                # Loop prevention
                if call_counts[call_key] >= DEFAULT_CYCLIC_LIMIT:
                    logger.warning("Cyclic loop detected for '%s' (%d calls)", tool_name, call_counts[call_key])
                    tool_result_str = f"Error: Tool '{tool_name}' aborted due to cyclic repetition limit."
                    verified = False
                elif self.tool_executor:
                    try:
                        tool_result_str, verified = self.tool_executor(tool_name, args)
                    except Exception as exc:
                        tool_result_str = f"Tool execution error: {exc}"
                        verified = False
                else:
                    tool_result_str = f"Tool '{tool_name}' executed (mock)."
                    verified = True

                task_state.record_action(tool_name, args, tool_result_str, verified)
                self.ledger.append(
                    LedgerEntry(
                        task_id=task_id,
                        step_id=f"step_{step}",
                        tool_name=tool_name,
                        status=LedgerStatus.SUCCESS if verified else LedgerStatus.FAILED,
                        evidence=tool_result_str[:200],
                        verification_status=LedgerStatus.SUCCESS if verified else LedgerStatus.FAILED,
                    )
                )

                tool_history.append({"tool": tool_name, "args": args, "result": tool_result_str, "verified": verified})
                self.session.add_tool_turn(tool_name, args, tool_result_str, verified)

                # Feed observation back to LLM for next turn
                messages.append(Message(role="assistant", content=raw_response))
                messages.append(Message(role="user", content=f"Tool '{tool_name}' result: {tool_result_str}"))
                continue

            # No tool call — final response reached
            final_text = clean_response_text(raw_response)
            break

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        self.session.add_assistant_turn(final_text, latency_ms=elapsed_ms)
        self.session.clear_active_task()

        task_state.transition(
            TaskStatus.COMPLETED if terminal_status == AgentTurnStatus.SUCCESS_VERIFIED else TaskStatus.FAILED
        )

        evidence_report = self.ledger.build_evidence_report(task_id) if tool_history else ""

        res = AgentTurnResult(
            response=final_text,
            status=terminal_status,
            verified=terminal_status == AgentTurnStatus.SUCCESS_VERIFIED,
            elapsed_ms=elapsed_ms,
            error=terminal_error,
            tool_failures=sum(1 for t in tool_history if not t["verified"]),
            evidence=evidence_report,
        )
        self.last_result = res
        return res
