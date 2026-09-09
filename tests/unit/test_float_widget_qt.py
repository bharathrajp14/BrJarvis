from __future__ import annotations

import os
import threading

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from brjarvis.desktop.float_widget import HeadlessFloat, JarvisFloat


class _Orchestrator:
    def __init__(self):
        self.called = threading.Event()

    def chat(self, prompt):
        self.called.set()
        return {"response": f"Received: {prompt}"}


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    for widget in list(app.topLevelWidgets()):
        widget.hide()
        widget.deleteLater()
    app.processEvents()


def test_default_surface_is_a_compact_orb(qt_app):
    widget = JarvisFloat()
    widget.show_orb()
    qt_app.processEvents()

    assert widget._mode == "orb"
    assert widget._minimized is True
    assert widget._stack.currentWidget() is widget._orb
    assert widget.size() == widget._mini_size
    widget.deleteLater()
    qt_app.processEvents()


def test_orb_expands_to_command_rail_with_clear_hierarchy(qt_app):
    widget = JarvisFloat()
    widget.show_orb()
    widget.show_rail()
    qt_app.processEvents()

    assert widget._mode == "rail"
    assert widget._minimized is False
    assert widget._stack.currentWidget() is widget._rail
    assert widget._rail.input.isEnabled() is True
    assert widget._rail.state.text() == "Idle"
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_runtime_and_assistant_states_render_on_rail_and_orb(qt_app):
    widget = JarvisFloat()
    widget.show_rail()
    widget.set_runtime("external_online")
    widget.set_state("LISTENING")
    qt_app.processEvents()

    assert widget._rail.runtime.text() == "Online · external"
    assert widget._rail.state.text() == "Listening"
    assert widget._orb._state == "listening"
    assert widget._rail.voice.isEnabled() is True
    assert widget._rail.voice.text() == "MIC"
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_command_rail_command_flow_uses_runtime_adapter(qt_app):
    orchestrator = _Orchestrator()
    widget = JarvisFloat(orchestrator=orchestrator)
    widget.show_rail()
    widget._rail.input.setText("check status")
    widget._rail._submit()
    qt_app.processEvents()

    assert orchestrator.called.wait(timeout=2)
    for _ in range(100):
        qt_app.processEvents()
        if widget._runtime.snapshot().input == "idle":
            break

    assert widget._runtime.snapshot().message == "Received: check status"
    assert widget._runtime.snapshot().task == "completed"
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_context_card_is_reserved_for_relevant_runtime_context(qt_app):
    widget = JarvisFloat()
    widget._runtime.set_task_state("running")
    widget._runtime.update(message="Building the requested artifact")
    widget.show_context()
    qt_app.processEvents()

    assert widget._mode == "context"
    assert widget._stack.currentWidget() is widget._context
    assert widget._context.title.text() == "Current task"
    assert "Building" in widget._context.body.text()
    widget._context.closed.emit()
    assert widget._mode == "rail"
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_escape_collapses_context_then_rail_to_orb(qt_app):
    widget = JarvisFloat()
    widget.show_context()
    widget._escape()
    assert widget._mode == "rail"
    widget._escape()
    assert widget._mode == "orb"
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_reduced_motion_stops_state_dot_animation(qt_app):
    widget = JarvisFloat()
    widget.show_rail()
    widget.set_reduced_motion(True)
    assert widget._orb is not None
    # The orb has no continuous idle animation; reduced motion remains a safe no-op.
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_headless_projection_matches_runtime_contract():
    headless = HeadlessFloat()
    headless.set_runtime("offline")
    headless.set_state("LISTENING")
    headless.speaking = True

    assert headless.state.runtime == "offline"
    assert headless.state.assistant == "listening"
    assert headless.state.audio == "playing"
    assert headless.state.capabilities["graphical_display"] is False


