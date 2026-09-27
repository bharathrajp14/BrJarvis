"""Execution runtime for dispatching and safeguarding tool invocations."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from .contracts import ToolContext, ToolResult, ToolRiskLevel
from .registry import ToolRegistry, get_tool_registry

logger = logging.getLogger("jarvis.tools.runtime")


class ToolRuntime:
    """Safeguarded execution environment for tool invocations."""

    def __init__(self, registry: ToolRegistry | None = None, default_workspace: Path | None = None) -> None:
        self.registry = registry or get_tool_registry()
        self.default_workspace = default_workspace or Path.cwd()

    def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Safely execute a tool with argument validation and error containment."""
        t0 = time.monotonic()
        entry = self.registry.get(tool_name)
        if entry is None:
            elapsed = int((time.monotonic() - t0) * 1000)
            return ToolResult.err(
                error=f"Tool '{tool_name}' is not recognized.",
                evidence=f"Tool not found: {tool_name}",
                execution_ms=elapsed,
            )

        definition, handler = entry
        ctx = context or ToolContext(workspace_dir=self.default_workspace)

        # Check required parameters
        missing = [p.name for p in definition.parameters if p.required and p.name not in args]
        if missing:
            elapsed = int((time.monotonic() - t0) * 1000)
            return ToolResult.err(
                error=f"Missing required arguments for '{tool_name}': {', '.join(missing)}",
                evidence=f"Validation failed: missing {missing}",
                execution_ms=elapsed,
            )

        # High/Critical risk approval check
        if definition.risk_level in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL} and not ctx.approved:
            elapsed = int((time.monotonic() - t0) * 1000)
            return ToolResult(
                status="waiting_approval",
                error=f"Action '{tool_name}' requires explicit user confirmation.",
                evidence="Execution halted pending approval",
                execution_ms=elapsed,
            )

        # Execute handler with exception containment
        try:
            result = handler(ctx, args)
            result.execution_ms = int((time.monotonic() - t0) * 1000)
            return result
        except Exception as exc:
            elapsed = int((time.monotonic() - t0) * 1000)
            logger.error("Error executing tool '%s': %s", tool_name, exc, exc_info=True)
            # Prevent raw stack traces from polluting the agent prompt (SEC-004)
            safe_error_msg = f"Tool execution failed: {type(exc).__name__} ({str(exc)[:120]})"
            return ToolResult.err(
                error=safe_error_msg,
                evidence=f"Tool error in {tool_name}",
                execution_ms=elapsed,
            )
