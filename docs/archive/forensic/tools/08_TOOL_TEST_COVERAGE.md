# BR JARVIS — TOOL TEST COVERAGE MAPPING

## 1. Automated Test Suite Mapping

| Tool Module | Unit Tests | Integration / E2E Tests | Security Tests | Coverage Status | Notes |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `tools/registry.py` | `test_tool_suite_audit.py` | `test_bootstrap.py` | `test_adversarial_security.py` | **100% COVERED** | Schema and registration verified |
| `tools/tool_runtime.py` | `test_tool_runtime.py` | `test_master_task_lifecycle.py` | `test_path_security_hardening.py` | **100% COVERED** | Execution timeout and errors verified |
| `tools/reminder_tools.py` | `test_tool_suite_audit.py` | None (Direct OS toast) | None | **VERIFIED** | Unit test verifies schema & execution |
| `tools/system_tools.py` | `test_tool_suite_audit.py` | `smoke_startup.py` | None | **VERIFIED** | Verified with psutil mocks & live OS |
| `tools/sandbox_process.py` | `test_regression_fixes.py` | `test_sandbox_artifact_lifecycle.py` | `test_security_sandbox_hostile.py` | **100% COVERED** | Restricted token & path checks verified |
| `tools/export_tools.py` | `test_artifact_manager.py` | `test_sandbox_artifact_lifecycle.py` | `test_path_security_hardening.py` | **100% COVERED** | SHA256 export & host verification |
| `tools/browser_automation.py`| `test_server_web.py` | `test_vision_operator.py` | None | **PARTIALLY VERIFIED**| Playwright mock in CI; live CDP verified |
