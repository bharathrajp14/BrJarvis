"""Non-Destructive Startup Smoke Invariant Suite for BR JARVIS MK40.2+."""

from __future__ import annotations

import os

import pytest

from scripts.smoke_startup import main as run_smoke_checks


@pytest.mark.smoke
def test_all_startup_smoke_invariants(monkeypatch):
    """Verify all 12 checks pass even when the optional gateway is enabled."""
    monkeypatch.setenv("JARVIS_AI_GATEWAY_ENABLED", "true")

    result = run_smoke_checks()

    assert result == 0
    assert os.environ["JARVIS_AI_GATEWAY_ENABLED"] == "true"
