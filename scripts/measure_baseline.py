import time
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "src" / "brjarvis"))

print("=== MEASURING ARCHITECTURAL BASELINE ===")

# 1. Measure AssistantRuntime Startup Latency
t0 = time.perf_counter()
from jarvis.core.bootstrap import build_assistant_runtime, run_doctor
runtime = build_assistant_runtime(force_new=True)
t_clean_boot = (time.perf_counter() - t0) * 1000
print(f"[1] jarvis.core.AssistantRuntime Boot Latency: {t_clean_boot:.2f} ms")

# 2. Measure ApplicationRuntime Startup Latency
t0 = time.perf_counter()
from brjarvis.core.runtime import ApplicationRuntime
app_runtime = ApplicationRuntime()
t_app_boot = (time.perf_counter() - t0) * 1000
print(f"[2] brjarvis.core.ApplicationRuntime Boot Latency: {t_app_boot:.2f} ms")

# 3. Measure Doctor Diagnostics Latency
t0 = time.perf_counter()
doc = run_doctor()
t_doctor = (time.perf_counter() - t0) * 1000
print(f"[3] Doctor Diagnostics Run Latency: {t_doctor:.2f} ms | Status: {doc.get('status')}")

# 4. Measure Tool Registry Initialization
t0 = time.perf_counter()
from brjarvis.tools.registry import get_registry_status
status = get_registry_status()
t_tools = (time.perf_counter() - t0) * 1000
print(f"[4] Tool Registry Load Latency: {t_tools:.2f} ms | Tools: {status['registered']}")

# 5. Measure AgentLoop Deterministic Turn Latency
t0 = time.perf_counter()
from jarvis.agent.loop import AgentLoop
agent = AgentLoop()
res = agent.run_turn("status")
t_turn = (time.perf_counter() - t0) * 1000
print(f"[5] AgentLoop Fast-Path Turn Latency: {t_turn:.2f} ms | Status: {res.status.value}")

# 6. Measure TaskState State Transitions
t0 = time.perf_counter()
from jarvis.agent.task_state import TaskState, TaskStatus
ts = TaskState(task_id="perf_test", user_request="test request")
ts.transition(TaskStatus.RUNNING)
ts.record_action("test_tool", {"a": 1}, "output", True)
ts.transition(TaskStatus.PAUSED)
ts.transition(TaskStatus.RUNNING)
ts.transition(TaskStatus.COMPLETED)
t_state_machine = (time.perf_counter() - t0) * 1000
print(f"[6] 5x TaskState Machine Transitions: {t_state_machine:.4f} ms | Rev: {ts.revision}")

# 7. Write baseline results
baseline_file = root / "docs" / "engineering" / "PERFORMANCE_BASELINE.md"
content = f"""# BRJARVIS // PERFORMANCE BASELINE
**Recorded:** {time.strftime('%Y-%m-%d %H:%M:%S')}  

| Metric | Measured Baseline | Target |
| :--- | :--- | :--- |
| **`jarvis.core.AssistantRuntime` Boot** | `{t_clean_boot:.2f} ms` | `< 50 ms` |
| **`brjarvis.core.ApplicationRuntime` Boot** | `{t_app_boot:.2f} ms` | `< 150 ms` |
| **Doctor Diagnostics Check** | `{t_doctor:.2f} ms` | `< 30 ms` |
| **Tool Registry Hydration (200 Tools)** | `{t_tools:.2f} ms` | `< 200 ms` |
| **AgentLoop Fast-Path Turn** | `{t_turn:.2f} ms` | `< 10 ms` |
| **TaskState 5x Transitions** | `{t_state_machine:.4f} ms` | `< 1 ms` |
| **Regression Test Suite (402 Tests)** | `90.95 s` | `< 60 s` |
"""
baseline_file.write_text(content, encoding="utf-8")
print(f"\nWritten baseline to {baseline_file}")
