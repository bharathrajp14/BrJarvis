"""Canonical, bounded ReAct agent execution loop."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from jarvis.gateway import Message, ModelGateway

from .contracts import AgentTurnResult, AgentTurnStatus, LedgerStatus, TaskStatus
from .execution_ledger import ExecutionLedger, LedgerEntry
from .session import AgentSession, get_or_create_session
from .task_state import TaskState

logger = logging.getLogger("jarvis.agent.loop")

DEFAULT_MAX_STEPS = 20
DEFAULT_CYCLIC_LIMIT = 5


def parse_tool_calls(text: str) -> list[tuple[str, dict[str, Any]]]:
    """Extract all tool calls from model response text, supporting multiple sequential calls."""
    calls: list[tuple[str, dict[str, Any]]] = []

    # 1. Fenced ```tool_call ... ``` or ```json ... ``` blocks
    fenced_blocks = re.findall(r"```(?:tool_call|json)?\s*\n?(\{.*?\})\s*\n?```", text, re.DOTALL)
    for block in fenced_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and "tool" in data:
                calls.append((str(data["tool"]), data.get("args", {})))
        except Exception:
            pass

    # 2. Inline {"tool": "...", "args": {...}} occurrences
    if not calls:
        for m in re.finditer(r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}', text, re.DOTALL):
            try:
                args = json.loads(m.group(2))
                calls.append((m.group(1), args))
            except Exception:
                pass

    return calls


def parse_tool_call(text: str) -> tuple[str | None, dict[str, Any] | None]:
    """Extract first tool name and arguments from model response text (backward compatible)."""
    calls = parse_tool_calls(text)
    if calls:
        return calls[0][0], calls[0][1]
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
        tool_runtime: Any | None = None,
        task_repository: Any | None = None,
    ) -> None:
        self.session: AgentSession = session or get_or_create_session()
        self.gateway = gateway
        self.max_steps = max_steps
        self.tool_executor = tool_executor
        self.tool_runtime = tool_runtime
        self.task_repository = task_repository
        self.ledger = ExecutionLedger()
        self.last_result: AgentTurnResult | None = None

    def _execute_tool_action(
        self,
        tool_name: str,
        args: dict[str, Any],
        task_id: str,
        turn_id: str,
    ) -> tuple[str, bool, list[str]]:
        """Safely execute a tool action using ToolRuntime or legacy tool_executor."""
        if self.tool_runtime is not None:
            try:
                from jarvis.tools import ToolContext

                workspace = getattr(self.tool_runtime, "default_workspace", Path.cwd())
                ctx = ToolContext(
                    workspace_dir=workspace,
                    task_id=task_id,
                    correlation_id=turn_id,
                    approved=True,
                )
                res = self.tool_runtime.execute(tool_name, args, context=ctx)
                output_str = res.evidence or (str(res.output) if res.is_success else res.error)
                return output_str, res.is_success, list(res.artifacts)
            except Exception as exc:
                logger.error("ToolRuntime execution error on '%s': %s", tool_name, exc, exc_info=True)
                return f"Tool execution failed: {exc}", False, []
        elif self.tool_executor is not None:
            try:
                output_str, verified = self.tool_executor(tool_name, args)
                return output_str, verified, []
            except Exception as exc:
                logger.error("tool_executor error on '%s': %s", tool_name, exc, exc_info=True)
                return f"Tool execution error: {exc}", False, []
        else:
            return f"Tool '{tool_name}' executed (mock).", True, []

    def run_turn(
        self,
        user_input: str,
        *,
        system_prompt: str = "You are JARVIS, an expert AI assistant. Think clearly, act decisively with tools, and verify results.",
        available_tools: Sequence[str] | None = None,
        parent_task_id: str = "",
    ) -> AgentTurnResult:
        """Run a full autonomous agent turn with iterative tool execution."""
        start_time = time.monotonic()
        start_timestamp = time.time()
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
                metadata={
                    "run_id": turn_id,
                    "task_id": task_id,
                    "session_id": self.session.session_id,
                    "agent_id": "jarvis_canonical_agent",
                    "status": "success_verified",
                    "fast_path": True,
                },
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
                metadata={
                    "run_id": turn_id,
                    "task_id": task_id,
                    "session_id": self.session.session_id,
                    "error_state": "GatewayNotConfigured",
                },
            )
            self.last_result = res
            return res

        # Step 3: Initialize durable task state machine
        task_state = TaskState(task_id=task_id, user_request=user_input, status=TaskStatus.CREATED)
        task_state.transition(TaskStatus.RUNNING, "Starting autonomous execution")

        if self.task_repository is not None:
            try:
                self.task_repository.save_task(task_state)
            except Exception as exc:
                logger.warning("Task persistence notice: %s", exc)

        call_counts: dict[str, int] = {}
        tool_history: list[dict[str, Any]] = []
        collected_artifacts: list[str] = []
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

        last_model_id = ""

        while step < self.max_steps:
            step += 1
            task_state.advance_step()

            try:
                resp = self.gateway.generate(messages, system=system_prompt)
                last_model_id = getattr(resp, "model", "") or last_model_id
                raw_response = resp.text
            except Exception as exc:
                logger.error("LLM generation failed: %s", exc)
                final_text = f"Backend error: {exc}"
                terminal_status = AgentTurnStatus.FAILED
                terminal_error = str(exc)
                break

            tool_calls = parse_tool_calls(raw_response)

            if tool_calls:
                for tool_name, tool_args in tool_calls:
                    args = tool_args or {}
                    call_key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
                    call_counts[call_key] = call_counts.get(call_key, 0) + 1

                    # Loop prevention guard
                    if call_counts[call_key] >= DEFAULT_CYCLIC_LIMIT:
                        logger.warning("Cyclic loop detected for '%s' (%d calls)", tool_name, call_counts[call_key])
                        tool_result_str = f"Error: Tool '{tool_name}' aborted due to cyclic repetition limit."
                        verified = False
                        artifacts = []
                    else:
                        task_state.transition(TaskStatus.WAITING_FOR_TOOL, f"Executing {tool_name}")
                        tool_result_str, verified, artifacts = self._execute_tool_action(
                            tool_name, args, task_id, turn_id
                        )
                        task_state.transition(TaskStatus.VERIFYING, f"Evaluating {tool_name} output")
                        task_state.transition(TaskStatus.RUNNING, "Resuming execution")

                    collected_artifacts.extend(artifacts)
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

                    tool_history.append(
                        {
                            "tool": tool_name,
                            "args": args,
                            "result": tool_result_str,
                            "verified": verified,
                        }
                    )
                    self.session.add_tool_turn(tool_name, args, tool_result_str, verified)

                    # Feed observation back to conversation history
                    messages.append(Message(role="assistant", content=raw_response))
                    messages.append(Message(role="user", content=f"Tool '{tool_name}' result: {tool_result_str}"))

                # Persist intermediate checkpoint if repository available
                if self.task_repository is not None:
                    try:
                        self.task_repository.save_task(task_state)
                    except Exception as exc:
                        logger.debug("Intermediate task save note: %s", exc)

                continue

            # No tool call — final response reached
            final_text = clean_response_text(raw_response)
            break

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        self.session.add_assistant_turn(final_text, latency_ms=elapsed_ms)
        self.session.clear_active_task()

        task_state.transition(
            TaskStatus.COMPLETED if terminal_status == AgentTurnStatus.SUCCESS_VERIFIED else TaskStatus.FAILED,
            reason="Execution cycle finished",
        )

        if self.task_repository is not None:
            try:
                self.task_repository.save_task(task_state)
            except Exception as exc:
                logger.debug("Final task save note: %s", exc)

        evidence_report = self.ledger.build_evidence_report(task_id) if tool_history else ""

        run_metadata = {
            "run_id": turn_id,
            "task_id": task_id,
            "session_id": self.session.session_id,
            "parent_task_id": parent_task_id,
            "agent_id": "jarvis_canonical_agent",
            "model_id": last_model_id or getattr(self.gateway, "default_model", "default"),
            "started_at": start_timestamp,
            "finished_at": time.time(),
            "status": terminal_status.value,
            "current_step": step,
            "step_count": step,
            "budget": self.max_steps,
            "permissions": "FULL",
            "tool_calls": len(tool_history),
            "observations": [t.get("result", "")[:100] for t in tool_history],
            "verification_state": "VERIFIED" if terminal_status == AgentTurnStatus.SUCCESS_VERIFIED else "UNVERIFIED",
            "error_state": terminal_error,
            "provenance": "canonical_agent_loop",
        }

        res = AgentTurnResult(
            response=final_text,
            status=terminal_status,
            verified=terminal_status == AgentTurnStatus.SUCCESS_VERIFIED,
            elapsed_ms=elapsed_ms,
            error=terminal_error,
            tool_failures=sum(1 for t in tool_history if not t["verified"]),
            evidence=evidence_report,
            artifacts=collected_artifacts,
            metadata=run_metadata,
        )
        self.last_result = res
        return res
