"""Web API route modules."""

from __future__ import annotations

from .chat import router as chat_router
from .control_plane import router as control_plane_router

__all__ = ["chat_router", "control_plane_router"]
