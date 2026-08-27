"""Runtime module probe (Phase 0 companion to reachability.py).

Static analysis cannot see modules that plugin loaders resolve from names that do not
match their import path (provider backends, skills, connectors). This script boots the
real system as far as it can without network or a GUI, then records every
``brjarvis.*`` module that actually landed in ``sys.modules``.

A module is only a deletion candidate when it is absent from BOTH this runtime set and
the static reachable set in ``audit/reachability.json``.

Usage:
    python audit/runtime_probe.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# Keep the probe offline and headless.
os.environ.setdefault("JARVIS_OFFLINE", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

steps: dict[str, str] = {}


def step(label: str, fn) -> None:
    """Run one boot step, recording success or the failure reason."""
    try:
        fn()
        steps[label] = "ok"
    except Exception as exc:  # noqa: BLE001 - probe records every failure verbatim
        steps[label] = f"{type(exc).__name__}: {exc}"
        if os.environ.get("PROBE_TRACE"):
            traceback.print_exc()


def load_tool_registry() -> None:
    from brjarvis.tools import registry

    # ``full=True`` pulls the extended plugin list, not just core plugins.
    registry._import_plugins(full=True)


def load_connectors() -> None:
    from brjarvis.connectors import hub

    hub.discover_connectors() if hasattr(hub, "discover_connectors") else hub.get_hub()


def load_skills() -> None:
    from brjarvis.skills import loader

    loader.load_skills() if hasattr(loader, "load_skills") else None


def load_backends() -> None:
    from brjarvis.router import core as router_core

    router_core.AgentRouter()


def load_web_app() -> None:
    from brjarvis.web.api.app import create_app

    create_app()


def load_cli() -> None:
    import brjarvis.apps.bootstrap  # noqa: F401
    import brjarvis.core.terminal.commands  # noqa: F401


def load_desktop() -> None:
    import brjarvis.ui.main_window  # noqa: F401


def load_voice() -> None:
    import brjarvis.voice.assistant  # noqa: F401


def load_career() -> None:
    import brjarvis.career.models  # noqa: F401
    import brjarvis.career.tools  # noqa: F401


def main() -> int:
    step("tool_registry", load_tool_registry)
    step("connectors", load_connectors)
    step("skills", load_skills)
    step("backends", load_backends)
    step("web_app", load_web_app)
    step("cli", load_cli)
    step("desktop", load_desktop)
    step("voice", load_voice)
    step("career", load_career)

    loaded = sorted(m for m in sys.modules if m.startswith("brjarvis") or m.startswith("apps"))

    static_path = REPO / "audit" / "reachability.json"
    static = json.loads(static_path.read_text(encoding="utf-8")) if static_path.exists() else {}
    dead_static = {d["module"] for d in static.get("dead", [])}

    # Names in reachability.json are relative to src/, i.e. already "brjarvis.x".
    still_dead = sorted(dead_static - set(loaded))
    revived = sorted(dead_static & set(loaded))

    by_module = {d["module"]: d for d in static.get("dead", [])}
    report = {
        "boot_steps": steps,
        "runtime_loaded_count": len(loaded),
        "static_dead_count": len(dead_static),
        "revived_by_runtime": [by_module[m] for m in revived],
        "confirmed_dead": [by_module[m] for m in still_dead],
        "confirmed_dead_loc": sum(by_module[m]["loc"] for m in still_dead),
    }
    out = REPO / "audit" / "runtime_probe.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("boot steps:")
    for label, result in steps.items():
        print(f"  {label:15s} {result}")
    print(f"\nruntime-loaded brjarvis modules: {len(loaded)}")
    print(f"static-dead revived by runtime:  {len(revived)}")
    print(f"confirmed dead: {len(still_dead)} modules, {report['confirmed_dead_loc']} LOC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
