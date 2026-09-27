"""Durable task state machine with optimistic concurrency revision tracking."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import TaskStatus


@dataclass(slots=True)
class TaskState:
    """Represents the persisted, durable state of a running or completed task."""

    task_id: str
    user_request: str
    status: TaskStatus = TaskStatus.CREATED
    current_step: int = 0
    total_steps: int = 0
    revision: int = 0
    actions: list[dict[str, Any]] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize state machine to a plain dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskState:
        """Hydrate state machine from a dictionary."""
        data_copy = dict(data)
        if "status" in data_copy and isinstance(data_copy["status"], str):
            data_copy["status"] = TaskStatus(data_copy["status"])
        return cls(**data_copy)

    def transition(self, new_status: TaskStatus, reason: str = "") -> None:
        """Perform a state transition, updating timestamp."""
        self.status = new_status
        self.updated_at = time.time()
        if reason:
            self.evidence.append(f"Status changed to {new_status.value}: {reason}")

    def advance_step(self, action_info: dict[str, Any] | None = None) -> None:
        """Increment current step and record optional action detail."""
        self.current_step += 1
        self.updated_at = time.time()
        if action_info:
            self.actions.append(action_info)

    def record_action(self, tool_name: str, args: dict[str, Any], result: str, verified: bool) -> None:
        """Record a completed tool action in the task history."""
        self.actions.append({
            "step": self.current_step,
            "tool": tool_name,
            "args": args,
            "result": result,
            "verified": verified,
            "timestamp": time.time(),
        })
        self.updated_at = time.time()

    def create_checkpoint(self, label: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate a restorable checkpoint snapshot."""
        cp = {
            "checkpoint_id": f"cp_{len(self.checkpoints) + 1}",
            "label": label,
            "step": self.current_step,
            "status": self.status.value,
            "revision": self.revision,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self.checkpoints.append(cp)
        self.updated_at = time.time()
        return cp
