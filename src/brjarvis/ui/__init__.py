# ui/__init__.py — JARVIS Desktop UI Package Initialization
"""
JARVIS Desktop UI Package.

Provides:
  - setup_qt_paths()  : configure Qt plugin paths for Windows
  - _base_dir()       : canonical project-root resolver used by all ui/ modules
  - _WIN_HIDE         : subprocess flag to suppress console windows on Windows
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def setup_qt_paths() -> None:
    """Configure Qt plugin and platform paths for PySide6/PyQt6 on Windows."""
    if sys.platform == "win32":
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        for _mod_name in ("PySide6", "PyQt6", "PyQt5"):
            try:
                _m = __import__(_mod_name)
                _mod_dir = os.path.dirname(_m.__file__)
                _plugins_dir = os.path.join(_mod_dir, "plugins")
                _platforms_dir = os.path.join(_plugins_dir, "platforms")
                os.environ["QT_PLUGIN_PATH"] = _plugins_dir
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = _platforms_dir
                if hasattr(os, "add_dll_directory"):
                    for _d in (_mod_dir, _plugins_dir, _platforms_dir):
                        if os.path.exists(_d):
                            try:
                                os.add_dll_directory(_d)
                            except Exception:
                                pass
                break
            except ImportError:
                continue


def _base_dir() -> Path:
    """
    Return the project root directory regardless of whether the app is
    frozen (PyInstaller) or running from source.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    from brjarvis.core.paths import paths

    return paths.PROJECT_ROOT


# ── Platform-specific subprocess flag ────────────────────────────────────────
if platform.system() == "Windows":
    _WIN_HIDE: dict = {"creationflags": subprocess.CREATE_NO_WINDOW}
else:
    _WIN_HIDE: dict = {}

# Call setup_qt_paths immediately when the package is imported so that any
# module doing `from ui._qt import *` already has the correct env vars set.
setup_qt_paths()


# ── Re-export public UI API ───────────────────────────────────────────────────
# The ui/ package directory shadows ui.py at the project root — Python always
# prefers a package directory over a same-named .py file. Therefore,
# `from ui import JarvisUI` resolves here (ui/__init__.py), NOT to ui.py.
# We re-export all public symbols so all callers get what they expect.
#
# IMPORTANT: Use lazy imports to prevent circular import.
#   ui/__init__.py  →  ui.app  →  ui.main_window  →  ui.overlays  →  ui.widgets
#   →  ui.colors  →  ui.__init__    (would be circular if done at module level)
#
def __getattr__(name: str):
    """Lazy re-export: resolve ui.JarvisUI, ui._RootShim, ui.MainWindow, ui.C, etc. on first access."""
    _app_public = {
        "JarvisUI",
        "HeadlessJarvisUI",
        "is_gui_available",
        "_RootShim",
    }
    if name in _app_public:
        from . import app as _app  # noqa: PLC0415

        val = getattr(_app, name, None)
        if val is not None:
            globals()[name] = val
            return val

    _window_public = {
        "MainWindow",
        "JARVISMainWindow",
    }
    if name in _window_public:
        from . import main_window as _win  # noqa: PLC0415

        val = getattr(_win, name, None)
        if val is not None:
            globals()[name] = val
            return val

    _colors_public = {
        "C",
        "apply_ui_accent",
        "current_palette",
        "retheme_all_widgets",
        "qcol",
        "DEFAULT_UI_COLOR",
    }
    if name in _colors_public:
        from . import colors as _col  # noqa: PLC0415

        val = getattr(_col, name, None)
        if val is not None:
            globals()[name] = val
            return val

    _widgets_public = {
        "HudCanvas",
        "MetricBar",
        "LogWidget",
        "SubAgentTaskWidget",
        "SubAgentTaskPanel",
        "FileDropZone",
    }
    if name in _widgets_public:
        from . import widgets as _wid  # noqa: PLC0415

        val = getattr(_wid, name, None)
        if val is not None:
            globals()[name] = val
            return val

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
