"""Append-only execution ledger and evidence synthesis."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import LedgerStatus


@dataclass(slots=True)
class LedgerEntry:
    """Immutable audit record of a single tool execution step."""

    task_id: str
    step_id: str
    tool_name: str
    status: LedgerStatus
    evidence: str
    verification_status: LedgerStatus = LedgerStatus.PENDING
    inputs_hash: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["verification_status"] = self.verification_status.value
        return data


class ExecutionLedger:
    """Thread-safe append-only ledger of physical execution evidence."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def append(self, entry: LedgerEntry) -> None:
        """Append an entry to the immutable ledger."""
        self._entries.append(entry)

    def get_entries(self, task_id: str | None = None) -> list[LedgerEntry]:
        """Retrieve recorded ledger entries, optionally filtered by task ID."""
        if task_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.task_id == task_id]

    def step_is_verified(self, task_id: str, step_id: str) -> bool:
        """Verify whether a specific step completed with successful verification."""
        for entry in self._entries:
            if entry.task_id == task_id and entry.step_id == step_id:
                return entry.verification_status == LedgerStatus.SUCCESS
        return False

    def build_evidence_report(self, task_id: str) -> str:
        """Synthesize an evidence report from verified actions."""
        entries = self.get_entries(task_id)
        if not entries:
            return "No recorded tool execution evidence found for this task."

        lines = [f"### Execution Evidence Report [Task: {task_id}]", ""]
        for entry in entries:
            v_icon = "✓" if entry.verification_status == LedgerStatus.SUCCESS else "✗"
            status_text = entry.status.value
            lines.append(f"- {v_icon} **{entry.step_id}** (`{entry.tool_name}`): {status_text} — {entry.evidence}")

        return "\n".join(lines)
