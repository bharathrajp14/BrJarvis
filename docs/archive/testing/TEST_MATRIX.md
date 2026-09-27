# BR JARVIS MK40.2 — Comprehensive Test Matrix

## Subsystem to Test Suite Mapping

| Subsystem | Core Source Modules | Primary Test Files | Test Category | Target Truth Level |
|---|---|---|---|---|
| **Runtime & Lifecycle** | `core/runtime.py`, `core/bootstrap.py`, `apps/bootstrap.py` | `tests/unit/test_core_runtime.py`, `tests/smoke/test_startup_smoke_suite.py` | Unit / Smoke | `INITIALIZES` |
| **Diagnostics & Doctor** | `diagnostics/doctor.py`, `core/health.py` | `tests/smoke/test_runtime_health.py`, `tests/smoke/test_startup_smoke_suite.py` | Smoke | `EXECUTES` |
| **Model Gateway** | `gateway/model_gateway.py`, `gateway/client.py` | `tests/unit/test_model_gateway.py`, `tests/adversarial/test_provider_adapters_chaos.py` | Unit / Adversarial | `CALLS` |
| **Smart Router** | `router/smart_router.py`, `router/diagnostics.py` | `tests/unit/test_smart_model_router.py`, `tests/unit/test_backend_diagnostics.py` | Unit | `CALLS` |
| **Intent Engine** | `core/intent_engine.py` | `tests/unit/test_deterministic_intent.py`, `tests/reliability/test_100_real_world_e2e_matrix.py` | Unit / Reliability | `EXECUTES` |
| **Tool Runtime** | `tools/tool_runtime.py`, `tools/registry.py` | `tests/unit/test_tool_runtime.py`, `tests/unit/test_comprehensive_tool_audit.py` | Unit | `SIDE_EFFECT_OCCURRED` |
| **Task Completion Gate** | `core/execution/completion_gate.py` | `tests/unit/test_contract_truth_levels.py`, `tests/unit/test_universal_execution_runtime.py` | Unit | `TASK_VERIFIED` |
| **Physical Verifiers** | `core/execution/verifier.py` | `tests/unit/test_universal_execution_runtime.py`, `tests/adversarial/test_verification_attack.py` | Unit / Adversarial | `PHYSICAL_STATE_VERIFIED` |
| **Security & Policy** | `security/policy_engine.py`, `guardian/prompt_injection_shield.py` | `tests/unit/test_capability_authorization.py`, `tests/adversarial/test_security_sandbox_hostile.py` | Security | `SIDE_EFFECT_OCCURRED` |
| **Unified Memory** | `memory/unified_memory.py`, `memory/persistent_store.py` | `tests/unit/test_memory_engine.py`, `tests/unit/test_cross_task_isolation.py` | Unit / Reliability | `SIDE_EFFECT_OCCURRED` |
| **Career OS CRM** | `career/crm/database.py`, `career/profile_manager.py` | `tests/unit/test_career_crm_state_machine.py`, `tests/unit/test_career_profile.py` | Career / Unit | `SIDE_EFFECT_OCCURRED` |
| **Career Application** | `career/application_engine/assistant.py` | `tests/unit/test_career_application_engine.py`, `tests/e2e/test_career_os_e2e.py` | Career / E2E | `TASK_VERIFIED` |
| **Career Documents** | `career/resume_engine/`, `career/spreadsheet/excel_engine.py` | `tests/unit/test_career_resume_engine.py`, `tests/unit/test_career_excel_projection.py` | Career / Unit | `ARTIFACT_VALID` |
| **Voice Pipeline** | `voice/assistant.py`, `voice/audio_bus.py`, `voice/stt.py` | `tests/unit/test_audio_bus.py`, `tests/unit/test_voice_pipeline.py` | Unit | `CALLS` |
| **Browser Agent** | `browser/`, `tools/browser_automation.py` | `tests/unit/test_browser_automation.py`, `tests/e2e/test_sandbox_artifact_lifecycle.py` | Unit / E2E | `PHYSICAL_STATE_VERIFIED` |
| **Web Server API** | `apps/web/api/app.py`, `apps/web/api/server.py` | `tests/unit/test_server_web.py`, `tests/e2e/test_production_flows.py` | Integration / E2E | `CALLS` |
