"""Central registry for tool definitions and executable handlers."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from .contracts import ToolContext, ToolDefinition, ToolResult

ToolHandler = Callable[[ToolContext, dict[str, Any]], ToolResult]


class ToolRegistry:
    """Thread-safe registry mapping tool names to definitions and handlers."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        """Register a new tool definition and its execution handler."""
        self._tools[definition.name] = (definition, handler)

    def get(self, name: str) -> tuple[ToolDefinition, ToolHandler] | None:
        """Look up a tool definition and handler by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tool specifications."""
        return [defn for defn, _ in self._tools.values()]

    def export_prompt_catalog(self) -> str:
        """Export all registered tools formatted as a markdown prompt catalog."""
        if not self._tools:
            return "No tools currently registered."

        lines = ["## Available Tools:", ""]
        for defn, _ in self._tools.values():
            schema = defn.to_prompt_schema()
            lines.append(f"### `{defn.name}` [{defn.risk_level.value.upper()}]")
            lines.append(f"{defn.description}")
            lines.append("```json")
            lines.append(json.dumps(schema["parameters"], indent=2))
            lines.append("```")
            lines.append("")

        return "\n".join(lines)


_GLOBAL_REGISTRY: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Retrieve the shared process-wide tool registry."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ToolRegistry()
    return _GLOBAL_REGISTRY
