import inspect
import importlib
import sys
from pathlib import Path

# Add src and src/brjarvis to path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "src" / "brjarvis"))

report = {}

# 1. Inspect entrypoints
entrypoints = {
    "start.py": root / "start.py",
    "server.py": root / "server.py",
    "brjarvis.apps.cli": "brjarvis.apps.cli",
    "brjarvis.apps.bootstrap": "brjarvis.apps.bootstrap",
    "brjarvis.apps.web": "brjarvis.apps.web",
    "brjarvis.ui.widgets": "brjarvis.ui.widgets",
    "brjarvis.voice.assistant": "brjarvis.voice.assistant",
}

print("=== INSPECTING ENTRYPOINTS ===")
for name, target in entrypoints.items():
    if isinstance(target, Path):
        print(f"[File] {name}: exists={target.exists()}")
    else:
        try:
            mod = importlib.import_module(target)
            print(f"[Module] {name}: loaded successfully (has main={'main' in dir(mod)})")
        except Exception as e:
            print(f"[Module] {name}: error loading - {e}")

# 2. Inspect Tool Registry
print("\n=== INSPECTING TOOL RUNTIME & REGISTRY ===")
try:
    from brjarvis.tools.registry import ToolRegistry, get_tool_registry
    registry = get_tool_registry()
    tools = registry.list_tools() if hasattr(registry, "list_tools") else []
    print(f"brjarvis ToolRegistry: {len(tools)} tools registered")
    print(f"Sample tools: {[t.get('name', getattr(t, 'name', str(t))) for t in tools[:10]]}")
except Exception as e:
    print(f"brjarvis ToolRegistry error: {e}")

try:
    from jarvis.tools.registry import ToolRegistry as CleanRegistry
    clean_reg = CleanRegistry()
    print(f"jarvis clean ToolRegistry: {len(clean_reg.list_tools())} tools registered")
except Exception as e:
    print(f"jarvis ToolRegistry error: {e}")

# 3. Inspect Model Gateway / Routing
print("\n=== INSPECTING MODEL GATEWAY & ROUTING ===")
try:
    from brjarvis.gateway.model_gateway import ModelGateway
    print("brjarvis ModelGateway imported successfully")
except Exception as e:
    print(f"brjarvis ModelGateway error: {e}")

try:
    from brjarvis.router.core import IntentRouter, route_request
    print("brjarvis IntentRouter imported successfully")
except Exception as e:
    print(f"brjarvis IntentRouter error: {e}")

try:
    from jarvis.gateway.model_gateway import ModelGateway as CleanGateway
    print("jarvis clean ModelGateway imported successfully")
except Exception as e:
    print(f"jarvis clean ModelGateway error: {e}")

# 4. Inspect Memory Systems
print("\n=== INSPECTING MEMORY STORES ===")
try:
    from brjarvis.memory.sqlite_memory import SQLiteMemory
    print("brjarvis SQLiteMemory imported successfully")
except Exception as e:
    print(f"brjarvis SQLiteMemory error: {e}")

try:
    from brjarvis.memory.vector_store import VectorMemoryStore
    print("brjarvis VectorMemoryStore imported successfully")
except Exception as e:
    print(f"brjarvis VectorMemoryStore error: {e}")

try:
    from jarvis.memory.store import MemoryStore as CleanMemoryStore
    print("jarvis clean MemoryStore imported successfully")
except Exception as e:
    print(f"jarvis clean MemoryStore error: {e}")

# 5. Inspect Agent Loop & Orchestrator
print("\n=== INSPECTING AGENT RUNTIME & ORCHESTRATOR ===")
try:
    from brjarvis.orchestrator.core import Orchestrator
    print("brjarvis Orchestrator imported successfully")
except Exception as e:
    print(f"brjarvis Orchestrator error: {e}")

try:
    from brjarvis.agent.agent_loop import AgentLoop
    print("brjarvis AgentLoop imported successfully")
except Exception as e:
    print(f"brjarvis AgentLoop error: {e}")

try:
    from jarvis.agent.loop import AgentLoop as CleanAgentLoop
    print("jarvis clean AgentLoop imported successfully")
except Exception as e:
    print(f"jarvis clean AgentLoop error: {e}")

# 6. Inspect Computer Use & Browser
print("\n=== INSPECTING COMPUTER / BROWSER USE ===")
try:
    from brjarvis.actions.live_os_control import LiveOSControl
    print("brjarvis LiveOSControl imported successfully")
except Exception as e:
    print(f"brjarvis LiveOSControl error: {e}")

try:
    from brjarvis.actions.browser_control import BrowserController
    print("brjarvis BrowserController imported successfully")
except Exception as e:
    print(f"brjarvis BrowserController error: {e}")

# 7. Inspect Evolution / Self-Improvement
print("\n=== INSPECTING EVOLUTION ENGINE ===")
try:
    from brjarvis.evolution.engine import EvolutionEngine
    print("brjarvis EvolutionEngine imported successfully")
except Exception as e:
    print(f"brjarvis EvolutionEngine error: {e}")
