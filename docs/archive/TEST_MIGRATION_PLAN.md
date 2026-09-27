# BR JARVIS — TEST SUITE MIGRATION & VALIDATION PLAN

## 1. Test Verification Strategy
All architectural refactoring and consolidation steps must pass the 116 test files in `tests/` without regression.

---

## 2. Test Verification Gates by Phase
| Phase | Target Modules | Automated Test Commands | Pass Criteria |
| :--- | :--- | :--- | :--- |
| **Phase 1: Security** | `security/`, `guardian/` | `pytest tests/unit/test_path_security_hardening.py tests/unit/test_prompt_injection_shield.py` | 100% Pass, Zero security breaches |
| **Phase 2: Core & Bootstrap** | `core/`, `start.py` | `pytest tests/unit/test_bootstrap.py tests/unit/test_lifecycle.py tests/unit/test_di.py` | Clean container instantiation |
| **Phase 3: Gateway & Models** | `gateway/`, `backends/` | `pytest tests/unit/test_model_gateway.py tests/unit/test_smart_model_router.py` | Circuit-breakers and fallbacks verified |
| **Phase 4: Tools & Actions** | `tools/`, `actions/`, `connectors/` | `pytest tests/unit/test_tool_runtime.py tests/unit/test_tool_suite_audit.py` | All tool schemas valid and executable |
| **Phase 5: Memory & Storage** | `memory/`, `history/` | `pytest tests/unit/test_regression_fixes.py tests/unit/test_sqlite_lock.py` | Concurrent writes verified |
| **Phase 6: Full Suite E2E** | All Subsystems | `pytest tests/` & `python scripts/smoke_startup.py` | All 116 test suites pass |
