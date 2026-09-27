"""FastAPI control plane server factory."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from jarvis.core.bootstrap import build_assistant_runtime, get_assistant_runtime
from jarvis.core.version import VERSION

from .routes import chat_router, control_plane_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup initialization and reverse-order shutdown."""
    runtime = build_assistant_runtime()
    yield
    await runtime.shutdown()


def create_app() -> FastAPI:
    """Construct and configure the production FastAPI application."""
    app = FastAPI(
        title="JARVIS Control Plane",
        version=VERSION,
        description="Local-first autonomous AI operating platform",
        lifespan=lifespan,
    )

    # Tighten CORS policy (SEC-005)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Health, readiness, diagnostic, and telemetry endpoints (Section 15)
    @app.get("/health", tags=["health"])
    @app.get("/healthz", tags=["health"])
    def health() -> dict[str, Any]:
        return {"status": "ok", "version": VERSION, "timestamp": time.time()}

    @app.get("/ready", tags=["health"])
    @app.get("/readyz", tags=["health"])
    def ready() -> dict[str, Any]:
        try:
            runtime = get_assistant_runtime()
            return {"status": "ready", "runtime": "healthy" if runtime else "uninitialized"}
        except Exception as exc:
            return {"status": "not_ready", "error": str(exc)}

    @app.get("/diagnostics", tags=["diagnostics"])
    def diagnostics() -> dict[str, Any]:
        from jarvis.core.bootstrap import run_doctor

        return run_doctor()

    @app.get("/metrics", tags=["telemetry"])
    def metrics() -> dict[str, Any]:
        try:
            import psutil

            proc = psutil.Process()
            mem = proc.memory_info()
            return {
                "status": "online",
                "cpu_percent": psutil.cpu_percent(interval=None),
                "process_memory_mb": round(mem.rss / (1024 * 1024), 2),
                "total_system_memory_percent": psutil.virtual_memory().percent,
                "timestamp": time.time(),
            }
        except Exception:
            return {"status": "online", "timestamp": time.time()}

    # Mount API routers
    app.include_router(control_plane_router)
    app.include_router(chat_router)

    # Mount static assets if built
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "frontend" / "dist",
        Path(__file__).resolve().parent.parent.parent / "brjarvis" / "web" / "static" / "dist",
    ]
    for static_dir in candidates:
        if static_dir.exists() and (static_dir / "index.html").exists():
            app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
            break

    return app
