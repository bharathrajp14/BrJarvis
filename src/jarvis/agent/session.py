"""Agent session management with multi-turn conversation tracking."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSession:
    """Represents an active interactive session between a user and JARVIS."""

    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    correlation_id: str = field(default_factory=lambda: f"corr_{uuid.uuid4().hex[:8]}")
    active_task_id: str | None = None
    active_task_label: str = ""
    current_mode: str = "general"
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_user_turn(self, content: str) -> None:
        """Append a user message turn."""
        self.history.append(
            {
                "role": "user",
                "content": content,
                "timestamp": time.time(),
            }
        )

    def add_assistant_turn(self, content: str, latency_ms: int = 0) -> None:
        """Append an assistant response turn."""
        self.history.append(
            {
                "role": "assistant",
                "content": content,
                "latency_ms": latency_ms,
                "timestamp": time.time(),
            }
        )

    def add_tool_turn(self, tool_name: str, args: dict[str, Any], result: Any, verified: bool) -> None:
        """Append a tool execution observation."""
        self.history.append(
            {
                "role": "tool",
                "tool": tool_name,
                "args": args,
                "result": result,
                "verified": verified,
                "timestamp": time.time(),
            }
        )

    def get_recent_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent conversation messages suitable for prompt construction."""
        return self.history[-limit:] if limit > 0 else list(self.history)

    def set_active_task(self, task_id: str, label: str = "") -> None:
        """Mark a task as currently active in this session."""
        self.active_task_id = task_id
        self.active_task_label = label

    def clear_active_task(self) -> None:
        """Clear active task binding."""
        self.active_task_id = None
        self.active_task_label = ""


_SESSION_REGISTRY: dict[str, AgentSession] = {}


def get_or_create_session(session_id: str | None = None) -> AgentSession:
    """Retrieve an existing session by ID or construct a new one."""
    if session_id and session_id in _SESSION_REGISTRY:
        return _SESSION_REGISTRY[session_id]
    new_sess = AgentSession(session_id=session_id or f"sess_{uuid.uuid4().hex[:8]}")
    _SESSION_REGISTRY[new_sess.session_id] = new_sess
    return new_sess
