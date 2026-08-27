"""Static reachability report for the BRJARVIS rebuild (Phase 0).

Walks the import graph from every real entrypoint and reports which modules under
``src/`` and ``apps/`` are never reached. Also resolves dynamic
``importlib.import_module("literal")`` calls, which the tool registry relies on.

Usage:
    python audit/reachability.py            # writes audit/reachability.json
    python audit/reachability.py --print    # also prints a summary
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
ROOTS = [SRC, REPO / "apps", REPO]

# Entrypoints a user or the packaging metadata can actually invoke.
ENTRYPOINTS = [
    "start.py",
    "main.py",
    "server.py",
    "float_widget.py",
    "ui.py",
    "ui_mark.py",
    "permissions.py",
    "apps/cli/main.py",
    "apps/web/main.py",
    "apps/voice/main.py",
    "apps/desktop/main.py",
    "src/brjarvis/apps/bootstrap.py",
    "src/brjarvis/apps/cli.py",
    "src/brjarvis/apps/web.py",
    "src/brjarvis/web/api/app.py",
    "src/brjarvis/core/bootstrap.py",
]


def module_name_for(path: Path) -> str | None:
    """Map a file path to its dotted module name, or None if outside the roots."""
    for root in (SRC, REPO / "apps", REPO):
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        parts = list(rel.with_suffix("").parts)
        if not parts:
            continue
        if parts[-1] == "__init__":
            parts.pop()
        if not parts:
            continue
        return ".".join(parts)
    return None


def build_index() -> dict[str, Path]:
    """Map every dotted module name in the repo to its file."""
    index: dict[str, Path] = {}
    for base in (SRC, REPO / "apps"):
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts or ".venv" in path.parts:
                continue
            name = module_name_for(path)
            if name:
                index.setdefault(name, path)
    for path in REPO.glob("*.py"):
        name = module_name_for(path)
        if name:
            index.setdefault(name, path)
    return index


def imports_of(path: Path, self_module: str | None) -> set[str]:
    """Every module name this file imports, including dynamic string imports.

    ``tools/registry.py`` and ``connectors/hub.py`` load plugins dynamically, so a
    purely syntactic ``import`` scan reports live tool modules as dead. Two dynamic
    forms are resolved here:

    * ``importlib.import_module("tools.pdf_tools")`` — a bare literal that the
      registry retries as ``brjarvis.tools.pdf_tools``. The caller tries both.
    * ``pkgutil.iter_modules(...)`` — package-wide discovery. Every sibling module
      of the calling package is treated as reachable.
    * Any string constant that resolves to a local module. The registry holds its
      plugin list in ``extended_plugins = [...]`` and passes a *variable* to
      ``import_module``, so literal-argument matching alone misses every tool
      module. Over-approximating here is the safe direction for a delete decision.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), str(path))
    except SyntaxError:
        return set()

    found: set[str] = set()
    pkg_parts = (self_module or "").split(".")[:-1]

    if "pkgutil" in path.read_text(encoding="utf-8", errors="replace"):
        found.add(f"__package_glob__:{'.'.join(pkg_parts)}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg_parts[: len(pkg_parts) - node.level + 1]
                target = ".".join([*base, node.module]) if node.module else ".".join(base)
            else:
                target = node.module or ""
            if target:
                found.add(target)
                for alias in node.names:
                    found.add(f"{target}.{alias.name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            literal = node.value
            if "." in literal and " " not in literal and literal.count(".") <= 5:
                found.add(literal)
        elif isinstance(node, ast.Call):
            # importlib.import_module("brjarvis.tools.x") and __import__("...")
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name in {"import_module", "__import__"} and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literal = arg.value
                    if literal.startswith("."):
                        literal = ".".join([*pkg_parts, literal.lstrip(".")])
                    found.add(literal)
    return found


def resolve(index: dict[str, Path], target: str) -> str | None:
    """Resolve an imported name to a local module, longest prefix first.

    Bare literals such as ``tools.pdf_tools`` are also tried under the ``brjarvis``
    package, matching the retry in ``tools.registry._import_single``.
    """
    for candidate_full in (target, f"brjarvis.{target}"):
        parts = candidate_full.split(".")
        for cut in range(len(parts), 0, -1):
            candidate = ".".join(parts[:cut])
            if candidate in index:
                return candidate
    return None


def expand(index: dict[str, Path], target: str) -> list[str]:
    """Resolve one import target into zero or more local module names."""
    if target.startswith("__package_glob__:"):
        pkg = target.split(":", 1)[1]
        if not pkg:
            return []
        prefix = f"{pkg}."
        return [m for m in index if m.startswith(prefix)]
    resolved = resolve(index, target)
    return [resolved] if resolved else []


def walk(index: dict[str, Path], seeds: list[str]) -> set[str]:
    """Transitively reach every local module from the given seed modules."""
    reached: set[str] = set()
    queue = list(seeds)
    while queue:
        name = queue.pop()
        if name in reached or name not in index:
            continue
        reached.add(name)
        for target in imports_of(index[name], name):
            for candidate in expand(index, target):
                if candidate not in reached:
                    queue.append(candidate)
    return reached


def main() -> int:
    index = build_index()

    seeds = []
    for rel in ENTRYPOINTS:
        path = REPO / rel
        if not path.exists():
            continue
        name = module_name_for(path)
        if name:
            seeds.append(name)

    reachable = walk(index, seeds)

    test_files = sorted((REPO / "tests").rglob("*.py")) if (REPO / "tests").exists() else []
    test_seeds: set[str] = set()
    for path in test_files:
        if "__pycache__" in path.parts:
            continue
        for target in imports_of(path, None):
            test_seeds.update(expand(index, target))
    test_reachable = walk(index, sorted(test_seeds))

    unreachable = sorted(set(index) - reachable)
    test_only = sorted(m for m in unreachable if m in test_reachable)
    fully_dead = sorted(m for m in unreachable if m not in test_reachable)

    def loc(name: str) -> int:
        try:
            return len(index[name].read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            return 0

    report = {
        "entrypoints": sorted(seeds),
        "total_modules": len(index),
        "reachable_count": len(reachable),
        "test_only_count": len(test_only),
        "dead_count": len(fully_dead),
        "dead_loc": sum(loc(m) for m in fully_dead),
        "test_only_loc": sum(loc(m) for m in test_only),
        "test_only": [{"module": m, "path": str(index[m].relative_to(REPO)), "loc": loc(m)} for m in test_only],
        "dead": [{"module": m, "path": str(index[m].relative_to(REPO)), "loc": loc(m)} for m in fully_dead],
    }

    out = REPO / "audit" / "reachability.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"modules={report['total_modules']} reachable={report['reachable_count']} "
          f"test_only={report['test_only_count']} ({report['test_only_loc']} LOC) "
          f"dead={report['dead_count']} ({report['dead_loc']} LOC)")

    if "--print" in sys.argv:
        print("\n--- dead (unreachable from entrypoints and tests) ---")
        for item in sorted(report["dead"], key=lambda d: -d["loc"]):
            print(f"{item['loc']:6d}  {item['path']}")
        print("\n--- test-only (reachable only from tests) ---")
        for item in sorted(report["test_only"], key=lambda d: -d["loc"]):
            print(f"{item['loc']:6d}  {item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
