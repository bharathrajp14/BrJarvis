# core/health.py — Hardware Metrics & Health Check Registry for JARVIS MK37
from __future__ import annotations

import logging
import shutil
import threading
import time
from typing import Callable, Dict, Optional

from pydantic import BaseModel, Field

try:
    import psutil

    _PSUTIL_AVAILABLE = True
    # Prime the CPU counter so the first call returns a real value (not 0.0)
    psutil.cpu_percent(interval=None)
except ImportError:
    _PSUTIL_AVAILABLE = False

from .native_bridge import get_status as get_native_status
from .native_bridge import is_native_active

logger = logging.getLogger("JARVIS.Health")

# Cache TTL in seconds — avoids hammering disk/OS on every request
_HARDWARE_CACHE_TTL = 5.0


class HardwareMetrics(BaseModel):
    cpu_percent: float = 0.0
    memory_used_percent: float = 0.0
    memory_available_mb: float = 0.0
    disk_used_percent: float = 0.0
    native_c_bridge_active: bool = False
    timestamp: float = Field(default_factory=time.time)


class ComponentHealth(BaseModel):
    name: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    message: str = "OK"
    latency_ms: Optional[float] = None


class HealthReport(BaseModel):
    overall_status: str  # HEALTHY, DEGRADED, UNHEALTHY
    hardware: HardwareMetrics
    components: Dict[str, ComponentHealth]


class HealthMonitor:
    """Monitors system hardware usage and manages component health checks."""

    def __init__(self):
        self._checkers: Dict[str, Callable[[], ComponentHealth]] = {}
        # Hardware metrics cache
        self._hw_cache: Optional[HardwareMetrics] = None
        self._hw_cache_ts: float = 0.0
        self._hw_lock = threading.Lock()

    def register_check(self, name: str, check_fn: Callable[[], ComponentHealth]) -> None:
        """Register a health check callback for a named component."""
        self._checkers[name] = check_fn

    def get_hardware_metrics(self, use_cache: bool = True) -> HardwareMetrics:
        """Collect current OS hardware utilization statistics.

        Results are cached for _HARDWARE_CACHE_TTL seconds to avoid blocking
        I/O on every call. Set use_cache=False to force a fresh reading.
        """
        with self._hw_lock:
            now = time.monotonic()
            if use_cache and self._hw_cache is not None and (now - self._hw_cache_ts) < _HARDWARE_CACHE_TTL:
                return self._hw_cache

            cpu = 0.0
            mem_pct = 0.0
            mem_avail_mb = 0.0

            if _PSUTIL_AVAILABLE:
                try:
                    # interval=0.1 returns a real measurement (not stale 0.0)
                    cpu = psutil.cpu_percent(interval=0.1)
                    mem = psutil.virtual_memory()
                    mem_pct = mem.percent
                    mem_avail_mb = mem.available / (1024 * 1024)
                except Exception as e:
                    logger.exception("Boot critical exception encountered in core/health.py")
                    raise e
            # Disk usage
            disk_pct = 0.0
            try:
                total, used, _ = shutil.disk_usage(".")
                disk_pct = (used / total) * 100.0
            except Exception as e:
                logger.exception("Boot critical exception encountered in core/health.py")
                raise e
            metrics = HardwareMetrics(
                cpu_percent=cpu,
                memory_used_percent=mem_pct,
                memory_available_mb=round(mem_avail_mb, 1),
                disk_used_percent=round(disk_pct, 1),
                native_c_bridge_active=is_native_active(),
            )
            self._hw_cache = metrics
            self._hw_cache_ts = now
            return metrics

    def generate_report(self) -> HealthReport:
        """Run all registered checks and return an aggregated HealthReport.

        This call is synchronous and may block briefly for CPU sampling.
        """
        hardware = self.get_hardware_metrics()
        components: Dict[str, ComponentHealth] = {}
        has_degraded = False
        has_unhealthy = False

        # Built-in check: Native C Bridge
        native_stat = get_native_status()
        components["c_native_bridge"] = ComponentHealth(
            name="c_native_bridge",
            status="HEALTHY" if native_stat["active"] else "DEGRADED",
            message=(f"Library v{native_stat['version']}" if native_stat["active"] else "Python Fallback Active"),
        )

        # Run all registered external checks
        for name, fn in self._checkers.items():
            try:
                t0 = time.perf_counter()
                res = fn()
                res.latency_ms = (time.perf_counter() - t0) * 1000.0
                components[name] = res
                if res.status == "DEGRADED":
                    has_degraded = True
                elif res.status == "UNHEALTHY":
                    has_unhealthy = True
            except Exception as exc:
                components[name] = ComponentHealth(name=name, status="UNHEALTHY", message=str(exc))
                has_unhealthy = True

        # Determine overall status
        overall = "HEALTHY"
        if has_unhealthy:
            overall = "UNHEALTHY"
        elif has_degraded or hardware.cpu_percent > 95.0 or hardware.memory_used_percent > 90.0:
            overall = "DEGRADED"

        return HealthReport(overall_status=overall, hardware=hardware, components=components)


_MONITOR: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Return the process-wide health monitor."""
    global _MONITOR
    if _MONITOR is None:
        _MONITOR = HealthMonitor()
    return _MONITOR


def get_health_report() -> Dict[str, float | str | bool]:
    """Return a JSON-serializable hardware snapshot for HTTP health routes."""
    report = get_health_monitor().generate_report()
    return {
        "cpu_percent": report.hardware.cpu_percent,
        "memory_percent": report.hardware.memory_used_percent,
        "disk_percent": report.hardware.disk_used_percent,
        "overall_status": report.overall_status,
        "native_c_bridge_active": report.hardware.native_c_bridge_active,
    }
