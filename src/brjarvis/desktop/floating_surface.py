"""Native Orb + Command Rail floating surface for BR JARVIS."""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Mapping, Optional

from brjarvis.desktop.floating_runtime import FloatingRuntimeAdapter, FloatingWidgetState

try:
    from brjarvis.ui import setup_qt_paths

    setup_qt_paths()
except Exception:
    pass

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal, Slot
    from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QFrame,
        QGraphicsDropShadowEffect,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMenu,
        QMessageBox,
        QPushButton,
        QProgressBar,
        QStackedLayout,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )

    HAS_QT = True
except ImportError:
    HAS_QT = False


if HAS_QT:

    class FloatingTheme:
        BG = "#0b1019"
        BG_RAISED = "#111a27"
        BG_CARD = "#151f2d"
        BORDER = "#26364a"
        TEXT = "#f2f6fb"
        MUTED = "#91a3ba"
        FAINT = "#5b6c81"
        CYAN = "#55d8f5"
        GREEN = "#62d9a3"
        AMBER = "#f0b45d"
        RED = "#f07882"

        @classmethod
        def state_color(cls, state: str) -> str:
            return {
                "idle": cls.CYAN,
                "listening": cls.CYAN,
                "processing": cls.AMBER,
                "speaking": cls.GREEN,
                "executing": "#b89aff",
                "waiting": cls.AMBER,
                "error": cls.RED,
            }.get(str(state).lower(), cls.FAINT)

        @classmethod
        def panel_style(cls) -> str:
            return f"""
                QFrame#rail, QFrame#context {{
                    background:rgba(11,16,25,232);
                    border:1px solid {cls.BORDER};
                    border-radius:16px;
                }}
                QLabel {{ color:{cls.TEXT}; }}
                QLabel#eyebrow {{ color:{cls.FAINT}; font-size:9px; font-weight:700; letter-spacing:1px; }}
                QLabel#runtime {{ color:{cls.MUTED}; font-size:11px; }}
                QLabel#state {{ color:{cls.CYAN}; font-size:12px; font-weight:700; letter-spacing:1px; }}
                QLabel#activity {{ color:{cls.TEXT}; font-size:13px; }}
                QLabel#helper {{ color:{cls.MUTED}; font-size:10px; }}
                QLineEdit {{
                    background:{cls.BG_RAISED}; color:{cls.TEXT}; border:1px solid {cls.BORDER};
                    border-radius:10px; padding:10px 12px; font-size:13px;
                }}
                QLineEdit:focus {{ border:1px solid {cls.CYAN}; }}
                QLineEdit:disabled {{ color:{cls.FAINT}; }}
                QPushButton#primary {{
                    background:{cls.CYAN}; color:#071018; border:0; border-radius:9px;
                    padding:8px 12px; font-size:11px; font-weight:700;
                }}
                QPushButton#primary:hover {{ background:#7be5fb; }}
                QPushButton#primary:disabled {{ background:#304454; color:{cls.FAINT}; }}
                QPushButton#secondary {{
                    background:{cls.BG_RAISED}; color:{cls.MUTED}; border:1px solid {cls.BORDER};
                    border-radius:8px; padding:7px 9px; font-size:10px;
                }}
                QPushButton#secondary:hover {{ color:{cls.TEXT}; border:1px solid #3f5873; }}
                QPushButton#danger {{
                    background:#24181e; color:{cls.RED}; border:1px solid #51303a;
                    border-radius:8px; padding:7px 9px; font-size:10px;
                }}
                QPushButton#orb {{
                    background:{cls.BG}; color:{cls.TEXT}; border:1px solid {cls.BORDER};
                    border-radius:34px; font-size:20px; font-weight:700;
                }}
                QPushButton#orb:hover {{ border:2px solid {cls.CYAN}; }}
                QPushButton#orb:focus {{ border:2px solid {cls.CYAN}; }}
                QProgressBar {{ background:{cls.BG_RAISED}; border:0; border-radius:2px; }}
                QProgressBar::chunk {{ background:{cls.CYAN}; border-radius:2px; }}
            """


    class StateDot(QWidget):
        def __init__(self, parent: Optional[QWidget] = None) -> None:
            super().__init__(parent)
            self.setFixedSize(12, 12)
            self._state = "idle"
            self._reduced = False
            self._phase = 0
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(100)

        def set_state(self, state: str) -> None:
            self._state = str(state or "idle").lower()
            self.update()

        def set_reduced_motion(self, reduced: bool) -> None:
            self._reduced = bool(reduced)
            if reduced:
                self._timer.stop()
            elif not self._timer.isActive():
                self._timer.start(100)
            self.update()

        def _tick(self) -> None:
            self._phase = (self._phase + 1) % 10
            self.update()

        def paintEvent(self, _event) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            color = QColor(FloatingTheme.state_color(self._state))
            if not self._reduced and self._state in {"listening", "processing", "speaking", "executing"}:
                glow = QColor(color)
                glow.setAlpha(35 + (self._phase % 5) * 8)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(glow)
                painter.drawEllipse(0, 0, 12, 12)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(3, 3, 6, 6)
            painter.end()


    class OrbSurface(QFrame):
        activated = Signal()
        stop_requested = Signal()

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            super().__init__(parent)
            self.setObjectName("orb")
            self.setFixedSize(74, 74)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(2)
            self.button = QPushButton("J")
            self.button.setObjectName("orb")
            self.button.setAccessibleName("Expand BR JARVIS command dock")
            self.button.clicked.connect(self._clicked)
            layout.addWidget(self.button)
            self._state = "idle"

        def _clicked(self) -> None:
            if self._state in {"listening", "processing"}:
                self.stop_requested.emit()
            else:
                self.activated.emit()

        def set_state(self, state: str) -> None:
            self._state = str(state or "idle").lower()
            color = FloatingTheme.state_color(self._state)
            listening = self._state == "listening"
            self.button.setText("■" if listening else "J")
            self.button.setAccessibleName("Stop listening" if listening else "Expand BR JARVIS command dock")
            self.button.setToolTip("Stop listening" if listening else "Open BR JARVIS")
            self.button.setStyleSheet(f"QPushButton#orb {{ background:rgba(11,16,25,220); color:{color}; border:2px solid {color}; border-radius:34px; font-size:20px; font-weight:700; }} QPushButton#orb:hover {{ border:2px solid {FloatingTheme.TEXT}; }}")


    class ContextCard(QFrame):
        closed = Signal()
        action_requested = Signal(str)

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            super().__init__(parent)
            self.setObjectName("context")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 16, 18, 16)
            layout.setSpacing(10)
            head = QHBoxLayout()
            self.title = QLabel("Context")
            self.title.setStyleSheet(f"color:{FloatingTheme.TEXT};font-size:14px;font-weight:700;")
            head.addWidget(self.title)
            head.addStretch()
            close = QPushButton("×")
            close.setObjectName("secondary")
            close.setAccessibleName("Close context card")
            close.setFixedWidth(28)
            close.clicked.connect(self.closed)
            head.addWidget(close)
            layout.addLayout(head)
            self.body = QLabel("")
            self.body.setWordWrap(True)
            self.body.setObjectName("activity")
            layout.addWidget(self.body)
            self.progress = QProgressBar()
            self.progress.setTextVisible(False)
            self.progress.setFixedHeight(5)
            self.progress.hide()
            layout.addWidget(self.progress)
            self.actions = QHBoxLayout()
            layout.addLayout(self.actions)
            self._buttons: list[QPushButton] = []

        def _clear_actions(self) -> None:
            while self.actions.count():
                item = self.actions.takeAt(0)
                child = item.widget()
                if child is not None:
                    child.deleteLater()
            self._buttons = []

        def show_task_history(self, tasks: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]]) -> None:
            self.title.setText("Completed and previous tasks")
            summaries = []
            for task in list(tasks)[:4]:
                goal = str(task.get("goal", "Untitled task")).strip()
                answer = str(task.get("answer", "")).strip()
                if answer:
                    summaries.append(f"{goal[:30]}: {answer[:72]}")
            summary_text = "\n".join(summaries)
            self.body.setText(("Recent answers:\n" + summary_text + "\n\n" if summary_text else "") + "Select a task to load its original request. Review it before sending.")
            self.progress.hide()
            self._clear_actions()
            for task in list(tasks)[:6]:
                task_id = str(task.get("task_id", ""))
                goal = str(task.get("goal", "Untitled task")).strip()
                status = str(task.get("status", "")).replace("_", " ").title()
                label = f"{goal[:42]} · {status}" if status else goal[:54]
                button = QPushButton(label)
                button.setObjectName("secondary")
                button.setToolTip(goal)
                button.clicked.connect(lambda _checked=False, value=task_id: self.action_requested.emit(f"continue_task:{value}"))
                self.actions.addWidget(button)
                self._buttons.append(button)
            self.actions.addStretch()

        def show_content(self, kind: str, title: str, body: str, *, progress: Optional[int] = None, actions: tuple[str, ...] = ()) -> None:
            self.title.setText(title)
            self.body.setText(body)
            self.progress.setVisible(progress is not None)
            if progress is not None:
                self.progress.setValue(max(0, min(100, int(progress))))
            self._clear_actions()
            for action in actions:
                button = QPushButton(action)
                button.setObjectName("primary" if action in {"Retry", "Approve", "Open workspace"} else "secondary")
                button.clicked.connect(lambda _checked=False, value=action.lower().replace(" ", "_"): self.action_requested.emit(value))
                self.actions.addWidget(button)
                self._buttons.append(button)
            self.actions.addStretch()


    class CommandRail(QFrame):
        command_submitted = Signal(str)
        voice_requested = Signal()
        speaker_requested = Signal()
        context_requested = Signal()
        workspace_requested = Signal()
        minimize_requested = Signal()
        hide_requested = Signal()

        def __init__(self, parent: Optional[QWidget] = None) -> None:
            super().__init__(parent)
            self.setObjectName("rail")
            self.setMinimumSize(320, 200)
            self.setMaximumSize(560, 250)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 16, 18, 15)
            layout.setSpacing(9)

            header = QHBoxLayout()
            self.dot = StateDot(self)
            header.addWidget(self.dot)
            identity = QVBoxLayout()
            identity.setSpacing(1)
            name = QLabel("BR JARVIS")
            name.setStyleSheet(f"color:{FloatingTheme.TEXT};font-size:13px;font-weight:700;letter-spacing:1px;")
            identity.addWidget(name)
            self.state = QLabel("Ready")
            self.state.setObjectName("state")
            identity.addWidget(self.state)
            header.addLayout(identity)
            header.addStretch()
            self.runtime = QLabel("Runtime status unknown")
            self.runtime.setObjectName("runtime")
            header.addWidget(self.runtime)
            self.minimize = QPushButton("−")
            self.minimize.setObjectName("secondary")
            self.minimize.setAccessibleName("Minimize to BR JARVIS orb")
            self.minimize.setFixedWidth(28)
            self.minimize.clicked.connect(self.minimize_requested)
            header.addWidget(self.minimize)
            self.hide_button = QPushButton("×")
            self.hide_button.setObjectName("danger")
            self.hide_button.setAccessibleName("Hide BR JARVIS command dock")
            self.hide_button.setFixedWidth(28)
            self.hide_button.clicked.connect(self.hide_requested)
            header.addWidget(self.hide_button)
            layout.addLayout(header)

            self.activity = QLabel("Ready for a command")
            self.activity.setObjectName("activity")
            layout.addWidget(self.activity)

            entry = QHBoxLayout()
            entry.setSpacing(7)
            self.input = QLineEdit()
            self.input.setPlaceholderText("Ask JARVIS…")
            self.input.setAccessibleName("Ask BR JARVIS")
            self.input.returnPressed.connect(self._submit)
            entry.addWidget(self.input, 1)
            self.voice = QPushButton("MIC")
            self._voice_available = True
            self.voice.setObjectName("secondary")
            self.voice.setAccessibleName("Capture voice-to-text")
            self.voice.clicked.connect(self.voice_requested)
            self.voice.setFixedWidth(54)
            entry.addWidget(self.voice)
            self.speaker = QPushButton("SPEAK")
            self.speaker.setObjectName("secondary")
            self.speaker.setAccessibleName("Speak the latest short response")
            self.speaker.setToolTip("Speak the latest response")
            self.speaker.clicked.connect(self.speaker_requested)
            self.speaker.setFixedWidth(66)
            entry.addWidget(self.speaker)
            send = QPushButton("→")
            send.setObjectName("primary")
            send.setAccessibleName("Send command")
            send.setFixedWidth(38)
            send.clicked.connect(self._submit)
            entry.addWidget(send)
            layout.addLayout(entry)

            footer = QHBoxLayout()
            footer.setSpacing(7)
            self.task = QPushButton("Task")
            self.task.setObjectName("secondary")
            self.task.setAccessibleName("Show current task context")
            self.task.clicked.connect(self.context_requested)
            footer.addWidget(self.task)
            self.workspace = QPushButton("Open workspace")
            self.workspace.setObjectName("secondary")
            self.workspace.clicked.connect(self.workspace_requested)
            footer.addWidget(self.workspace)
            helper = QLabel("Alt+Space · Esc")
            helper.setObjectName("helper")
            footer.addStretch()
            footer.addWidget(helper)
            layout.addLayout(footer)

        def _submit(self) -> None:
            text = self.input.text().strip()
            if text:
                self.input.clear()
                self.command_submitted.emit(text)

        def set_state(self, state: str) -> None:
            normalized = str(state or "idle").lower()
            self.dot.set_state(normalized)
            self.state.setText({"processing": "Processing", "waiting": "Needs approval", "error": "Needs attention"}.get(normalized, normalized.capitalize()))
            self.state.setStyleSheet(f"color:{FloatingTheme.state_color(normalized)};font-size:11px;font-weight:700;letter-spacing:1px;")

        def set_runtime(self, text: str) -> None:
            self.runtime.setText(text)

        def set_activity(self, text: str) -> None:
            self.activity.setText(text)

        def set_input_enabled(self, enabled: bool) -> None:
            self.input.setEnabled(enabled)
            self.voice.setEnabled(enabled and self.voice.text() != "N/A")
            self.speaker.setEnabled(bool(enabled))
            self.input.setPlaceholderText("Ask JARVIS…" if enabled else "Processing…")

        def set_transcript(self, transcript: str) -> None:
            if transcript and self.input.text() != transcript:
                self.input.setText(transcript)
                self.input.setCursorPosition(len(transcript))

        def set_speaker_state(self, state: str) -> None:
            speaking = str(state).lower() in {"synthesizing", "speaking"}
            self.speaker.setText("STOP" if speaking else "SPEAK")
            self.speaker.setAccessibleName("Stop speaker" if speaking else "Speak the latest short response")
            self.speaker.setToolTip("Stop speaking" if speaking else "Speak the latest response")

        def set_voice_enabled(self, enabled: bool) -> None:
            self._voice_available = bool(enabled)
            self.set_voice_state("ready", enabled)

        def set_voice_state(self, state: str, enabled: Optional[bool] = None) -> None:
            available = self._voice_available if enabled is None else bool(enabled)
            normalized = str(state or "ready").lower()
            if not available:
                self.voice.setEnabled(False)
                self.voice.setText("N/A")
                self.voice.setToolTip("No microphone or speech-to-text provider is available")
                return
            if normalized == "recording":
                self.voice.setEnabled(True)
                self.voice.setText("STOP")
                self.voice.setToolTip("Stop listening")
            elif normalized in {"transcribing", "refining"}:
                self.voice.setEnabled(False)
                self.voice.setText("REFINE" if normalized == "refining" else "…")
                self.voice.setToolTip("Refining your voice command" if normalized == "refining" else "Transcribing your voice")
            else:
                self.voice.setEnabled(True)
                self.voice.setText("MIC")
                self.voice.setToolTip("Listen for one command, then stop automatically")


    class JarvisFloat(QWidget):
        """First-principles Orb + Command Rail + Context Card controller."""

        runtime_state_signal = Signal(object)

        def __init__(self, orchestrator: Any = None, voice_trigger: Any = None) -> None:
            super().__init__()
            self._orchestrator = orchestrator
            self._voice_trigger = voice_trigger
            self._mode = "orb"
            self._drag_pos: Optional[QPoint] = None
            self._minimized = True
            self._reduced_motion = False
            self._normal_size = QSize(500, 220)
            self._mini_size = QSize(74, 74)
            self._setup_window()
            self._runtime = FloatingRuntimeAdapter(orchestrator=orchestrator, voice_trigger=voice_trigger)
            self._connector_timer = QTimer(self)
            self._connector_timer.setInterval(30000)
            self._connector_timer.timeout.connect(self._runtime.refresh_connectors)
            self.runtime_state_signal.connect(self._render_runtime_state)
            self._setup_surfaces()
            self._setup_tray()
            self._setup_shortcuts()
            self._runtime_unsubscribe = self._runtime.subscribe(self._on_runtime_state)

        def _setup_window(self) -> None:
            self.setWindowTitle("BR JARVIS")
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 120))
            self.setGraphicsEffect(shadow)
            self.setStyleSheet(FloatingTheme.panel_style())

        def _setup_surfaces(self) -> None:
            self._stack = QStackedLayout()
            self.setLayout(self._stack)
            self._orb = OrbSurface(self)
            self._rail = CommandRail(self)
            self._context = ContextCard(self)
            self._stack.addWidget(self._orb)
            self._stack.addWidget(self._rail)
            self._stack.addWidget(self._context)
            self._orb.activated.connect(self.show_rail)
            self._orb.stop_requested.connect(self._stop_voice)
            self._rail.command_submitted.connect(self._runtime_submit)
            self._rail.voice_requested.connect(self._runtime_voice)
            self._rail.speaker_requested.connect(self._runtime_speaker)
            self._rail.context_requested.connect(self.show_context)
            self._rail.workspace_requested.connect(self._open_workspace)
            self._rail.minimize_requested.connect(self.show_orb)
            self._rail.hide_requested.connect(self.hide)
            self._context.closed.connect(self.show_rail)
            self._context.action_requested.connect(self._context_action)
            self.show_orb()

        def _setup_tray(self) -> None:
            self._tray = QSystemTrayIcon(self)
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(FloatingTheme.CYAN))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(4, 4, 24, 24)
            painter.setPen(QPen(QColor(FloatingTheme.BG), 2))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "J")
            painter.end()
            self._tray.setIcon(QIcon(pixmap))
            self._tray.setToolTip("BR JARVIS")
            self._tray.activated.connect(lambda reason: self.show_rail() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
            menu = QMenu(self)
            menu.addAction("Open command rail", self.show_rail)
            menu.addAction("Show orb", self.show_orb)
            menu.addSeparator()
            menu.addAction("Quit BR JARVIS", self._request_safe_exit)
            self._tray.setContextMenu(menu)
            self._tray.show()

        def _setup_shortcuts(self) -> None:
            toggle = QShortcut(QKeySequence("Alt+Space"), self)
            toggle.setContext(Qt.ShortcutContext.ApplicationShortcut)
            toggle.activated.connect(self.toggle_visibility)
            escape = QShortcut(QKeySequence("Escape"), self)
            escape.setContext(Qt.ShortcutContext.WidgetShortcut)
            escape.activated.connect(self._escape)
            safe_exit = QShortcut(QKeySequence("Ctrl+D"), self)
            safe_exit.setContext(Qt.ShortcutContext.ApplicationShortcut)
            safe_exit.activated.connect(self._request_safe_exit)

        def _on_runtime_state(self, state: FloatingWidgetState) -> None:
            """Bridge adapter updates to the Qt thread without mutating widgets from workers."""
            self.runtime_state_signal.emit(state)

        @Slot(object)
        def _render_runtime_state(self, state: FloatingWidgetState) -> None:
            self._rail.set_state(state.assistant)
            self._orb.set_state(state.assistant)
            self._rail.set_runtime(self._runtime_text(state.runtime))
            self._rail.set_activity(state.error or state.message or "Ready for a command")
            self._rail.set_input_enabled(state.input != "submitting")
            self._rail.set_voice_state(state.voice, bool(state.capabilities.get("voice_to_text", False)))
            self._rail.set_transcript(state.transcript)
            self._rail.set_speaker_state(state.speaker)
            if self._mode == "context" and state.recent_tasks and state.task in {"none", "completed", "failed"}:
                self._context.show_task_history(state.recent_tasks)
            if state.workspace == "authenticating":
                self._rail.set_activity("Connecting workspace…")
            if state.task in {"running", "waiting_for_approval", "approval"}:
                self._rail.task.setText("Approval" if state.task in {"waiting_for_approval", "approval"} else "Task active")
            elif state.task == "completed":
                self._rail.task.setText("Task complete")
            else:
                self._rail.task.setText("Task")

        @staticmethod
        def _runtime_text(value: str) -> str:
            return {
                "embedded_online": "Online · embedded",
                "external_online": "Online · external",
                "online": "Online",
                "starting": "Starting",
                "reconnecting": "Reconnecting",
                "offline": "Offline",
                "error": "Error",
            }.get(str(value).lower(), "Unknown")

        def _runtime_submit(self, text: str) -> None:
            self._runtime.submit_command(text)

        def _runtime_voice(self) -> None:
            self._runtime.trigger_voice()

        def _stop_voice(self) -> None:
            self._runtime.stop_voice_capture()

        def _runtime_speaker(self) -> None:
            self._runtime.speak_latest_response()

        def _context_action(self, action: str) -> None:
            if action == "open_workspace":
                self._open_workspace()
            elif action == "retry":
                self._runtime.refresh_connectors()
                self.show_rail()
            elif action.startswith("continue_task:"):
                self._runtime.continue_task(action.split(":", 1)[1])
                self.show_rail()

        def show_orb(self) -> None:
            self._mode = "orb"
            self._minimized = True
            self._connector_timer.stop()
            self._stack.setCurrentWidget(self._orb)
            self.setFixedSize(self._mini_size)
            self.show()
            self.raise_()

        def show_rail(self) -> None:
            self._mode = "rail"
            self._minimized = False
            self._stack.setCurrentWidget(self._rail)
            self.setMinimumSize(QSize(0, 0))
            self.setMaximumSize(QSize(16777215, 16777215))
            self.resize(self._bounded_window_size(self._normal_size))
            self._connector_timer.start()
            self.show()
            self.raise_()
            self._rail.input.setFocus()

        def show_context(self) -> None:
            state = self._runtime.snapshot()
            if state.task not in {"running", "waiting_for_approval", "approval"}:
                self._runtime.refresh_recent_tasks()
            self._mode = "context"
            self._minimized = False
            if state.task in {"running", "waiting_for_approval", "approval"}:
                title = "Approval required" if state.task in {"waiting_for_approval", "approval"} else "Current task"
                actions = ("Open workspace",)
                body = state.message or ("Review and approve this task in the workspace." if state.task in {"waiting_for_approval", "approval"} else "A task is active.")
                self._context.show_content("task", title, body, actions=actions)
            elif state.error:
                self._context.show_content("error", "Needs attention", state.error, actions=("Retry", "Open workspace"))
            else:
                self._context.show_content("activity", "Current activity", state.message or "Ready for a command.", actions=("Open workspace",))
            self._stack.setCurrentWidget(self._context)
            self.setMinimumSize(QSize(0, 0))
            self.setMaximumSize(QSize(16777215, 16777215))
            self.resize(self._bounded_window_size(QSize(460, 220)))
            self.show()
            self.raise_()

        def _bounded_window_size(self, preferred: QSize) -> QSize:
            screen = self.screen() or QApplication.primaryScreen()
            if screen is None:
                return preferred
            available = screen.availableGeometry()
            max_width = max(320, int(available.width() * 0.42))
            max_height = max(180, int(available.height() * 0.30))
            return QSize(min(preferred.width(), max_width), min(preferred.height(), max_height))

        def toggle_visibility(self) -> None:
            if self.isVisible():
                self.hide()
            else:
                self.show_orb()

        def _escape(self) -> None:
            if self._mode == "context":
                self.show_rail()
            elif self._mode == "rail":
                self.show_orb()
            else:
                self.hide()

        def _request_safe_exit(self) -> None:
            """Request explicit exit; never trigger while typing in the command field."""
            focus = QApplication.focusWidget()
            if focus is self._rail.input and self._rail.input.text().strip():
                return
            answer = QMessageBox.question(
                self,
                "Exit BR JARVIS",
                "Safely exit the floating dock? Active work owned by another runtime will remain unchanged.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._connector_timer.stop()
            self._runtime.set_runtime("stopping")
            self._tray.hide()
            self.hide()
            QApplication.quit()

        def _open_workspace(self) -> None:
            self._runtime.request_workspace_handoff(on_ready=self._open_workspace_url)

        @staticmethod
        def _open_workspace_url(url: str) -> None:
            import webbrowser

            webbrowser.open(url)

        def set_state(self, state: str) -> None:
            self._runtime.set_assistant_state(state)

        def set_runtime(self, runtime: str) -> None:
            self._runtime.set_runtime(runtime)

        def write_log(self, text: str) -> None:
            self._runtime.update(message=str(text))

        @property
        def speaking(self) -> bool:
            return self._runtime.snapshot().audio == "playing"

        @speaking.setter
        def speaking(self, value: bool) -> None:
            self._runtime.set_audio_state("playing" if value else "inactive")
            self._runtime.set_assistant_state("SPEAKING" if value else "IDLE")

        @property
        def muted(self) -> bool:
            return self._runtime.snapshot().audio == "muted"

        @muted.setter
        def muted(self, value: bool) -> None:
            self._runtime.set_audio_state("muted" if value else "inactive")

        def set_reduced_motion(self, reduced: bool) -> None:
            self._reduced_motion = bool(reduced)
            self._orb.set_state(self._runtime.snapshot().assistant)
            self._rail.dot.set_reduced_motion(self._reduced_motion)

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event) -> None:
            if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            super().mouseMoveEvent(event)

        def closeEvent(self, event) -> None:
            event.ignore()
            self.hide()

else:
    JarvisFloat = None
    OrbSurface = None
    CommandRail = None
    ContextCard = None
