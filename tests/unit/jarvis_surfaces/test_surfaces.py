from __future__ import annotations

from fastapi.testclient import TestClient

from jarvis.surfaces import create_app, refine_voice_transcript


def test_web_surface_endpoints() -> None:
    app = create_app()
    client = TestClient(app)

    # 1. Healthz
    h_res = client.get("/healthz")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "ok"

    # 2. Control plane summary (PERF-001)
    s_res = client.get("/api/v1/control-plane/summary")
    assert s_res.status_code == 200
    data = s_res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "platform" in data
    assert "tools" in data
    assert "tasks" in data


def test_voice_prompt_refiner() -> None:
    raw = "Hey Jarvis, um could you please tell me the time?"
    refined = refine_voice_transcript(raw)
    assert "Hey Jarvis" not in refined.cleaned_prompt
    assert "um" not in refined.cleaned_prompt
    assert "could you please" not in refined.cleaned_prompt
    assert "tell me the time" in refined.cleaned_prompt
    assert refined.is_empty is False

    empty_res = refine_voice_transcript("   ")
    assert empty_res.is_empty is True
