# core/intent_models.py — Data contracts for Atomic & Composite Intent Classification
"""
Data contracts for Request Atomicity, Composite Multi-Intent Decomposition,
and Execution Tracing in BR JARVIS.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AtomicIntentResult:
    """Represents the structured result of an atomic intent classification."""

    matched: bool = False
    atomic: bool = False
    intent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    consumed_text: str = ""
    remaining_text: str = ""
    confidence: float = 0.0
    requires_planner: bool = False
    action_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionIntent:
    """Represents a single executable action inside a composite intent."""

    intent: str
    order: int
    raw_text: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    action_type: str = ""
    is_negated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompositeIntent:
    """Represents a composite multi-step user request containing ordered actions."""

    original_text: str
    actions: List[ActionIntent] = field(default_factory=list)
    dependencies: List[Any] = field(default_factory=list)
    confidence: float = 0.0
    requires_planner: bool = True
    is_negated_clause_present: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "actions": [a.to_dict() for a in self.actions],
            "dependencies": self.dependencies,
            "confidence": self.confidence,
            "requires_planner": self.requires_planner,
            "is_negated_clause_present": self.is_negated_clause_present,
        }


@dataclass
class ExecutionTrace:
    """
    Structured execution trace recorded for every user request.
    Enforces observability across deterministic, composite, and planned paths.
    """

    user_input: str
    classification: str  # "atomic" | "composite" | "conversational" | "negated"
    atomic: bool
    deterministic: bool
    intent: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    planner_required: bool = False
    execution_started: float = field(default_factory=time.time)
    execution_completed: Optional[float] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_input": self.user_input,
            "classification": self.classification,
            "atomic": self.atomic,
            "deterministic": self.deterministic,
            "intent": self.intent,
            "steps": self.steps,
            "planner_required": self.planner_required,
            "execution_started": self.execution_started,
            "execution_completed": self.execution_completed,
            "success": self.success,
            "details": self.details,
        }