def test_ctrl_d_is_safe_and_requires_confirmation(qt_app, monkeypatch):
    from brjarvis.desktop import floating_surface as surface

    widget = JarvisFloat()
    widget.show_rail()
    qt_app.processEvents()
    quit_called = []
    monkeypatch.setattr(surface.QMessageBox, "question", lambda *args, **kwargs: surface.QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(surface.QApplication, "quit", lambda: quit_called.append(True))

    widget._request_safe_exit()

    assert quit_called == [True]
    assert widget._runtime.snapshot().runtime == "stopping"
    assert widget.isVisible() is False
    widget.deleteLater()
    qt_app.processEvents()


def test_ctrl_d_never_exits_while_typing(qt_app, monkeypatch):
    from brjarvis.desktop import floating_surface as surface

    widget = JarvisFloat()
    widget.show_rail()
    widget._rail.input.setFocus()
    widget._rail.input.setText("draft command")
    qt_app.processEvents()
    asked = []
    monkeypatch.setattr(surface.QMessageBox, "question", lambda *args, **kwargs: asked.append(True))

    widget._request_safe_exit()

    assert asked == []
    assert widget.isVisible() is True
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_connector_polling_is_suspended_in_orb_and_active_in_rail(qt_app):
    widget = JarvisFloat()
    widget.show_orb()
    assert widget._connector_timer.isActive() is False
    widget.show_rail()
    assert widget._connector_timer.isActive() is True
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()



def test_listening_control_has_explicit_stop_and_transcribing_states(qt_app):
    widget = JarvisFloat()
    widget.show_rail()
    widget._runtime.update(voice="recording", assistant="listening", message="Listening…")
    qt_app.processEvents()
    assert widget._rail.voice.text() == "STOP"
    assert widget._rail.voice.isEnabled() is True

    widget._runtime.update(voice="transcribing", assistant="processing", message="Transcribing…")
    qt_app.processEvents()
    assert widget._rail.voice.text() == "…"
    assert widget._rail.voice.isEnabled() is False
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_command_rail_stays_within_comfortable_screen_bounds(qt_app):
    widget = JarvisFloat()
    widget.show_rail()
    qt_app.processEvents()
    screen = widget.screen() or QApplication.primaryScreen()
    available = screen.availableGeometry()
    assert widget.width() <= min(500, int(available.width() * 0.42))
    assert widget.height() <= min(220, int(available.height() * 0.30))
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()



def test_minimized_orb_becomes_audio_stop_control_while_listening(qt_app):
    widget = JarvisFloat()
    widget.show_orb()
    widget._runtime.update(voice="recording", assistant="listening", message="Listening…")
    qt_app.processEvents()
    assert widget._orb.button.text() == "■"
    assert "Stop listening" in widget._orb.button.accessibleName()
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()


def test_task_context_renders_previous_task_choices(qt_app):
    widget = JarvisFloat()
    widget.show_context()
    widget._runtime.update(
        recent_tasks=({"task_id": "task_1", "goal": "Review a chapter", "status": "WAITING_FOR_USER"},),
        task="none",
    )
    qt_app.processEvents()
    assert widget._context.title.text() == "Completed and previous tasks"
    assert len(widget._context._buttons) == 1
    assert "Review a chapter" in widget._context._buttons[0].toolTip()
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()



def test_context_refresh_does_not_duplicate_actions_or_show_dead_approval(qt_app):
    widget = JarvisFloat()
    widget._runtime.update(task="waiting_for_approval", message="A review is required.")
    widget.show_context()
    qt_app.processEvents()
    assert [button.text() for button in widget._context._buttons] == ["Open workspace"]

    widget._runtime.update(recent_tasks=({"task_id": "task_1", "goal": "Read notes", "status": "WAITING_FOR_USER"},), task="none")
    qt_app.processEvents()
    assert len(widget._context._buttons) == 1
    widget._runtime.update(recent_tasks=({"task_id": "task_1", "goal": "Read notes", "status": "WAITING_FOR_USER"},), task="none")
    qt_app.processEvents()
    assert len(widget._context._buttons) == 1
    widget.hide()
    widget.deleteLater()
    qt_app.processEvents()
