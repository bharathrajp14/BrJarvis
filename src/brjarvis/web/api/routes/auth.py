# api/routes/auth.py — Canonical Authentication & WebSocket Ticket Exchange
"""
Provides secure session authentication and one-time short-lived ticket issuance for WebSocket handshakes.
Prevents passing long-lived credentials in URL query parameters.
Supports both versioned (/api/v1/auth/*) and root (/api/auth/*) paths.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
import time
from typing import Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ..state import SERVER_API_KEY

logger = logging.getLogger("JARVIS.API.Auth")

router = APIRouter(tags=["Authentication"])

# Ticket storage: ticket_id -> expiry_timestamp
_TICKET_STORE: Dict[str, float] = {}
_TICKET_TTL_SECONDS = 60.0

# Session token storage: session_token -> expiry_timestamp
_SESSION_STORE: Dict[str, float] = {}
_SESSION_TTL_SECONDS = 86400.0  # 24 hours

# Desktop-to-browser handoff storage: one-time token -> expiry timestamp.
_HANDOFF_STORE: Dict[str, float] = {}
_HANDOFF_TTL_SECONDS = 45.0


def _prune_expired() -> None:
    now = time.time()
    expired_tickets = [t for t, exp in _TICKET_STORE.items() if exp < now]
    for t in expired_tickets:
        _TICKET_STORE.pop(t, None)

    expired_sessions = [s for s, exp in _SESSION_STORE.items() if exp < now]
    for s in expired_sessions:
        _SESSION_STORE.pop(s, None)

    expired_handoffs = [h for h, exp in _HANDOFF_STORE.items() if exp < now]
    for h in expired_handoffs:
        _HANDOFF_STORE.pop(h, None)


def issue_ws_ticket() -> str:
    """Issue a secure, single-use, short-lived WebSocket connection ticket."""
    _prune_expired()
    ticket = secrets.token_urlsafe(32)
    _TICKET_STORE[ticket] = time.time() + _TICKET_TTL_SECONDS
    return ticket


def verify_and_consume_ws_ticket(ticket: str) -> bool:
    """Verify and immediately consume a single-use WebSocket connection ticket."""
    _prune_expired()
    if not ticket:
        return False
    expiry = _TICKET_STORE.pop(ticket, None)
    if expiry is None:
        return False
    return expiry >= time.time()


def create_session() -> str:
    """Create a persistent authenticated session."""
    _prune_expired()
    token = secrets.token_urlsafe(48)
    _SESSION_STORE[token] = time.time() + _SESSION_TTL_SECONDS
    return token


def verify_session(token: str) -> bool:
    """Check if a session token is valid."""
    _prune_expired()
    if not token:
        return False
    expiry = _SESSION_STORE.get(token)
    if expiry is None:
        return False
    return expiry >= time.time()


class LoginRequest(BaseModel):
    api_key: str = Field(..., description="Server API Key for authentication")


class LoginResponse(BaseModel):
    success: bool
    expires_in: int
    auth_required: bool = True


class AuthStatusResponse(BaseModel):
    auth_required: bool
    authenticated: bool
    server_time: float


class TicketResponse(BaseModel):
    ticket: str
    expires_in: int


class DesktopHandoffRequest(BaseModel):
    redirect: str = Field(default="/web/", description="Same-origin workspace redirect path")


class DesktopHandoffResponse(BaseModel):
    url: str
    expires_in: int


class DesktopHandoffRedeemRequest(BaseModel):
    handoff: str = Field(..., min_length=16, max_length=256)


def _extract_token(request: Request, authorization: Optional[str], x_api_key: Optional[str]) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:].strip()
    if x_api_key:
        return x_api_key.strip()
    session_cookie = request.cookies.get("jarvis_session")
    if session_cookie:
        return session_cookie.strip()
    return None


def _is_authorized(request: Request, authorization: Optional[str], x_api_key: Optional[str]) -> bool:
    if not SERVER_API_KEY:
        return False

    token = _extract_token(request, authorization, x_api_key)
    if not token:
        return False
    if hmac.compare_digest(token, SERVER_API_KEY):
        return True
    if verify_session(token):
        return True
    return False


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(
    request: Request, authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)
):
    """Inspect whether server authentication is active and if caller is authenticated."""
    auth_req = bool(SERVER_API_KEY)
    authenticated = _is_authorized(request, authorization, x_api_key)
    return AuthStatusResponse(
        auth_required=auth_req,
        authenticated=authenticated,
        server_time=time.time(),
    )


@router.post("/auth/login", response_model=LoginResponse)
async def login(login_req: LoginRequest, response: Response):
    """Authenticate with API key and establish a session."""
    if not SERVER_API_KEY or not hmac.compare_digest(login_req.api_key.strip(), SERVER_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")

    session_token = create_session()
    response.set_cookie(
        key="jarvis_session",
        value=session_token,
        max_age=int(_SESSION_TTL_SECONDS),
        httponly=True,
        samesite="strict",
        secure=os.environ.get("JARVIS_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"},
    )
    return LoginResponse(
        success=True,
        expires_in=int(_SESSION_TTL_SECONDS),
        auth_required=bool(SERVER_API_KEY),
    )


@router.post("/auth/desktop-handoff", response_model=DesktopHandoffResponse)
async def create_desktop_handoff(
    req: DesktopHandoffRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
):
    """Create a short-lived browser handoff without exposing the native API key."""
    if not _is_authorized(request, authorization, x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
    redirect = req.redirect.strip() or "/web/"
    if not redirect.startswith("/web") or "//" in redirect:
        raise HTTPException(status_code=400, detail="Workspace redirect must be same-origin under /web")
    _prune_expired()
    handoff = secrets.token_urlsafe(32)
    _HANDOFF_STORE[handoff] = time.time() + _HANDOFF_TTL_SECONDS
    separator = "&" if "?" in redirect else "?"
    return DesktopHandoffResponse(url=f"{redirect}{separator}handoff={handoff}", expires_in=int(_HANDOFF_TTL_SECONDS))


@router.post("/auth/desktop-handoff/redeem")
async def redeem_desktop_handoff(req: DesktopHandoffRedeemRequest, response: Response):
    """Consume a one-time desktop handoff and establish the normal browser session cookie."""
    _prune_expired()
    expiry = _HANDOFF_STORE.pop(req.handoff, None)
    if expiry is None or expiry < time.time():
        raise HTTPException(status_code=401, detail="Workspace handoff expired or already used")
    session_token = create_session()
    response.set_cookie(
        key="jarvis_session",
        value=session_token,
        max_age=int(_SESSION_TTL_SECONDS),
        httponly=True,
        samesite="strict",
        secure=os.environ.get("JARVIS_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"},
    )
    return {"success": True, "expires_in": int(_SESSION_TTL_SECONDS)}


@router.post("/auth/ws-ticket", response_model=TicketResponse)
async def request_ws_ticket(

    request: Request, authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)
):
    """Issue a short-lived one-time ticket for WebSocket connection."""
    if not _is_authorized(request, authorization, x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key or Session")

    ticket = issue_ws_ticket()
    return TicketResponse(ticket=ticket, expires_in=int(_TICKET_TTL_SECONDS))
