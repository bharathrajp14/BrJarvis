"""Jarvis Tools subsystem: standardized contracts, registry, runtime, and builtin tools."""

from __future__ import annotations

from .bridge import LegacyToolBridge, bridge_legacy_tools
from .builtin import register_default_tools
from .contracts import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    ToolRiskLevel,
)
from .registry import ToolHandler, ToolRegistry, get_tool_registry
from .runtime import ToolRuntime

__all__ = [
    "LegacyToolBridge",
    "ToolContext",
    "ToolDefinition",
    "ToolHandler",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
    "ToolRiskLevel",
    "ToolRuntime",
    "bridge_legacy_tools",
    "get_tool_registry",
    "register_default_tools",
]
