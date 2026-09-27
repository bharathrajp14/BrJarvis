# core/intent_models.py — Data contracts for Universal Intent Arbitration & Execution
"""
Data contracts for Request Understanding, Atomicity Classification,
Action Plans, Authorization, Execution Records, and Observability in BR JARVIS.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AtomicityType(str, Enum):
    """Canonical 10-tier atomicity classification for user requests."""

    ATOMIC = "ATOMIC"
    COMPOSITE = "COMPOSITE"
    CONDITIONAL = "CONDITIONAL"
    ITERATIVE = "ITERATIVE"
    AMBIGUOUS = "AMBIGUOUS"
    INFORMATIONAL = "INFORMATIONAL"
    HYPOTHETICAL = "HYPOTHETICAL"
    NEGATED = "NEGATED"
    CONVERSATIONAL = "CONVERSATIONAL"
    UNSUPPORTED = "UNSUPPORTED"


class ExecutionMode(str, Enum):
    """Execution coordination mode across actions."""

    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"
    FALLBACK = "FALLBACK"


class RiskLevel(str, Enum):
    """Safety and impact risk classification for actions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionState(str, Enum):
    """Truthful user-facing execution lifecycle states."""

    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ── Backward Compatibility Contracts ─────────────────────────────────────────


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


# ── Canonical Universal Intent Architecture Contracts ─────────────────────────


@dataclass
class ProposedAction:
    """Represents an individual proposed action inside an ActionPlan."""

    action_id: str = field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    intent: str = ""
    tool: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    order: int = 1
    raw_text: str = ""
    depends_on: List[str] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    is_negated: bool = False
    is_conditional: bool = False
    condition_expr: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    verification_strategy: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["execution_mode"] = self.execution_mode.value
        d["risk_level"] = self.risk_level.value
        return d


@dataclass
class ActionPlan:
    """Canonical ActionPlan representing the complete decomposition of a user request."""

    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    original_text: str = ""
    actions: List[ProposedAction] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    dag: Dict[str, List[str]] = field(default_factory=dict)  # action_id -> [dependency_action_ids]
    atomicity: AtomicityType = AtomicityType.ATOMIC
    requires_confirmation: bool = False
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "original_text": self.original_text,
            "actions": [a.to_dict() for a in self.actions],
            "execution_mode": self.execution_mode.value,
            "dag": self.dag,
            "atomicity": self.atomicity.value,
            "requires_confirmation": self.requires_confirmation,
            "is_valid": self.is_valid,
        }


@dataclass
class AuthorizedActionPlan:
    """Authorized plan approved by the ActionAuthorizationEngine."""

    plan_id: str
    authorized: bool
    actions: List[ProposedAction] = field(default_factory=list)
    denial_reasons: List[str] = field(default_factory=list)
    requires_user_approval: bool = False
    approval_granted: bool = False
    authorization_token: str = field(default_factory=lambda: f"auth_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "authorized": self.authorized,
            "actions": [a.to_dict() for a in self.actions],
            "denial_reasons": self.denial_reasons,
            "requires_user_approval": self.requires_user_approval,
            "approval_granted": self.approval_granted,
            "authorization_token": self.authorization_token,
        }


@dataclass
class ActionExecutionRecord:
    """
    Transactional execution record created BEFORE any side-effect occurs.
    Enforces: EXECUTE -> OBSERVE -> VERIFY -> RECORD.
    """

    request_id: str
    task_id: str
    action_id: str
    intent: str
    tool: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    authorization: bool = False
    risk: str = "LOW"
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: str = "PENDING"  # PENDING | EXECUTING | VERIFYING | COMPLETED | FAILED | SKIPPED
    observation: Any = None
    verification: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RequestUnderstanding:
    """
    Canonical structured representation of full user request understanding.
    Produced exclusively by RequestUnderstandingEngine before any action authorization.
    """

    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:10]}")
    raw_input: str = ""
    normalized_input: str = ""
    language: str = "en"
    intent_type: str = "unknown"
    atomicity: AtomicityType = AtomicityType.AMBIGUOUS
    confidence: float = 0.0
    action_count: int = 0
    actions: List[ProposedAction] = field(default_factory=list)
    dependencies: List[Any] = field(default_factory=list)
    ordering: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    negations: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    unresolved_parts: List[str] = field(default_factory=list)
    ignored_parts: List[str] = field(default_factory=list)
    requires_planner: bool = False
    requires_clarification: bool = False
    requires_confirmation: bool = False
    deterministic_eligible: bool = False
    risk_level: str = "LOW"
    privacy_level: str = "PUBLIC"
    completeness_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["atomicity"] = self.atomicity.value
        d["actions"] = [a.to_dict() for a in self.actions]
        return d


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


@dataclass
class IntentCandidate:
    """
    Pure classifier / extractor output from DeterministicSignalExtractor.
    Represents semantic candidate signals extracted from the request without any side effects.
    """

    matched: bool = False
    intent: Optional[str] = None
    action_type: str = ""
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)
    app_names: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    command_vocab: List[str] = field(default_factory=list)
    confidence: float = 0.0
    consumed_text: str = ""
    remaining_text: str = ""
    is_negated: bool = False
    is_question: bool = False
    is_composite: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RequestResult:
    """
    Canonical structured result returned for every request by the unified agent runtime.
    """

    request_id: str
    task_id: str
    status: str
    response: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    execution_trace: Dict[str, Any] = field(default_factory=dict)
    verification: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    memory_updates: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    provider_usage: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

