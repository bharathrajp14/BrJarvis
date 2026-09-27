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
    """State machine states for a durable agent task."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


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
