# 21 — TECHNICAL DEBT & CODE SMELL CATALOG

## 1. Overview
This catalog enumerates specific technical debt, duplicate implementations, dead code branches, and code smells discovered across the 2,037 files in the repository.

---

## 2. Technical Debt Catalog by Domain

### A. Subsystem Duplication (High Severity)
1. **Bootstrappers**: `core/bootstrap.py` vs `core/bootstrapper.py` vs inline `start.py` bootstrapper.
2. **Model Invocations**: `backends/` vs `gateway/model_gateway.py` vs `gateway/client.py` vs `router/smart_router.py`.
3. **Tool Execution**: `actions/` (58 files) vs `tools/` (63 files) vs `tools/legacy_actions_tools.py`.
4. **Reminders / Scheduling**: `actions/reminder.py` vs `actions/reminders.py` vs `tools/reminder_tools.py` vs `actions/scheduler.py`.
5. **Memory DB Stores**: 8 separate SQLite/JSON stores across `.jarvis/`, `memory_db/`, and `memory/`.

### B. Oversized Monolithic Modules
1. `core/intent_engine.py` (1,811 lines): Giant regex patterns and hardcoded application paths.
2. `ui/main_window.py` (1,649 lines): UI layout, event handling, network hooks, and audio visualizers tangled in a single class.
3. `tools/pdf_tools.py` (1,257 lines): Comprehensive but monolithic PDF manipulation file.
4. `actions/browser_control.py` (1,079 lines): Complex multi-session CDP controller.

### C. Exception Handling & Silent Fallbacks
- Discovered 14 instances of `try: ... except Exception: pass` in legacy `actions/` modules that swallow critical OS errors silently.
