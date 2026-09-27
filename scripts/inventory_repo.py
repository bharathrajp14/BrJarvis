import os
from pathlib import Path
from collections import defaultdict
import json

root = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "dist", "__pycache__",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", ".pyright", ".idea", ".vscode"
}

summary = {
    "by_top_level": defaultdict(lambda: {"files": 0, "lines": 0}),
    "by_package_src": defaultdict(lambda: {"files": 0, "lines": 0}),
    "by_test_type": defaultdict(lambda: {"files": 0, "lines": 0}),
    "entrypoints": [],
    "python_files": [],
}

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
    rel_dir = Path(dirpath).relative_to(root)
    
    for f in filenames:
        p = Path(dirpath) / f
        rel = p.relative_to(root)
        top = rel.parts[0] if len(rel.parts) > 1 else "root"
        
        try:
            lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            lines = 0

        summary["by_top_level"][top]["files"] += 1
        summary["by_top_level"][top]["lines"] += lines

        if top == "src" and len(rel.parts) > 2:
            pkg = f"{rel.parts[0]}/{rel.parts[1]}/{rel.parts[2]}"
            summary["by_package_src"][pkg]["files"] += 1
            summary["by_package_src"][pkg]["lines"] += lines

        if top == "tests" and len(rel.parts) > 2:
            test_cat = f"{rel.parts[0]}/{rel.parts[1]}"
            summary["by_test_type"][test_cat]["files"] += 1
            summary["by_test_type"][test_cat]["lines"] += lines

        if p.suffix == ".py":
            summary["python_files"].append(str(rel))

print("=== BY TOP LEVEL ===")
for cat, data in sorted(summary["by_top_level"].items(), key=lambda x: -x[1]["lines"]):
    print(f"{cat:25} | {data['files']:5} files | {data['lines']:8} lines")

print("\n=== BY SRC SUBSYSTEM ===")
for cat, data in sorted(summary["by_package_src"].items(), key=lambda x: -x[1]["lines"]):
    print(f"{cat:35} | {data['files']:5} files | {data['lines']:8} lines")

print("\n=== BY TEST DIRECTORY ===")
for cat, data in sorted(summary["by_test_type"].items(), key=lambda x: -x[1]["lines"]):
    print(f"{cat:25} | {data['files']:5} files | {data['lines']:8} lines")
