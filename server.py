#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — BR JARVIS Production Server Entrypoint Shim
======================================================
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src and apps/web to sys.path
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
_APPS_WEB = _ROOT / "apps" / "web"
for _p in [str(_SRC), str(_APPS_WEB), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import brjarvis
from brjarvis.core.paths import ensure_canonical_python
ensure_canonical_python()

from brjarvis.apps.web import main

try:
    from brjarvis.web.api.server import create_app
    app = create_app()
except Exception:
    try:
        from jarvis.surfaces.web.server import create_app
        app = create_app()
    except Exception:
        app = None  # type: ignore[assignment]

def __getattr__(name: str):
    if name == "app":
        global app
        if app is None:
            try:
                from brjarvis.web.api.server import create_app
                app = create_app()
            except Exception:
                try:
                    from jarvis.surfaces.web.server import create_app
                    app = create_app()
                except Exception:
                    pass
        return app
    import brjarvis.apps.web as _w
    return getattr(_w, name)

if __name__ == "__main__":
    sys.exit(main())
