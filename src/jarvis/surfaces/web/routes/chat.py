"""Chat endpoints for user interaction turns."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jarvis.agent.loop import AgentLoop
from jarvis.agent.session import get_or_create_session
from jarvis.core.bootstrap import get_assistant_runtime
from jarvis.tools.builtin import register_default_tools
from jarvis.tools.registry import get_tool_registry
from jarvis.tools.runtime import ToolRuntime

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatTurnRequest(BaseModel):
    """Payload for submitting a user message to JARVIS."""

    message: str = Field(..., min_length=1, description="User prompt or instruction")
    session_id: str | None = Field(default=None, description="Optional persistent session identifier")
    mode: str | None = Field(default="general", description="Agent persona or operational mode")


class ChatTurnResponse(BaseModel):
    """Execution outcome of a completed user turn."""

    response: str
    status: str
    verified: bool
    elapsed_ms: int
    evidence: str = ""
    error: str = ""


@router.post("", response_model=ChatTurnResponse)
def run_chat_turn(payload: ChatTurnRequest) -> dict[str, Any]:
    """Execute a complete agent turn against the canonical model gateway and tool runtime."""
    runtime = get_assistant_runtime()
    gateway = runtime.gateway

    # Register default tools if needed
    registry = get_tool_registry()
    if not registry.list_tools():
        register_default_tools(registry)

    tool_rt = ToolRuntime(registry=registry, default_workspace=runtime.layout.workspace_root)

    def tool_executor(tool_name: str, args: dict[str, Any]) -> tuple[str, bool]:
        res = tool_rt.execute(tool_name, args)
        return (res.output if res.is_success else res.error), res.is_success

    session = get_or_create_session(payload.session_id)
    if payload.mode:
        session.current_mode = payload.mode

    loop = AgentLoop(
        session=session,
        gateway=gateway,
        tool_executor=tool_executor,
    )

    result = loop.run_turn(payload.message)
    return {
        "response": result.response,
        "status": result.status.value,
        "verified": result.verified,
        "elapsed_ms": result.elapsed_ms,
        "evidence": result.evidence,
        "error": result.error,
    }


@router.get("/history")
def get_chat_history(session_id: str | None = None) -> dict[str, Any]:
    """Retrieve message history for an active session."""
    session = get_or_create_session(session_id)
    return {
        "session_id": session.session_id,
        "current_mode": session.current_mode,
        "history": session.get_recent_history(limit=50),
    }
