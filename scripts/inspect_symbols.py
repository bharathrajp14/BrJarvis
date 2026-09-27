import inspect
import importlib
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "src" / "brjarvis"))

modules_to_inspect = [
    "brjarvis.tools.registry",
    "jarvis.tools.registry",
    "brjarvis.router.core",
    "brjarvis.orchestrator.core",
    "brjarvis.memory.store",
    "brjarvis.memory.db",
    "brjarvis.memory.vector_store",
    "jarvis.memory.store",
    "jarvis.memory.db",
    "brjarvis.actions.live_os_control",
    "brjarvis.evolution.engine",
    "brjarvis.core.runtime",
    "jarvis.core.bootstrap",
    "brjarvis.agent.agent_loop",
    "jarvis.agent.loop",
    "brjarvis.web.api.server",
    "brjarvis.apps.bootstrap",
    "brjarvis.apps.cli",
    "brjarvis.guardian.core",
    "brjarvis.contracts.models",
    "brjarvis.contracts.agent",
    "brjarvis.actions.dev_agent",
    "brjarvis.actions.code_helper",
]

print("=== MODULE SYMBOL INSPECTION ===")
for mod_name in modules_to_inspect:
    try:
        mod = importlib.import_module(mod_name)
        classes = [n for n, obj in inspect.getmembers(mod, inspect.isclass) if obj.__module__ == mod_name]
        funcs = [n for n, obj in inspect.getmembers(mod, inspect.isfunction) if obj.__module__ == mod_name]
        print(f"\n[{mod_name}]")
        if classes:
            print(f"  Classes: {', '.join(classes)}")
        if funfuncs := funcs[:10]:
            print(f"  Functions: {', '.join(funfuncs)}{' (truncated)' if len(funcs) > 10 else ''}")
    except Exception as e:
        print(f"\n[{mod_name}] -> Error: {e}")
