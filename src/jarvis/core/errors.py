"""Structured exceptions shared by the rebuilt runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class JarvisError(Exception):
    """Base exception for expected runtime failures."""


class ConfigurationError(JarvisError):
    """Raised when startup configuration is invalid."""


@dataclass(slots=True)
class TaskExecutionDiagnostic:
    """Machine-readable evidence for a task outcome."""

    task_id: str
    status: str
    message: str
    stage: str | None = None
    error_type: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable diagnostic envelope."""
        return asdict(self)

    @classmethod
    def failure(
        cls, task_id: str, message: str, *, stage: str | None = None, error: Exception | None = None
    ) -> "TaskExecutionDiagnostic":
        """Build a failure diagnostic without exposing secret values."""
        return cls(
            task_id=task_id,
            status="FAILED",
            message=message,
            stage=stage,
            error_type=type(error).__name__ if error else None,
        )
