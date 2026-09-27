"""Regression tests for browser authentication hardening."""

from __future__ import annotations

import pytest
from starlette.requests import Request
from starlette.responses import Response

from brjarvis.web.api.routes import auth


def make_request(host: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/login",
        "headers": [],
        "query_string": b"",
        "client": (host, 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.mark.unit
def test_session_can_be_revoked_immediately() -> None:
    token = auth.create_session()
    assert auth.verify_session(token)
    auth.revoke_session(token)
    assert not auth.verify_session(token)


@pytest.mark.unit
def test_cookie_secure_policy_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JARVIS_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("JARVIS_ENV", "production")
    assert auth._cookie_secure() is True

    monkeypatch.setenv("JARVIS_COOKIE_SECURE", "false")
    assert auth._cookie_secure() is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_login_sets_scoped_cookie_and_throttles_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "SERVER_API_KEY", "test-secret")
    auth._LOGIN_FAILURES.clear()
    request = make_request("198.51.100.10")

    for _ in range(auth._LOGIN_MAX_FAILURES):
        with pytest.raises(Exception) as error:
            await auth.login(auth.LoginRequest(api_key="wrong"), request, Response())
        assert getattr(error.value, "status_code", None) == 401

    with pytest.raises(Exception) as error:
        await auth.login(auth.LoginRequest(api_key="wrong"), request, Response())
    assert getattr(error.value, "status_code", None) == 429

    auth._LOGIN_FAILURES.clear()
    response = Response()
    await auth.login(auth.LoginRequest(api_key="test-secret"), request, response)
    cookie = response.headers["set-cookie"]
    assert "Path=/" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert not auth._LOGIN_FAILURES.get("198.51.100.10")
