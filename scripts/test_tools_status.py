import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "src" / "brjarvis"))

from brjarvis.tools.registry import get_registry_status, TOOL_SCHEMAS

status = get_registry_status()
print(f"Registered tools: {status['registered']}")
print(f"Failed tools/plugins: {status['failed']}")
print("\nTool names:")
for t in status['tool_names']:
    print(f"  {t}")
