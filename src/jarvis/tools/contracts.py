"""Contracts, definitions, and result types for the canonical tool subsystem."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ToolRiskLevel(str, Enum):
    """Risk tiers for tool execution policies and approval interlocks."""

    # Canonical classes from Master Directive
    READ_ONLY = "read_only"
    LOW_RISK_WRITE = "low_risk_write"
    HIGH_RISK_WRITE = "high_risk_write"
    DESTRUCTIVE = "destructive"
    EXTERNAL_COMMUNICATION = "external_communication"
    CREDENTIAL_ACCESS = "credential_access"
    SYSTEM_CONTROL = "system_control"

    # Compatibility aliases
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def requires_approval(self) -> bool:
        """Whether actions with this risk tier require explicit user approval by default."""
        return self in {
            ToolRiskLevel.HIGH,
            ToolRiskLevel.CRITICAL,
            ToolRiskLevel.HIGH_RISK_WRITE,
            ToolRiskLevel.DESTRUCTIVE,
            ToolRiskLevel.CREDENTIAL_ACCESS,
            ToolRiskLevel.SYSTEM_CONTROL,
        }


@dataclass(slots=True)
class ToolResult:
    """Standardized, evidence-bearing output contract for every tool execution.

    Invariant: Every tool must return ToolResult; no bare strings or unhandled exceptions.
    """

    status: str
    output: Any = None
    error: str = ""
    evidence: str = ""
    artifacts: list[str] = field(default_factory=list)
    execution_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        output: Any,
        evidence: str = "",
        artifacts: list[str] | None = None,
        execution_ms: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        """Construct a successful ToolResult."""
        return cls(
            status="success",
            output=output,
            evidence=evidence or (str(output)[:200] if output is not None else "Operation succeeded"),
            artifacts=list(artifacts or []),
            execution_ms=execution_ms,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def err(
        cls,
        error: str,
        evidence: str = "",
        execution_ms: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        """Construct an error ToolResult."""
        return cls(
            status="error",
            error=str(error),
            evidence=evidence or f"Error: {error}",
            execution_ms=execution_ms,
            metadata=dict(metadata or {}),
        )

    @property
    def is_success(self) -> bool:
        """True if the tool succeeded."""
        return self.status == "success"

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return asdict(self)


@dataclass(slots=True)
class ToolParameter:
    """Schema descriptor for an individual tool argument."""

    name: str
    type_name: str
    description: str
    required: bool = True
    default: Any = None


@dataclass(slots=True)
class ToolDefinition:
    """Declarative specification and capability profile of a tool."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def to_prompt_schema(self) -> dict[str, Any]:
        """Convert definition to JSON-schema structure for prompt integration."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            properties[p.name] = {"type": p.type_name, "description": p.description}
            if p.required:
                required.append(p.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


@dataclass(slots=True)
class ToolContext:
    """Operational execution context passed to tool handlers."""

    workspace_dir: Path
    session_id: str = ""
    task_id: str = ""
    correlation_id: str = ""
    user_id: str = "default_user"
    approved: bool = True
    started_at: float = field(default_factory=time.time)
