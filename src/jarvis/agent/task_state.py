"""Durable task state machine with optimistic concurrency revision tracking."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import TaskStatus


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_status: TaskStatus, to_status: TaskStatus, reason: str = "") -> None:
        msg = f"Invalid task state transition: {from_status.value} -> {to_status.value}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.from_status = from_status
        self.to_status = to_status


# Valid state transitions matrix enforcing the canonical 14-state lifecycle
VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {
        TaskStatus.QUEUED,
        TaskStatus.PLANNING,
        TaskStatus.RUNNING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.QUEUED: {
        TaskStatus.PLANNING,
        TaskStatus.RUNNING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.PLANNING: {
        TaskStatus.WAITING_FOR_APPROVAL,
        TaskStatus.RUNNING,
        TaskStatus.WAITING_FOR_USER,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.WAITING_FOR_APPROVAL: {
        TaskStatus.RUNNING,
        TaskStatus.PLANNING,
        TaskStatus.CANCELLED,
        TaskStatus.FAILED,
    },
    TaskStatus.RUNNING: {
        TaskStatus.PLANNING,
        TaskStatus.WAITING_FOR_TOOL,
        TaskStatus.WAITING_FOR_USER,
        TaskStatus.WAITING_FOR_APPROVAL,
        TaskStatus.VERIFYING,
        TaskStatus.RECOVERING,
        TaskStatus.PAUSED,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.ROLLED_BACK,
        TaskStatus.PARTIAL,
    },
    TaskStatus.WAITING_FOR_TOOL: {
        TaskStatus.RUNNING,
        TaskStatus.VERIFYING,
        TaskStatus.RECOVERING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.WAITING_FOR_USER: {
        TaskStatus.RUNNING,
        TaskStatus.PLANNING,
        TaskStatus.PAUSED,
        TaskStatus.CANCELLED,
        TaskStatus.FAILED,
    },
    TaskStatus.VERIFYING: {
        TaskStatus.COMPLETED,
        TaskStatus.RECOVERING,
        TaskStatus.FAILED,
        TaskStatus.ROLLED_BACK,
        TaskStatus.RUNNING,
    },
    TaskStatus.RECOVERING: {
        TaskStatus.PLANNING,
        TaskStatus.RUNNING,
        TaskStatus.VERIFYING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.ROLLED_BACK,
    },
    TaskStatus.PAUSED: {
        TaskStatus.RUNNING,
        TaskStatus.PLANNING,
        TaskStatus.QUEUED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.ROLLED_BACK: {
        TaskStatus.RECOVERING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: {
        TaskStatus.QUEUED,
        TaskStatus.PLANNING,
    },
    TaskStatus.FAILED: {
        TaskStatus.QUEUED,
        TaskStatus.PLANNING,
        TaskStatus.RECOVERING,
    },
    TaskStatus.CANCELLED: {
        TaskStatus.QUEUED,
        TaskStatus.PLANNING,
    },
    TaskStatus.PARTIAL: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.RECOVERING,
        TaskStatus.QUEUED,
    },
}


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
    events: list[dict[str, Any]] = field(default_factory=list)
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
        if "events" not in data_copy:
            data_copy["events"] = []
        return cls(**data_copy)

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Verify whether transition to new_status is valid under the state machine policy."""
        if self.status == new_status:
            return True
        allowed = VALID_TRANSITIONS.get(self.status, set())
        return new_status in allowed

    def transition(self, new_status: TaskStatus, reason: str = "", force: bool = False) -> None:
        """Perform a validated state transition, recording timestamp and event trail."""
        if not force and not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(self.status, new_status, reason)

        old_status = self.status
        self.status = new_status
        now = time.time()
        self.updated_at = now

        event = {
            "event_id": f"evt_{len(self.events) + 1}",
            "task_id": self.task_id,
            "from_status": old_status.value,
            "to_status": new_status.value,
            "revision": self.revision,
            "reason": reason,
            "timestamp": now,
        }
        self.events.append(event)

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
        self.actions.append(
            {
                "step": self.current_step,
                "tool": tool_name,
                "args": args,
                "result": result,
                "verified": verified,
                "timestamp": time.time(),
            }
        )
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
