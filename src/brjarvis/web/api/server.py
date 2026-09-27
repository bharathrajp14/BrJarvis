# api/server.py — Modular Canonical FastAPI Application Factory for BR JARVIS
"""
Modular FastAPI Application Factory for BR JARVIS Autonomous Control Plane.
Mounts all route routers with authentication, CORS, security headers, rate limiting, and lifespan management.
"""

from __future__ import annotations

import asyncio
import hmac
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from brjarvis.agent.recovery_watchdog import get_recovery_watchdog
from brjarvis.agent.task_queue import get_queue
from brjarvis.career.api_routes import router as career_router
from brjarvis.core.bootstrap import build_assistant_runtime
from brjarvis.core.version import DESCRIPTION, VERSION
from brjarvis.events.bus import get_event_bus

from .routes.artifacts import router as artifacts_router
from .routes.auth import router as auth_router
from .routes.auth import verify_session
from .routes.automations import router as automations_router
from .routes.chat import router as chat_router
from .routes.connectors import router as connectors_router
from .routes.conversations import router as conversations_router
from .routes.devices import router as devices_router
from .routes.health import router as health_router
from .routes.memory import router as memory_router
from .routes.notifications import router as notifications_router
from .routes.projects import router as projects_router
from .routes.routines import router as routines_router
from .routes.search import router as search_router
from .routes.skills import router as skills_router
from .routes.tasks import router as tasks_router
from .routes.voice import router as voice_router
from .routes.websocket import router as ws_router
from .state import (
    ACTIVE_WEBSOCKETS,
    SERVER_API_KEY,
    WEB_DIR,
    get_orchestrator,
    get_ws_lock,
    require_server_api_key,
    set_orchestrator,
)

logger = logging.getLogger("JARVIS.API.Server")

_RICH_RE = re.compile(r"\[/?[a-z_]+\]", re.IGNORECASE)


def strip_rich(text: str) -> str:
    return _RICH_RE.sub("", text)


# ── Canonical WebSocket Logging Handler (Clean Logging without sys.stdout hacks) ─


