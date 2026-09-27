"""Durable task state machine with optimistic concurrency revision tracking."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
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
    user_request: str = ""
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

    def __init__(
        self,
        task_id: str,
        user_request: str = "",
        *,
        description: str = "",
        status: TaskStatus = TaskStatus.CREATED,
        current_step: int = 0,
        total_steps: int = 0,
        revision: int = 0,
        actions: list[dict[str, Any]] | None = None,
        checkpoints: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
        evidence: list[str] | None = None,
        created_at: float | None = None,
        updated_at: float | None = None,
        **kwargs: Any,
    ) -> None:
        self.task_id = task_id
        self.user_request = user_request or description or kwargs.get("user_request", "")
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        self.current_step = current_step
        self.total_steps = total_steps
        self.revision = revision
        self.actions = list(actions) if actions is not None else []
        self.checkpoints = list(checkpoints) if checkpoints is not None else []
        self.events = list(events) if events is not None else []
        self.evidence = list(evidence) if evidence is not None else []
        self.created_at = created_at if created_at is not None else time.time()
        self.updated_at = updated_at if updated_at is not None else time.time()

    @property
    def steps(self) -> list[str]:
        """User-readable steps list."""
        return [str(a.get("action", a)) for a in self.actions]

    def add_step(self, step_desc: str) -> None:
        """Add a high-level step."""
        self.advance_step({"action": step_desc})

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


class TaskStateStore:
    """Durable file-backed task state storage for restart recovery."""

    def __init__(self, storage_dir: Path | str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: TaskState) -> Path:
        path = self.storage_dir / f"{state.task_id}.json"
        path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
        return path

    def load(self, task_id: str) -> TaskState | None:
        path = self.storage_dir / f"{task_id}.json"
        if not path.is_file():
            return None
        return TaskState.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_tasks(self) -> list[str]:
        return [p.stem for p in self.storage_dir.glob("*.json")]

