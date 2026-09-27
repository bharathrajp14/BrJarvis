"""Integration test proving 'One store, every surface' and cross-surface memory recall.

Verifies:
1. CLI, Web API, Voice/Widget, and Career OS resolve the exact same canonical UnifiedMemory.
2. Facts written on one surface are immediately recalled across all other surfaces.
3. Post-session background summarization synthesizes turns into durable facts accessible everywhere.
4. User consent toggles (disable/enable) and privacy deletion/wipe are immediately respected across all surfaces.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jarvis.core.bootstrap import (
    AssistantRuntime,
    build_assistant_runtime,
    get_assistant_runtime,
    reset_assistant_runtime,
)
from jarvis.core.paths import PathLayout
from jarvis.memory.unified import UnifiedMemory


@pytest.fixture
def clean_runtime(tmp_path):
    """Fixture providing an isolated AssistantRuntime with dedicated test SQLite database."""
    reset_assistant_runtime()

    test_layout = PathLayout(
        project_root=tmp_path,
        config_root=tmp_path / "config",
        runtime_root=tmp_path / "runtime",
        workspace_root=tmp_path / "workspace",
        data_root=tmp_path / "data",
    )
    test_layout.ensure_directories()

    runtime = build_assistant_runtime(layout=test_layout, force_new=True)
    yield runtime

    # Teardown
    reset_assistant_runtime()


def test_cross_surface_memory_recall_flow(clean_runtime: AssistantRuntime) -> None:
    # ── Verify Shared Singleton Identity ──────────────────────────────────────
    runtime = get_assistant_runtime()
    assert runtime is clean_runtime
    assert isinstance(runtime.memory, UnifiedMemory)
    shared_memory = runtime.memory

    # ── Surface 1: Web API Surface ───────────────────────────────────────────
    # Initialize FastAPI TestClient against brjarvis web application
    from brjarvis.web.api.server import create_app
    from brjarvis.web.api.state import SERVER_API_KEY

    app = create_app()
    client = TestClient(app)
    auth_headers = {"X-API-Key": SERVER_API_KEY}

    # 1. User on Web UI saves an explicit preference
    save_resp = client.post(
        "/api/memory",
        headers=auth_headers,
        json={
            "name": "primary_editor",
            "type": "preference",
            "description": "User primary code editor",
            "content": "Neovim with Lua",
            "scope": "user",
        },
    )
    assert save_resp.status_code == 200

    # 2. Verify Web API lists the newly saved canonical fact
    list_resp = client.get("/api/memory", headers=auth_headers)
    assert list_resp.status_code == 200
    memories = list_resp.json().get("memories", [])
    matching = [m for m in memories if m["name"] == "primary_editor"]
    assert len(matching) == 1
    assert matching[0]["content"] == "Neovim with Lua"

    # ── Surface 2: CLI / Agent Runtime Surface ────────────────────────────────
    # A CLI command or autonomous agent loop turn accesses memory through runtime
    cli_memory = get_assistant_runtime().memory
    assert cli_memory is not None

    # CLI immediately retrieves the preference written by the Web surface
    assert cli_memory.get_preference("primary_editor") == "Neovim with Lua"

    # CLI injects memory context for a coding turn
    context_cli = cli_memory.recall("Which editor should I configure for Python development?")
    assert "Neovim with Lua" in context_cli

    # CLI records an active project initiative
    cli_memory.remember(
        key="active_initiative",
        value="Project Hyperion: Autonomous Flight Stack",
        category="project",
        source="cli_surface",
    )

    # ── Surface 3: Ambient Voice Assistant / Floating Widget Surface ──────────
    # Ambient voice daemon checks current active project
    voice_memory = get_assistant_runtime().memory
    assert voice_memory is not None

    voice_context = voice_memory.recall("What is my active project initiative?")
    assert "Project Hyperion" in voice_context

    # Voice assistant executes a multi-turn conversation session
    voice_session_id = "voice-session-hyperion-01"
    voice_memory.summarizer.record_turn(
        session_id=voice_session_id,
        role="user",
        content="Hello JARVIS. My name is Commander Shepherd. Keep in mind that oxygen reserves must stay above 40 percent.",
    )
    voice_memory.summarizer.record_turn(
        session_id=voice_session_id,
        role="assistant",
        content="Acknowledged Commander Shepherd. Oxygen reserves safety constraint logged.",
    )

    # Voice session closes; background session summarizer synthesizes durable facts
    summary = voice_memory.summarize_session(voice_session_id)
    assert summary is not None
    assert summary.turn_count == 2
    assert len(summary.durable_facts) >= 1

    # ── Surface 4: Career OS & Profile Cross-Recall ───────────────────────────
    # Career OS inspects the user profile
    profile = shared_memory.get_profile()
    # Confirm name extracted from voice conversation is now part of the global user profile!
    assert "Commander Shepherd" in profile.values() or any("Shepherd" in v for v in profile.values())
    assert profile.get("primary_editor") == "Neovim with Lua"

    # Query from any surface retrieves both explicit facts and synthesized facts
    global_query_context = shared_memory.recall("Who am I and what constraints apply?")
    assert "Shepherd" in global_query_context
    assert "oxygen" in global_query_context.lower() or "reserves" in global_query_context.lower()

    # ── Surface 5: Consent, Editability, and Privacy Controls ─────────────────
    # The user manages consent from settings
    all_facts = shared_memory.list_facts()
    assert len(all_facts) >= 3

    # Find the primary_editor fact
    editor_fact = next(f for f in all_facts if f["key"] == "primary_editor")
    fact_id = editor_fact["id"]

    # 1. Toggle off (disable) fact
    toggle_success = shared_memory.toggle_fact(fact_id, enabled=False)
    assert toggle_success is True

    # After disabling, verify recall on ANY surface excludes the disabled fact
    context_after_disable = shared_memory.recall("Which editor do I use?")
    assert "Neovim with Lua" not in context_after_disable

    # 2. Re-enable fact
    assert shared_memory.enable_fact(fact_id) is True
    context_after_enable = shared_memory.recall("Which editor do I use?")
    assert "Neovim with Lua" in context_after_enable

    # 3. Permanent deletion via Web API DELETE endpoint
    del_resp = client.delete("/api/memory/primary_editor", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify completely absent across all surfaces
    assert shared_memory.get_preference("primary_editor") == ""
    assert "Neovim with Lua" not in shared_memory.recall("Which editor do I use?")

    # 4. User exercises full privacy wipe (GDPR / zero-trace reset)
    purged_count = shared_memory.clear()
    assert purged_count > 0
    assert len(shared_memory.list_facts()) == 0
    assert shared_memory.recall("Who am I?") == ""
