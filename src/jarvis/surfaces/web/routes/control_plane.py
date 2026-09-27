"""Control plane aggregated summary endpoint resolving PERF-001."""

from __future__ import annotations

import platform
import sys
from typing import Any

from fastapi import APIRouter

from jarvis.core.bootstrap import get_assistant_runtime
from jarvis.core.version import VERSION
from jarvis.tools.registry import get_tool_registry

router = APIRouter(prefix="/api/v1/control-plane", tags=["control-plane"])


@router.get("/summary")
def get_control_plane_summary() -> dict[str, Any]:
    """Single aggregated summary endpoint delivering instant dashboard hydration."""
    runtime = get_assistant_runtime()
    doctor_info = runtime.doctor_report() if hasattr(runtime, "doctor_report") else {}
    registry = get_tool_registry()

    tools_summary = [
        {
            "name": t.name,
            "description": t.description,
            "risk_level": t.risk_level.value,
            "capabilities": list(t.capabilities),
        }
        for t in registry.list_tools()
    ]

    return {
        "status": "healthy",
        "version": VERSION,
        "environment": doctor_info.get("environment", "development"),
        "platform": {
            "system": platform.system(),
            "python": sys.version.split()[0],
            "machine": platform.machine(),
        },
        "gateway": doctor_info.get("gateway", {}),
        "tools": {
            "count": len(tools_summary),
            "items": tools_summary,
        },
        "tasks": {
            "active_count": 0,
            "recent": [],
        },
    }
