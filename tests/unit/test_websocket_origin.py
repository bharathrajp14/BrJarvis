"""Unit tests for WebSocket origin policy."""

from __future__ import annotations

import pytest

from brjarvis.web.api.routes.websocket import websocket_origin_allowed


@pytest.mark.unit
def test_missing_origin_is_allowed_for_non_browser_clients():
    assert websocket_origin_allowed(None, "127.0.0.1:8000") is True
    assert websocket_origin_allowed("", "127.0.0.1:8000") is True


@pytest.mark.unit
def test_same_origin_matches_host_even_on_non_default_port():
    assert websocket_origin_allowed("http://127.0.0.1:8080", "127.0.0.1:8080") is True
    assert websocket_origin_allowed("https://preview.example.app", "preview.example.app") is True


@pytest.mark.unit
def test_configured_and_localhost_origins_are_allowed():
    assert websocket_origin_allowed("http://localhost:3000", "localhost:8000") is True
    assert websocket_origin_allowed(
        "https://approved.example",
        "127.0.0.1:8000",
        extra_origins={"https://approved.example"},
    ) is True


@pytest.mark.unit
def test_cross_origin_sockets_are_rejected():
    assert websocket_origin_allowed("https://evil.example", "127.0.0.1:8000") is False
    assert websocket_origin_allowed("http://127.0.0.1:9000", "127.0.0.1:8000") is False