class WSLogHandler(logging.Handler):
    """Standard logging handler that broadcasts formatted logs to active WebSockets."""

    def __init__(self):
        super().__init__()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._active: bool = False

    def activate(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._active = True

    def deactivate(self) -> None:
        self._active = False
        self._loop = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self._active or not self._loop or not self._loop.is_running():
            return
        try:
            msg = self.format(record)
            clean_msg = strip_rich(msg).strip()
            # Redact secrets from broadcasted logs
            clean_msg = re.sub(r"AIzaSy[A-Za-z0-9_\-]{33}", "[REDACTED_API_KEY]", clean_msg)
            clean_msg = re.sub(r"sk-[A-Za-z0-9_\-]{20,}", "[REDACTED_API_KEY]", clean_msg)
            if clean_msg:
                asyncio.run_coroutine_threadsafe(broadcast_log(clean_msg), self._loop)
        except Exception:
            pass


ws_log_handler = WSLogHandler()
ws_log_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
logging.getLogger("JARVIS").addHandler(ws_log_handler)


async def _send_ws_log(ws: WebSocket, line: str):
    try:
        from starlette.websockets import WebSocketState

        if ws.client_state == WebSocketState.CONNECTED:
            await asyncio.wait_for(
                ws.send_json(
                    {"event_id": str(uuid.uuid4()), "type": "log", "payload": {"message": line}, "message": line}
                ),
                timeout=0.5,
            )
    except Exception:
        async with get_ws_lock():
            ACTIVE_WEBSOCKETS.discard(ws)


async def broadcast_log(line: str):
    """Broadcast a log line with bounded, awaited fan-out."""
    async with get_ws_lock():
        targets = list(ACTIVE_WEBSOCKETS)
    if not targets:
        return
    await asyncio.gather(
        *(asyncio.wait_for(_send_ws_log(ws, line), timeout=0.5) for ws in targets),
        return_exceptions=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler — builds runtime, recovers tasks, and activates logging."""
    logger.info("⚙ Starting BR JARVIS Core Server v%s...", VERSION)

    runtime = await asyncio.to_thread(build_assistant_runtime)
    set_orchestrator(runtime.orchestrator)
    task_queue = get_queue()

    # Run Crash Recovery Watchdog
    try:
        get_recovery_watchdog().inspect_and_recover()
    except Exception as exc:
        logger.warning("Recovery watchdog non-fatal note: %s", exc)

    ws_log_handler.activate(asyncio.get_running_loop())
    logger.info("✓ BR JARVIS Core Server Ready.")
    try:
        yield
    finally:
        ws_log_handler.deactivate()
        try:
            await asyncio.to_thread(task_queue.stop, 5.0)
        except Exception as exc:
            logger.warning("Task queue shutdown note: %s", exc)
        try:
            get_event_bus().store.close(timeout=2.0)
        except Exception as exc:
            logger.warning("Event store shutdown note: %s", exc)
        orch = get_orchestrator()
        if orch:
            try:
                orch.shutdown()
            except Exception as exc:
                logger.warning("Orchestrator shutdown note: %s", exc)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security headers for browser protection."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content-Security-Policy allows local scripts, fonts, and inline UI styling safely
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' ws: wss: http: https:; "
            "frame-ancestors 'none';"
        )
        return response


def create_app() -> FastAPI:
    """Create and configure the production FastAPI application."""
    require_server_api_key()
    app = FastAPI(
        title="BR JARVIS Autonomous Operating Platform", version=VERSION, description=DESCRIPTION, lifespan=lifespan
    )

    # Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS configuration
    cors_origins = os.environ.get("JARVIS_CORS_ORIGINS", "").strip()
    allowed_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if cors_origins:
        allowed_origins.extend([o.strip() for o in cors_origins.split(",") if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Key / Session Authentication Middleware
    @app.middleware("http")
    async def verify_api_key(request: Request, call_next):
        if SERVER_API_KEY:
            path = request.url.path
            exempt_prefixes = (
                "/health",
                "/api/health",
                "/api/v1/health",
                "/ready",
                "/api/ready",
                "/api/v1/ready",
                "/diagnostics",
                "/api/diagnostics",
                "/api/v1/diagnostics",
                "/metrics",
                "/api/metrics",
                "/api/v1/metrics",
                "/api/auth",
                "/api/v1/auth",
                "/static",
                "/web",
                "/galaxy",
                "/3d",
            )
            exempt_exact = (
                "/",
                "/index.html",
                "/galaxy.html",
                "/manifest.json",
                "/sw.js",
                "/style.css",
                "/app.js",
                "/graph-data.js",
                "/favicon.ico",
            )

            is_exempt = path.startswith(exempt_prefixes) or path in exempt_exact
            if not is_exempt and path.startswith(("/api", "/v1")):
                auth_header = request.headers.get("Authorization")
                api_key_header = request.headers.get("X-API-Key")
                session_cookie = request.cookies.get("jarvis_session")

                token = None
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:].strip()
                elif api_key_header:
                    token = api_key_header.strip()
                elif session_cookie:
                    token = session_cookie.strip()

                is_valid = False
                if token:
                    if len(token) == len(SERVER_API_KEY) and hmac.compare_digest(token, SERVER_API_KEY):
                        is_valid = True
                    elif verify_session(token):
                        is_valid = True

                if not is_valid:
                    req_id = str(uuid.uuid4())
                    return JSONResponse(
                        status_code=401,
                        content={
                            "success": False,
                            "request_id": req_id,
                            "error": {
                                "code": "UNAUTHORIZED",
                                "message": "Authentication required: Valid API Key or Session needed.",
                            },
                        },
                    )
        return await call_next(request)

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred while processing the request.",
                },
            },
        )

    # 404 Exception Handler with Glassmorphic Web Fallback
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            accept = request.headers.get("accept", "")
            if "text/html" in accept and not request.url.path.startswith(("/api", "/v1", "/ws")):
                index_file = WEB_DIR / "index.html"
                if index_file.exists() and request.url.path not in ("/404", "/404.html"):
                    return FileResponse(index_file)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": "NOT_FOUND", "message": exc.detail}},
        )

    # Mount Route Routers
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router)
    app.include_router(tasks_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(artifacts_router, prefix="/api")
    app.include_router(search_router)
    app.include_router(notifications_router, prefix="/api")
    app.include_router(automations_router)
    app.include_router(devices_router)
    app.include_router(routines_router)
    app.include_router(skills_router)
    app.include_router(connectors_router, prefix="/api")
    app.include_router(memory_router, prefix="/api")
    app.include_router(chat_router)
    app.include_router(voice_router)
    app.include_router(ws_router)
    app.include_router(career_router, prefix="/api")

    # Versioned mounts are explicit for routers whose decorators are canonical
    # relative paths. Legacy routers retain their own tested `/api/v1` aliases
    # and are not mounted again, preventing `/api/v1/api/...` drift.
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(artifacts_router, prefix="/api/v1")
    app.include_router(connectors_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")
    app.include_router(career_router, prefix="/api/v1")

    # Mount Static Files & Web Client
    # Critical: HTML/JS/CSS served with no-cache so the Service Worker and browser
    # cannot serve stale files after an upgrade.
    _NO_CACHE_HEADERS = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    def _use_rebuilt_ui() -> bool:
        configured = os.environ.get("JARVIS_REBUILT_UI_DEFAULT", "true").strip().lower()
        return configured not in {"0", "false", "no", "off"} and (WEB_DIR / "dist" / "index.html").exists()

    @app.get("/")
    @app.get("/index.html")
    @app.get("/web")
    @app.get("/web/")
    @app.get("/web/index.html")
    async def get_index():
        index_file = WEB_DIR / "dist" / "index.html" if _use_rebuilt_ui() else WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file, headers=_NO_CACHE_HEADERS)
        return HTMLResponse("<h1>BR JARVIS Dashboard</h1><p>Web client loaded</p>")

    @app.get("/web/legacy", include_in_schema=False)
    async def get_legacy_web():
        index_file = WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file, headers=_NO_CACHE_HEADERS)
        raise HTTPException(status_code=404, detail="legacy UI not found")

    @app.get("/web/sw.js")
    async def get_sw():
        sw_file = WEB_DIR / "sw.js"
        if sw_file.exists():
            return FileResponse(
                sw_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        raise HTTPException(status_code=404, detail="sw.js not found")

    @app.get("/web/app.js")
    async def get_app_js():
        app_js_file = WEB_DIR / "app.js"
        if app_js_file.exists():
            return FileResponse(app_js_file, headers=_NO_CACHE_HEADERS)
        raise HTTPException(status_code=404, detail="app.js not found")

    @app.get("/galaxy")
    @app.get("/galaxy.html")
    @app.get("/3d")
    async def get_galaxy():
        galaxy_file = WEB_DIR / "galaxy.html"
        if galaxy_file.exists():
            return FileResponse(galaxy_file, headers=_NO_CACHE_HEADERS)
        return HTMLResponse("<h1>3D Knowledge Galaxy</h1>")

    @app.get("/web/rebuild", include_in_schema=False)
    @app.get("/web/control-plane", include_in_schema=False)
    async def get_rebuilt_web():
        rebuilt_index = WEB_DIR / "dist" / "index.html"
        if rebuilt_index.exists():
            return FileResponse(rebuilt_index, headers=_NO_CACHE_HEADERS)
        raise HTTPException(status_code=404, detail="rebuilt UI not built")

    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

    @app.get("/{file_name:path}")
    async def serve_root_static_or_fallback(file_name: str, request: Request):
        if file_name.startswith(("api/", "v1/", "ws", "health")):
            raise HTTPException(status_code=404, detail=f"API endpoint '/{file_name}' not found.")
        web_root = WEB_DIR.resolve()
        target_file = (web_root / file_name).resolve()
        try:
            target_file.relative_to(web_root)
        except ValueError:
            raise HTTPException(status_code=404, detail="Requested static file was not found.")
        if target_file.exists() and target_file.is_file():
            extra = _NO_CACHE_HEADERS if target_file.suffix in (".html", ".js", ".css") else {}
            return FileResponse(target_file, headers=extra)
        accept = request.headers.get("accept", "")
        if "text/html" in accept or not Path(file_name).suffix:
            configured = os.environ.get("JARVIS_REBUILT_UI_DEFAULT", "true").strip().lower()
            index_file = WEB_DIR / "dist" / "index.html" if configured not in {"0", "false", "no", "off"} and (WEB_DIR / "dist" / "index.html").exists() else WEB_DIR / "index.html"
            if index_file.exists():
                return FileResponse(index_file, headers=_NO_CACHE_HEADERS)
        raise HTTPException(status_code=404, detail=f"Requested URL '/{file_name}' not found.")

    return app
