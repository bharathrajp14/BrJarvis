# BR JARVIS MK40.2 — Repair & Regression Prevention Matrix

## Bug to Regression Test Traceability

| ID | Defect / Vulnerability | Root Cause | Fix Applied | Permanent Regression Test |
|---|---|---|---|---|
| **REG-01** | `NameError: base_dir is not defined` in `CoreBootstrapper.get_status()` | Unbound variable in diagnostic status method | Bound `base_dir` to `paths.PROJECT_ROOT` and imported `os` | `tests/smoke/test_startup_smoke_suite.py::test_core_bootstrapper_get_status_no_name_error` |
| **REG-02** | Bare imports causing circular import hazards in `core/runtime.py` and `core/bootstrap.py` | Legacy relative/bare import style | Canonicalized imports to `from brjarvis...` | `tests/unit/test_core_runtime.py`, `tests/smoke/test_startup_smoke_suite.py` |
| **REG-03** | Weak assertions in 100 Real-World Matrix | Tests asserted `len(ranked) > 0` without domain validation | Added semantic domain checking & capability verification | `tests/reliability/test_100_real_world_e2e_matrix.py` |
| **REG-04** | Missing `task_id` and `step_id` in `ToolResult` | Dataclass omitted execution hierarchy tracking | Added `task_id`, `step_id`, `duration`, and `verification` properties | `tests/unit/test_contract_truth_levels.py::test_tool_result_canonical_fields` |
| **REG-05** | False success claims without physical verification | Lower execution tiers claiming complete task success | Integrated `UniversalVerifier` & `TaskCompletionGate` truth checks | `tests/unit/test_contract_truth_levels.py::test_level_8_app_command_sent_does_not_imply_level_9_task_verified` |
| **REG-06** | Cross-task state leakage under concurrency | Working memory and traces lacking task isolation bounds | Strict task ID scoping and thread-safe lock isolation | `tests/unit/test_cross_task_isolation.py::test_concurrent_working_memory_isolation` |
| **REG-07** | Root package `brjarvis` shim attribute resolution | Submodules not lazily accessible on root package object | Added dynamic `__getattr__` module resolution in `brjarvis.py` | `tests/smoke/test_startup_smoke_suite.py::test_root_brjarvis_shim_attributes` |
