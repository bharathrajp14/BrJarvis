# 23 — CROSS-FILE & CROSS-SUBSYSTEM INTERACTION FINDINGS

## 1. Interaction Mapping Across Architectural Boundaries

### A. Core Runtime ↔ UI ↔ Voice Thread Interaction
- **Finding**: When `start.py` launches `ui_mark.py`, it starts `BRVoiceAssistant` in a background daemon thread (`threading.Thread`). The voice thread pushes audio waveform data directly to `ui/main_window.py`.
- **Thread Safety**: Qt GUI updates from background threads must strictly pass through Qt Signals (`pyqtSignal` / `Signal`) rather than directly calling UI methods to avoid race conditions and Windows DWM UI thread deadlocks.
- **Remediation**: Use `ui/app.py` Signal Bridge for all cross-thread UI updates.

### B. Agent Planner ↔ Tools ↔ Security Policy
- **Finding**: When `orchestrator/core.py` parses a tool invocation, it delegates execution to `agent/executor.py`. `agent/executor.py` checks `security/policy_engine.py`.
- **Finding**: Some intent rules in `core/intent_engine.py` bypassed `agent/executor.py` and called `actions/open_app.py` directly.
- **Remediation**: All execution must pass through the deterministic 6-tuple policy engine before touching OS resources.
