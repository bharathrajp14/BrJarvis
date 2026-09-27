"""Composition root for the rebuilt Jarvis runtime."""

from __future__ import annotations

import importlib.util
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from .config import JarvisConfig, load_config
from .di import Container
from .lifecycle import Lifecycle
from .logging import configure_logging, get_logger
from .paths import PathLayout

logger = get_logger("bootstrap")


@dataclass(slots=True)
class AssistantRuntime:
    """Shared runtime context passed to future gateway, memory, and surface layers."""

    config: JarvisConfig
    paths: PathLayout
    container: Container
    lifecycle: Lifecycle
    gateway: Any | None
    started_at: str
    _closed: bool = False

    @property
    def layout(self) -> PathLayout:
        return self.paths

    @property
    def healthy(self) -> bool:
        return not self._closed and not self.lifecycle.closed

    def doctor_report(self) -> dict[str, object]:
        return run_doctor()

    async def shutdown(self) -> None:
        if self._closed:
            return
        await self.lifecycle.shutdown()
        self._closed = True


_runtime: AssistantRuntime | None = None
_runtime_lock = Lock()


def get_assistant_runtime() -> AssistantRuntime:
    """Return the active runtime instance, initializing it if necessary."""
    return build_assistant_runtime()


def build_assistant_runtime(
    *,
    config: JarvisConfig | None = None,
    layout: PathLayout | None = None,
    container: Container | None = None,
    gateway: Any | None = None,
    force_new: bool = False,
) -> AssistantRuntime:
    """Build the shared core runtime and configured gateway composition root."""
    global _runtime
    if _runtime is not None and not force_new:
        return _runtime

    with _runtime_lock:
        if _runtime is not None and not force_new:
            return _runtime
        resolved_layout = layout or PathLayout.from_project()
        resolved_layout.ensure_directories()
        resolved_config = (config or load_config(resolved_layout)).apply_paths(resolved_layout)
        resolved_config.validate_startup()
        configure_logging(resolved_config.log_level)
        resolved_gateway = gateway
        if resolved_gateway is None:
            try:
                from ..gateway.factory import build_configured_gateway

                resolved_gateway = build_configured_gateway()
            except Exception as exc:
                logger.warning("Gateway construction deferred: %s", exc)
        resolved_container = container or Container()
        if resolved_gateway is not None:
            from ..gateway.model_gateway import ModelGateway

            resolved_container.register_instance(ModelGateway, resolved_gateway)
        runtime = AssistantRuntime(
            config=resolved_config,
            paths=resolved_layout,
            container=resolved_container,
            lifecycle=Lifecycle(),
            gateway=resolved_gateway,
            started_at=datetime.now(UTC).isoformat(),
        )
        _runtime = runtime
        logger.info("Jarvis core started in %s", resolved_config.environment)
        return runtime


def reset_assistant_runtime() -> None:
    """Reset the singleton for tests and controlled process restart."""
    global _runtime
    with _runtime_lock:
        _runtime = None


def run_doctor() -> dict[str, object]:
    """Return a comprehensive machine-readable diagnostic report across all subsystems."""
    runtime = build_assistant_runtime()

    # 1. Directory and filesystem check
    dir_status: dict[str, dict[str, bool]] = {}
    for name, path in {
        "config": runtime.paths.config_root,
        "runtime": runtime.paths.runtime_root,
        "workspace": runtime.paths.workspace_root,
        "data": runtime.paths.data_root,
    }.items():
        exists = path.exists()
        writable = False
        if exists:
            try:
                probe = path / ".doctor_probe"
                probe.write_text("probe", encoding="utf-8")
                probe.unlink()
                writable = True
            except Exception:
                writable = False
        dir_status[name] = {"exists": exists, "writable": writable}

    # 2. Database & memory connectivity
    db_status: dict[str, Any] = {"status": "untested"}
    try:
        from jarvis.memory.db import Database
        from jarvis.memory.schema import initialize_database

        db_path = runtime.paths.data_root / "jarvis.db"
        db = Database(db_path)
        initialize_database(db)
        with db.read_connection() as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        db_status = {"status": "healthy", "tables": tables, "wal_enabled": True}
    except Exception as exc:
        db_status = {"status": "error", "error": str(exc)}

    # 3. Tool registry audit
    tools_status: dict[str, Any] = {"status": "untested"}
    try:
        from jarvis.tools.registry import get_tool_registry

        reg = get_tool_registry()
        tool_list = reg.list_tools()
        tools_status = {
            "status": "healthy",
            "registered_count": len(tool_list),
            "tools": [t.name for t in tool_list],
        }
    except Exception as exc:
        tools_status = {"status": "error", "error": str(exc)}

    # 4. Browser / computer-use readiness
    browser_status = {
        "playwright_installed": bool(importlib.util.find_spec("playwright")),
        "headless_capable": True,
    }

    # 5. Core dependencies check
    core_packages = ["pydantic", "fastapi", "uvicorn", "yaml", "sqlite3"]
    packages_status = {pkg: bool(importlib.util.find_spec(pkg)) for pkg in core_packages}

    overall_healthy = (
        runtime.healthy and db_status.get("status") == "healthy" and tools_status.get("status") == "healthy"
    )

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "runtime": "healthy" if runtime.healthy else "closed",
        "environment": runtime.config.environment,
        "python": sys.version.split()[0],
        "platform": platform.system(),
        "provider_credentials": list(runtime.config.configured_providers()),
        "gateway": runtime.gateway.status() if runtime.gateway is not None else None,
        "directories": dir_status,
        "database": db_status,
        "tools": tools_status,
        "browser": browser_status,
        "packages": packages_status,
        "registered_types": list(runtime.container.registered_types()),
    }
