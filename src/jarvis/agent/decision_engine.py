"""Decision engine with machine-readable receipts and pre-action consistency validation."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DecisionRecord:
    """Represents a recorded architectural or tactical decision."""

    decision_id: str
    question: str
    goal: str
    selected_option: str
    rejected_options: list[str]
    evidence: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_receipt(self) -> dict[str, Any]:
        """Convert decision to a machine-readable receipt."""
        return asdict(self)


class DecisionEngine:
    """Maintains an auditable record of system decisions and guards against regression."""

    def __init__(self) -> None:
        self._decisions: list[DecisionRecord] = []

    def record_decision(
        self,
        question: str,
        goal: str,
        selected_option: str,
        rejected_options: list[str] | None = None,
        evidence: str = "",
        confidence: float = 1.0,
    ) -> DecisionRecord:
        """Record an explicit decision with evidence and options considered."""
        dec = DecisionRecord(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            question=question,
            goal=goal,
            selected_option=selected_option,
            rejected_options=rejected_options or [],
            evidence=evidence,
            confidence=confidence,
        )
        self._decisions.append(dec)
        return dec

    def get_decision(self, decision_id: str) -> DecisionRecord | None:
        """Find a decision by its ID."""
        for d in self._decisions:
            if d.decision_id == decision_id:
                return d
        return None

    def get_recent_decisions(self, limit: int = 20) -> list[DecisionRecord]:
        """Return the most recent decisions."""
        return list(reversed(self._decisions[-limit:]))

    def validate_action_against_decisions(self, proposed_action: str) -> tuple[bool, str]:
        """Validate if a proposed action contradicts any previously rejected option.

        Returns (True, "") if compliant, or (False, reason) if conflicting.
        """
        action_lower = proposed_action.lower()
        for dec in self._decisions:
            for rejected in dec.rejected_options:
                if rejected.lower() in action_lower:
                    return (
                        False,
                        f"Action '{proposed_action}' conflicts with Decision {dec.decision_id}: "
                        f"rejected '{rejected}' in favor of '{dec.selected_option}'.",
                    )
        return (True, "")


_GLOBAL_DECISION_ENGINE: DecisionEngine | None = None


def get_decision_engine() -> DecisionEngine:
    """Retrieve the global decision engine singleton."""
    global _GLOBAL_DECISION_ENGINE
    if _GLOBAL_DECISION_ENGINE is None:
        _GLOBAL_DECISION_ENGINE = DecisionEngine()
    return _GLOBAL_DECISION_ENGINE
