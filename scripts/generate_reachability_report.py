"""Generate a conservative import reachability report for the BrJarvis rebuild.

The report intentionally treats dynamic imports as unresolved rather than guessing.
It is a discovery aid for Phase 0, not permission to delete code by itself.
"""

from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable


PACKAGE = "brjarvis"


def module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([PACKAGE, *parts])


def discover_modules(root: Path) -> dict[str, Path]:
    return {
        module_name(path, root): path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    }


def resolve_relative(current: str, level: int, imported: str | None) -> str | None:
    current_parts = current.split(".")
    # A relative import at level one starts from the current package.
    base = current_parts[:-level]
    if imported:
        base.extend(imported.split("."))
    return ".".join(base) if base else None


def imported_modules(path: Path, current: str, known: set[str]) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return set()

    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                candidates = [alias.name]
                parts = alias.name.split(".")
                candidates.extend(".".join(parts[:index]) for index in range(len(parts) - 1, 0, -1))
                result.update(candidate for candidate in candidates if candidate in known)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = resolve_relative(current, node.level, node.module)
                if base and base in known:
                    result.add(base)
                for alias in node.names:
                    if alias.name == "*" or not base:
                        continue
                    candidate = f"{base}.{alias.name}"
                    if candidate in known:
                        result.add(candidate)
            elif node.module:
                parts = node.module.split(".")
                candidates = [node.module]
                candidates.extend(".".join(parts[:index]) for index in range(len(parts) - 1, 0, -1))
                result.update(candidate for candidate in candidates if candidate in known)
    return result


def build_graph(modules: dict[str, Path]) -> dict[str, set[str]]:
    known = set(modules)
    return {name: imported_modules(path, name, known) for name, path in modules.items()}


def external_seed_imports(paths: Iterable[Path], known: set[str]) -> set[str]:
    seeds: set[str] = set()
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    parts = alias.name.split(".")
                    seeds.update(".".join(parts[:index]) for index in range(len(parts), 0, -1) if ".".join(parts[:index]) in known)
            elif isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                seeds.update(".".join(parts[:index]) for index in range(len(parts), 0, -1) if ".".join(parts[:index]) in known)
    return seeds


def reachable(graph: dict[str, set[str]], seeds: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    queue = deque(seed for seed in seeds if seed in graph)
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(graph[current] - seen)
    return seen


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    src_root = repo / "src" / PACKAGE
    modules = discover_modules(src_root)
    graph = build_graph(modules)

    start_seeds = {"brjarvis.apps.bootstrap", "brjarvis.core.version", "brjarvis.diagnostics.doctor"}
    app_paths = [
        path
        for path in (repo / "apps").rglob("*.py")
        if "__pycache__" not in path.parts and path.is_file()
    ]
    app_seeds = external_seed_imports(app_paths, set(modules))
    package_app_seeds = {name for name in modules if name == "brjarvis.apps" or name.startswith("brjarvis.apps.")}
    surface_seeds = {
        "brjarvis.web.api.server",
        "brjarvis.core.cli",
        "brjarvis.voice.assistant",
        "brjarvis.desktop.float_widget",
        "brjarvis.career",
    }

    start_reachable = reachable(graph, start_seeds)
    app_reachable = reachable(graph, app_seeds)
    package_app_reachable = reachable(graph, package_app_seeds)
    surface_reachable = reachable(graph, surface_seeds)
    all_reachable = start_reachable | app_reachable | package_app_reachable | surface_reachable

    report = {
        "description": "Conservative static import reachability; dynamic imports are not inferred.",
        "module_count": len(modules),
        "python_loc": sum(len(path.read_text(encoding="utf-8", errors="replace").splitlines()) for path in modules.values()),
        "seed_groups": {
            "start": sorted(start_seeds),
            "apps": sorted(app_seeds),
            "package_apps": sorted(package_app_seeds),
            "surface_entrypoints": sorted(surface_seeds),
        },
        "reachable_counts": {
            "from_start": len(start_reachable),
            "from_apps": len(app_reachable),
            "from_package_apps": len(package_app_reachable),
            "from_surfaces": len(surface_reachable),
            "union": len(all_reachable),
        },
        "reachable_union": sorted(all_reachable),
        "unreachable_union": sorted(set(modules) - all_reachable),
        "unreachable_paths": sorted(str(modules[name].relative_to(repo)) for name in set(modules) - all_reachable),
    }

    output = repo / "audit" / "reachability.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), **report["reachable_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
