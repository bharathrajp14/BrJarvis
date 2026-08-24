# agent/task_state.py — Persistent Task State Machine for BR JARVIS
"""
Persistent task state machine and SQLite WAL checkpointing engine for Autonomous Agent Control Plane.
Tracks full lifecycle: Goal -> Planning -> Tool/Device Selection -> Execution -> Observe -> Verify -> Complete.
Supports pause, resume, cancel, retry, checkpoints, recovery, and approval gates.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from brjarvis.memory.canonical_db import get_canonical_db

logger = logging.getLogger("JARVIS.TaskState")


class ConcurrentTaskUpdateError(RuntimeError):
    """Raised when a stale task snapshot attempts to overwrite a newer one."""


class TaskStatus(str, Enum):

    CREATED = "CREATED"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    PREFLIGHT = "PREFLIGHT"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RUNNING = "RUNNING"
    RECOVERING = "RECOVERING"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPLETED_UNVERIFIED = "COMPLETED_UNVERIFIED"
    SUCCESS_VERIFIED = "SUCCESS_VERIFIED"
    # MK40.2 additions
    REQUIRES_USER = "REQUIRES_USER"  # needs human action to continue
    TASK_FAILED_RESULT_MISMATCH = "TASK_FAILED_RESULT_MISMATCH"  # result does not match requested goal

    # Backwards-compatible aliases
    PENDING = "CREATED"
    VALIDATING = "PREFLIGHT"
    PAUSED = "WAITING_FOR_USER"
    WAITING_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_DEVICE = "WAITING_FOR_APPROVAL"
    WAITING_FOR_AUTH = "WAITING_FOR_APPROVAL"
    RETRYING = "RECOVERING"
    VERIFYING = "RUNNING"
    COMPLETED = "SUCCESS_VERIFIED"
    PARTIAL = "PARTIAL_SUCCESS"


@dataclass
class TaskCriterion:
    """Discrete requirement criterion (e.g. C1 = PDF generated, C6 = Application window verified)."""

    criterion_id: str
    description: str
    required: bool = True
    status: str = "PENDING"  # PENDING, VERIFIED, FAILED, UNVERIFIED
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskCriterion:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TaskAction:
    action_id: str
    step_index: int
    tool: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    target_device: str = "pc"
    target_app: str = ""
    status: str = "pending"
    result: str = ""
    error: str = ""
    verified: bool = False
    verification_notes: str = ""
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskAction:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ApprovalRequest:
    request_id: str
    task_id: str
    action_id: str
    description: str
    risk_level: str = "medium"  # low, medium, high, critical
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalRequest:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TaskState:
    """Authoritative Single Source of Truth for Autonomous Task State."""

    task_id: str
    session_id: str = ""
    # ── Immutable goal fields — set once, never overwritten (MK40.2 §1, §2) ──
    user_request: str = ""  # IMMUTABLE: original user text verbatim
    normalized_request: str = ""  # IMMUTABLE: cleaned/normalized version set at creation
    goal: str = ""  # alias for user_request (backward compat)
    # ── MK40.2 goal contract fields ───────────────────────────────────────────
    required_operations: List[str] = field(default_factory=list)  # e.g. ["CREATE_PORTFOLIO", "PUSH_TO_GITHUB"]
    acceptance_criteria: List[Dict[str, Any]] = field(default_factory=list)  # serialized Criterion objects
    goal_spec: Dict[str, Any] = field(default_factory=dict)  # full GoalSpec serialized
    # ── Execution state ───────────────────────────────────────────────────────
    current_phase: str = "CREATED"
    current_step: int = 0
    total_steps: int = 0
    status: TaskStatus = TaskStatus.CREATED
    planned_steps: List[Dict[str, Any]] = field(default_factory=list)
    completed_steps: List[Dict[str, Any]] = field(default_factory=list)
    failed_steps: List[Dict[str, Any]] = field(default_factory=list)
    blocked_steps: List[Dict[str, Any]] = field(default_factory=list)
    pending_steps: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    applications: List[Dict[str, Any]] = field(default_factory=list)
    memory_updates: List[Dict[str, Any]] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)
    approvals: List[ApprovalRequest] = field(default_factory=list)
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)
    criteria: List[TaskCriterion] = field(default_factory=list)
    final_status: TaskStatus = TaskStatus.CREATED
    completion_evidence: str = ""
    request_id: str = ""
    parent_task_id: str = ""
    cancellation_requested: bool = False
    plan: Dict[str, Any] = field(default_factory=dict)
    active_agents: List[str] = field(default_factory=list)
    active_devices: List[str] = field(default_factory=lambda: ["pc"])
    actions: List[TaskAction] = field(default_factory=list)
    approval_request: Optional[ApprovalRequest] = None
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    error_info: Optional[Dict[str, Any]] = None
    final_report: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Monotonic persistence revision used for optimistic concurrency control.
    revision: int = 0

    def to_dict(self) -> Dict[str, Any]:

        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, TaskStatus) else str(self.status)
        d["final_status"] = (
            self.final_status.value if isinstance(self.final_status, TaskStatus) else str(self.final_status)
        )
        d["actions"] = [a.to_dict() if isinstance(a, TaskAction) else a for a in self.actions]
        d["criteria"] = [c.to_dict() if isinstance(c, TaskCriterion) else c for c in self.criteria]
        d["approvals"] = [a.to_dict() if isinstance(a, ApprovalRequest) else a for a in self.approvals]
        if self.approval_request:
            d["approval_request"] = (
                self.approval_request.to_dict()
                if isinstance(self.approval_request, ApprovalRequest)
                else self.approval_request
            )
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskState:
        raw = dict(data)
        if "status" in raw and isinstance(raw["status"], str):
            try:
                raw["status"] = (
                    TaskStatus[raw["status"].upper()]
                    if raw["status"].upper() in TaskStatus.__members__
                    else TaskStatus(raw["status"].upper())
                )
            except Exception:
                raw["status"] = TaskStatus.RUNNING if "RUN" in raw["status"].upper() else TaskStatus.CREATED
        if "final_status" in raw and isinstance(raw["final_status"], str):
            try:
                raw["final_status"] = (
                    TaskStatus[raw["final_status"].upper()]
                    if raw["final_status"].upper() in TaskStatus.__members__
                    else TaskStatus(raw["final_status"].upper())
                )
            except Exception:
                raw["final_status"] = TaskStatus.CREATED
        if "actions" in raw and isinstance(raw["actions"], list):
            raw["actions"] = [TaskAction.from_dict(a) if isinstance(a, dict) else a for a in raw["actions"]]
        if "criteria" in raw and isinstance(raw["criteria"], list):
            raw["criteria"] = [TaskCriterion.from_dict(c) if isinstance(c, dict) else c for c in raw["criteria"]]
        if "approvals" in raw and isinstance(raw["approvals"], list):
            raw["approvals"] = [ApprovalRequest.from_dict(a) if isinstance(a, dict) else a for a in raw["approvals"]]
        if "approval_request" in raw and isinstance(raw["approval_request"], dict):
            raw["approval_request"] = ApprovalRequest.from_dict(raw["approval_request"])
        return cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})


class TaskStateManager:
    """SQLite WAL-backed manager for persistent task states, steps, and checkpoints."""

    def __init__(self, db_manager=None, db_path: Optional[Path | str] = None):
        if db_path is not None:
            from brjarvis.memory.canonical_db import CanonicalDatabaseManager

            self.db_manager = CanonicalDatabaseManager(db_path=Path(db_path))
        else:
            self.db_manager = db_manager or get_canonical_db()

        # Serialize read-modify-write operations within a manager; the SQL
        # revision predicate also protects against races between processes.
        self._mutation_lock = threading.RLock()

    def _get_conn(self) -> sqlite3.Connection:

        return self.db_manager.get_connection()

    def create_task(
        self,
        goal: str,
        total_steps: int = 0,
        active_devices: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        goal_spec: Optional[Dict[str, Any]] = None,
    ) -> TaskState:
        """Initialize and persist a new autonomous task.

        MK40.2: user_request is stored verbatim and is NEVER overwritten after
        this point.  The CompletionGate compares the final executed artifacts
        against the original request to prevent result substitution.
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        now = time.time()
        devices = active_devices or ["pc"]

        # Normalize goal (strip extra whitespace, keep original verbatim)
        normalized = " ".join(goal.split())

        # Extract required_operations and acceptance_criteria from goal_spec if provided
        required_ops: List[str] = []
        acceptance: List[Dict[str, Any]] = []
        if goal_spec and isinstance(goal_spec, dict):
            required_ops = list(goal_spec.get("required_operations", []))
            acceptance = list(goal_spec.get("acceptance_criteria", []))

        state = TaskState(
            task_id=tid,
            user_request=goal,  # immutable — verbatim user text
            normalized_request=normalized,  # immutable — cleaned version
            goal=goal,  # backward-compat alias
            required_operations=required_ops,
            acceptance_criteria=acceptance,
            goal_spec=goal_spec or {},
            status=TaskStatus.CREATED,
            total_steps=total_steps,
            active_devices=devices,
            created_at=now,
            updated_at=now,
        )

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks (task_id, goal, status, current_step, total_steps, active_agents, active_devices, data_json, created_at, updated_at, revision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.task_id,
                    state.goal,
                    state.status.value,
                    state.current_step,
                    state.total_steps,
                    json.dumps(state.active_agents),
                    json.dumps(state.active_devices),
                    json.dumps(state.to_dict()),
                    state.created_at,
                    state.updated_at,
                    state.revision,
                ),
            )
            conn.commit()

        logger.info("Created Task [%s]: '%s'", state.task_id, goal[:60])
        return state

    def record_action(self, task_id: str, action: TaskAction) -> None:
        """Record an executed action to the task history."""
        task = self.get_task(task_id)
        if task:
            task.actions.append(action)
            task.current_step = max(task.current_step, action.step_index)
            self.save_task(task)

    def update_status(
        self, task_id: str, status: TaskStatus, error_info: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskState]:
        """Update overall task status with timestamp and optional error payload."""
        return self.update_task_status(task_id, status, error_info)

    def update_task_status(
        self, task_id: str, status: TaskStatus, error_info: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskState]:
        """Update overall task status with timestamp and optional error payload."""
        state = self.get_task(task_id)
        if not state:
            return None

        state.status = status
        state.updated_at = time.time()
        if error_info:
            state.error_info = error_info

        self.save_task(state)
        logger.info("Task [%s] transition -> %s", task_id, status.value if hasattr(status, "value") else status)
        return state

    def save_task(self, state: TaskState) -> None:
        """Persist a task snapshot only if its revision is still current."""
        with self._mutation_lock:
            state.updated_at = time.time()
            next_revision = int(state.revision) + 1
            state_json = state.to_dict()
            state_json["revision"] = next_revision
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET goal = ?, status = ?, current_step = ?, total_steps = ?,
                        active_agents = ?, active_devices = ?, data_json = ?,
                        updated_at = ?, revision = ?
                    WHERE task_id = ? AND revision = ?
                    """,
                    (
                        state.goal,
                        state.status.value if isinstance(state.status, TaskStatus) else str(state.status),
                        state.current_step,
                        state.total_steps,
                        json.dumps(state.active_agents),
                        json.dumps(state.active_devices),
                        json.dumps(state_json),
                        state.updated_at,
                        next_revision,
                        state.task_id,
                        state.revision,
                    ),
                )
                if cursor.rowcount != 1:
                    raise ConcurrentTaskUpdateError(
                        f"Task '{state.task_id}' changed since it was loaded; reload before saving."
                    )
                conn.commit()
            state.revision = next_revision

    def get_task(self, task_id: str) -> Optional[TaskState]:
        """Retrieve task by ID."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT data_json, revision FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["data_json"])
                data.setdefault("revision", int(row["revision"] or 0))
                return TaskState.from_dict(data)
            except Exception as e:
                logger.error("Error deserializing task [%s]: %s", task_id, e)
                return None

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[TaskState]:
        """List active and historical tasks."""
        with self._get_conn() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT data_json, revision FROM tasks WHERE status = ? ORDER BY updated_at DESC LIMIT ?", (status, limit)
                )
            else:
                cursor = conn.execute("SELECT data_json, revision FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            tasks = []
            for r in rows:
                try:
                    data = json.loads(r["data_json"])
                    data.setdefault("revision", int(r["revision"] or 0))
                    tasks.append(TaskState.from_dict(data))
                except Exception:
                    pass
            return tasks

    def record_step_wal(
        self,
        task_id: str,
        step_index: int,
        capability: str,
        parameters: Dict[str, Any],
        status: str = "running",
        result: Optional[Any] = None,
        error: Optional[str] = None,
        duration: float = 0.0,
        verified: bool = False,
    ) -> str:
        """Write-Ahead Log step transition to task_steps table before and after tool execution."""
        step_id = f"{task_id}_s{step_index}_{int(time.time() * 1000)}"
        now = time.time()
        with self._get_conn() as conn:
            # Ensure parent task exists to satisfy foreign key constraint
            conn.execute(
                """
                INSERT OR IGNORE INTO tasks (task_id, goal, status, current_step, total_steps, active_agents, active_devices, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    f"Auto-task {task_id}",
                    "running",
                    step_index,
                    0,
                    "[]",
                    '["pc"]',
                    json.dumps({"task_id": task_id, "goal": f"Auto-task {task_id}", "status": "running"}),
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO task_steps (step_id, task_id, step_index, capability, parameters_json, status, result_json, error_msg, verified, duration, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    task_id,
                    step_index,
                    capability,
                    json.dumps(parameters, default=str),
                    status,
                    json.dumps(result, default=str) if result is not None else None,
                    error,
                    1 if verified else 0,
                    duration,
                    now,
                    now,
                ),
            )
            conn.commit()
        return step_id

    def create_checkpoint(self, task_id: str, step_index: int) -> str:
        """Save a rollback checkpoint snapshot for the current step."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found for checkpoint")

        chk_id = f"chk_{task_id}_{step_index}_{int(time.time())}"
        snapshot_json = json.dumps(task.to_dict())

        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints (checkpoint_id, task_id, step_index, state_snapshot, created_at) VALUES (?, ?, ?, ?, ?)",
                (chk_id, task_id, step_index, snapshot_json, time.time()),
            )
            conn.commit()

        task.checkpoints.append({"checkpoint_id": chk_id, "step_index": step_index, "created_at": time.time()})
        self.save_task(task)
        logger.info("Saved Checkpoint [%s] at Step #%d for Task [%s]", chk_id, step_index, task_id)
        return chk_id

    def request_approval(
        self,
        task_id: str,
        action_id: str,
        description: str,
        risk_level: str = "medium",
        details: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequest:
        """Pause task execution and register an approval gate."""
        req_id = f"appr_{uuid.uuid4().hex[:8]}"
        req = ApprovalRequest(
            request_id=req_id,
            task_id=task_id,
            action_id=action_id,
            description=description,
            risk_level=risk_level,
            details=details or {},
        )

        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.WAITING_FOR_APPROVAL
            task.approval_request = req
            self.save_task(task)

        logger.warning("Approval Required for Task [%s]: %s (Risk: %s)", task_id, description, risk_level)
        return req

    def resolve_approval(self, task_id: str, request_id: str, approved: bool) -> Optional[TaskState]:
        """Approve or reject a pending approval request."""
        task = self.get_task(task_id)
        if not task or not task.approval_request:
            return None

        if task.approval_request.request_id == request_id:
            task.approval_request.status = "approved" if approved else "rejected"
            task.approval_request.resolved_at = time.time()
            task.status = TaskStatus.RUNNING if approved else TaskStatus.CANCELLED
            self.save_task(task)
            logger.info("Resolved Approval [%s] for Task [%s]: %s", request_id, task_id, task.approval_request.status)
            return task
        return None


_GLOBAL_TASK_STATE_MGR: Optional[TaskStateManager] = None


def get_task_state_manager() -> TaskStateManager:
    """Return the global TaskStateManager instance."""
    global _GLOBAL_TASK_STATE_MGR
    if _GLOBAL_TASK_STATE_MGR is None:
        _GLOBAL_TASK_STATE_MGR = TaskStateManager()
    return _GLOBAL_TASK_STATE_MGR
