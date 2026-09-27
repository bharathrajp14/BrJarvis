# api/routes/health.py — Health and Telemetry Endpoints
from __future__ import annotations

import platform
import time

from fastapi import APIRouter

from ..state import get_orchestrator

router = APIRouter(tags=["Health"])


def _hardware_metrics() -> dict[str, float]:
    """Return live hardware readings, or zeros when metrics are unavailable."""
    try:
        from brjarvis.core.health import get_health_report

        report = get_health_report()
        return {
            "cpu_percent": float(report.get("cpu_percent") or 0.0),
            "memory_percent": float(report.get("memory_percent") or 0.0),
            "disk_percent": float(report.get("disk_percent") or 0.0),
        }
    except Exception:
        return {"cpu_percent": 0.0, "memory_percent": 0.0, "disk_percent": 0.0}


@router.get("/health")
@router.get("/api/health")
async def health_check():
    """Return health metrics and hardware telemetry."""
    metrics = _hardware_metrics()
    return {
        "status": "online",
        "cpu_percent": metrics["cpu_percent"],
        "memory_percent": metrics["memory_percent"],
        "disk_percent": metrics["disk_percent"],
        "timestamp": time.time(),
    }


@router.get("/api/status")
async def get_status():
    """Return platform status and active backend."""
    metrics = _hardware_metrics()
    backend_str = None
    mode_str = None
    try:
        orch = get_orchestrator()
        if orch and getattr(orch, "router", None):
            default_backend = getattr(orch.router, "default", None)
            backend_str = getattr(default_backend, "value", default_backend)
            mode_str = getattr(orch, "current_mode", None)
    except Exception:
        pass

    return {
        "status": "online",
        "cpu": metrics["cpu_percent"],
        "ram": metrics["memory_percent"],
        "disk": metrics["disk_percent"],
        "backend": backend_str,
        "mode": mode_str,
        "time": time.strftime("%I:%M %p"),
        "os": platform.system(),
    }
