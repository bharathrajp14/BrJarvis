from pathlib import Path
import shutil

repo = Path(__file__).resolve().parents[1]
source = repo / "frontend" / "dist"
target = repo / "src" / "brjarvis" / "web" / "static" / "dist"

if not (source / "index.html").is_file():
    raise SystemExit("frontend/dist/index.html is missing; run the frontend build first")

if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target)
print(f"Copied frontend build to {target}")
