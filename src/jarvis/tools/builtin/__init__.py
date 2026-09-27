"""Builtin tool modules for the rebuilt jarvis.tools package."""

from __future__ import annotations

from jarvis.tools.registry import ToolRegistry

from .fs import register_fs_tools
from .system import register_system_tools
from .terminal import register_terminal_tools


def register_default_tools(registry: ToolRegistry) -> None:
    """Register all standard builtin tools into the registry."""
    register_fs_tools(registry)
    register_terminal_tools(registry)
    register_system_tools(registry)


__all__ = [
    "register_default_tools",
    "register_fs_tools",
    "register_system_tools",
    "register_terminal_tools",
]
