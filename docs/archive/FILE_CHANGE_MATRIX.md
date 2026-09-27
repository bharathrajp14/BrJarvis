# BR JARVIS — FILE CHANGE MATRIX

## 1. Master Remediation Matrix
| Target File | Subsystem | Action | Target / Rationale | Callers Affected | Tests Required | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `core/bootstrapper.py` | `core` | **CONSOLIDATE** | Merge duplicate logic into `core/bootstrap.py` | `scripts/test_bootstrap.py` | `test_bootstrap.py` | LOW |
| `core/sanitizer.py` | `core` | **CONSOLIDATE** | Merge 4-line stub into `security/sanitizer.py` | None | `test_path_security_hardening.py` | LOW |
| `start.py` | Root | **REFACTOR** | Slim down 1,000-line monolith to thin launcher delegating to `core/bootstrap.py` | CLI / UI launch scripts | `test_smoke_startup.py` | MEDIUM |
| `actions/reminders.py` | `actions` | **CONSOLIDATE** | Merge into `tools/reminder_tools.py` | `core/intent_engine.py` | `test_whatsapp_calendar_automation.py` | LOW |
| `actions/reminder.py` | `actions` | **CONSOLIDATE** | Merge into `tools/reminder_tools.py` | `core/intent_engine.py` | `test_whatsapp_calendar_automation.py` | LOW |
| `actions/system_cleanup.py`| `actions`| **CONSOLIDATE** | Merge into `tools/system_tools.py` | `core/intent_engine.py` | `test_tool_runtime.py` | LOW |
| `actions/system_optimizer.py`| `actions`| **CONSOLIDATE**| Merge into `tools/system_tools.py` | `core/intent_engine.py` | `test_tool_runtime.py` | LOW |
| `actions/browser_control.py`| `actions`| **REFACTOR** | Modularize 1,079 lines into `tools/browser_tools.py` | `core/intent_engine.py` | `test_server_web.py` | MEDIUM |
| `dashboard/server.py` | `dashboard` | **CONSOLIDATE** | Mount dashboard endpoints onto FastAPI `api/routes/` | `brjarvis.py` | `test_server_web.py` | LOW |
| `orchestrator/speculative.py`| `orchestrator`| **CONSOLIDATE**| Merge 18-line stub into `reasoning/speculative.py` | `orchestrator/core.py` | `test_regression_fixes.py` | LOW |
| `workspace/browser_user_data/`| `workspace`| **CLEANUP** | Add to `.gitignore`, purge binary cache files | None | None | LOW |
