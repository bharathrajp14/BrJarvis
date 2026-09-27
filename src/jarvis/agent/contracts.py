"""Contracts, data structures, and status enums for the rebuilt jarvis agent package."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentTurnStatus(str, Enum):
    """Terminal state classifications for an agent interaction turn."""

    SUCCESS_VERIFIED = "success_verified"
    SUCCESS_UNVERIFIED = "success_unverified"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class TaskStatus(str, Enum):
    """Rigorous 14-state task lifecycle state machine."""

    CREATED = "created"
    QUEUED = "queued"
    PLANNING = "planning"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    WAITING_FOR_USER = "waiting_for_user"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"

    # Backward-compatible aliases
    WAITING_APPROVAL = "waiting_for_approval"
    PARTIAL = "partial"

    @classmethod
    def _missing_(cls, value: object) -> TaskStatus | None:
        if isinstance(value, str):
            val_norm = value.strip().lower()
            if val_norm == "waiting_approval":
                return cls.WAITING_FOR_APPROVAL
            for member in cls:
                if member.value == val_norm or member.name.lower() == val_norm:
                    return member
        return None


class LedgerStatus(str, Enum):
    """Execution status for ledger entries."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PENDING = "PENDING"


@dataclass(slots=True)
class AgentTurnResult:
    """Typed result produced at the end of an autonomous agent turn."""

    response: str
    status: AgentTurnStatus
    verified: bool
    elapsed_ms: int
    error: str = ""
    tool_failures: int = 0
    evidence: str = ""
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
