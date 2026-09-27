"""System information and operational metrics tools."""

from __future__ import annotations

import platform
import sys
from typing import Any

from jarvis.tools.contracts import (
    ToolContext,
    ToolDefinition,
    ToolResult,
    ToolRiskLevel,
)
from jarvis.tools.registry import ToolRegistry


def handle_system_status(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """Collect platform hardware, OS, and Python interpreter metadata."""
    info = {
        "platform": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "workspace": str(ctx.workspace_dir),
    }
    evidence = (
        f"Platform: {info['platform']} {info['release']} ({info['machine']}), "
        f"Python {info['python_version']}"
    )
    return ToolResult.ok(output=info, evidence=evidence)


def register_system_tools(registry: ToolRegistry) -> None:
    """Register system metric tools."""
    registry.register(
        ToolDefinition(
            name="system_status",
            description="Retrieve host system information, OS details, and Python environment status.",
            parameters=[],
            risk_level=ToolRiskLevel.LOW,
            capabilities=frozenset({"system", "diagnostics"}),
        ),
        handle_system_status,
    )
