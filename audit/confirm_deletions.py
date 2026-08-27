"""Confirm the delete list before Phase 0 removes anything.

Cross-checks every module that both ``reachability.py`` (static) and
``runtime_probe.py`` (runtime ``sys.modules``) call dead against a reference sweep of
the whole repository: other Python files, config JSON/YAML, batch scripts, and CI.

Two refinements matter for a correct answer:

* Search for *import forms* of the module (``brjarvis.pkg.mod``, ``pkg.mod``,
  ``from .mod``, ``pkg/mod.py``), never the bare stem. A stem search holds back
  ``computer/operator.py`` because a React file contains the word "operator".
* Iterate to a fixpoint. A module referenced only by other dead modules is dead too
  (``memory/knowledge_graph.py`` is held only by the dead ``memory/temporal_kg.py``).

Prose files cannot keep code alive, so markdown, the changelog, generated egg-info,
lockfiles, and the secrets baseline are excluded. Config, scripts, and CI are not.

Usage:
    python audit/confirm_deletions.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Mentions in these paths do not keep a module alive.
IGNORED_PREFIXES = (
    "docs/",
    "audit/",
    "notes/",
    "brjarvis.egg-info/",
    "legacy/",
    ".secrets.baseline",
    "CHANGELOG.md",
    "readme.md",
    "frontend/pnpm-lock.yaml",
    "frontend/dist/",
)
IGNORED_SUFFIXES = (".md", ".pyc", ".png", ".mmd", ".txt")

# Kept regardless of reachability: packaging entry points and package markers.
KEEP = {
    "setup.py",
    "setup_native.py",
    "apps/__init__.py",
    "apps/web/api/__init__.py",
}


def import_patterns(rel: str) -> tuple[list[str], list[str]]:
    """Import forms for this module, split into global and package-local patterns.

    Relative forms (``from .server import``) are only meaningful inside the module's
    own package. Searching for them repo-wide holds back
    ``apps/web/dashboard/server.py`` because an unrelated file contains
    ``from brjarvis.web.api.server import create_app``.
    """
    path = Path(rel)
    parts = list(path.with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return [], []

    dotted = ".".join(parts)
    stem = parts[-1]
    global_patterns = {dotted, "/".join(parts) + ".py", "\\".join(parts) + ".py"}
    if parts[0] == "brjarvis" and len(parts) > 1:
        global_patterns.add(".".join(parts[1:]))
    local_patterns = {f"import {stem}", f"from .{stem}", f".{stem} import"}
    return sorted(global_patterns), sorted(local_patterns)


def references(rel: str) -> list[str]:
    """Files other than ``rel`` that reference this module as an import target."""
    global_patterns, local_patterns = import_patterns(rel)
    package_dir = str(Path(rel).parent).replace("\\", "/")
    hits: set[str] = set()

    def sweep(pattern: str, restrict_to_package: bool) -> None:
        out = subprocess.run(
            ["git", "grep", "-l", "-F", pattern],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        for line in out.splitlines():
            line = line.strip().replace("\\", "/")
            if not line or line == rel.replace("\\", "/"):
                continue
            if line.startswith(IGNORED_PREFIXES) or line.endswith(IGNORED_SUFFIXES):
                continue
            if restrict_to_package and str(Path(line).parent).replace("\\", "/") != package_dir:
                continue
            hits.add(line)

    for pattern in global_patterns:
        sweep(pattern, restrict_to_package=False)
    for pattern in local_patterns:
        sweep(pattern, restrict_to_package=True)
    return sorted(hits)


def main() -> int:
    probe = json.loads((REPO / "audit" / "runtime_probe.json").read_text(encoding="utf-8"))

    candidates: list[dict] = []
    kept: list[dict] = []
    for item in probe["confirmed_dead"]:
        rel = item["path"].replace("\\", "/")
        if rel in KEEP:
            kept.append(item)
        else:
            candidates.append({**item, "rel": rel, "referenced_by": references(rel)})

    # Fixpoint: a module referenced only by other dead modules is itself dead.
    dead_paths = {c["rel"] for c in candidates}
    while True:
        newly_held = {
            c["rel"]
            for c in candidates
            if c["rel"] in dead_paths and any(r not in dead_paths for r in c["referenced_by"])
        }
        if not newly_held:
            break
        dead_paths -= newly_held

    clear = [c for c in candidates if c["rel"] in dead_paths]
    held = [c for c in candidates if c["rel"] not in dead_paths]

    report = {
        "clear_to_delete": sorted(clear, key=lambda d: -d["loc"]),
        "clear_count": len(clear),
        "clear_loc": sum(d["loc"] for d in clear),
        "held_back": sorted(held, key=lambda d: -d["loc"]),
        "kept_by_policy": kept,
    }
    (REPO / "audit" / "delete_list.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"clear to delete: {len(clear)} modules, {report['clear_loc']} LOC")
    for item in report["clear_to_delete"]:
        print(f"  {item['loc']:6d}  {item['rel']}")
    print(f"\nheld back (live references): {len(held)}")
    for item in report["held_back"]:
        print(f"  {item['loc']:6d}  {item['rel']}  <- {', '.join(item['referenced_by'][:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
