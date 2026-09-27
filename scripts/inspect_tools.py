import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "src" / "brjarvis"))

from brjarvis.tools.registry import TOOL_REGISTRY, _ensure_builtins_registered

_ensure_builtins_registered()
print(f"Total tools in _TOOL_REGISTRY: {len(_TOOL_REGISTRY)}")
for name, data in sorted(_TOOL_REGISTRY.items()):
    desc = data.get("description", "")
    risk = data.get("risk", data.get("risk_level", "unknown"))
    print(f"  - {name:30} | Risk: {str(risk):10} | {desc[:60]}")
