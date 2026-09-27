# BR JARVIS — MASTER SYSTEM REMEDIATION PLAN (17 PHASES)

## 1. Strategic Principles & System-Wide Invariants
1. **Never Report Unverified Success**: A tool return code of `0` or API return value of `OK` is strictly treated as `ACTION_EXECUTED`. The system only transitions to `VERIFIED` after physical post-condition validation.
2. **Strict Sandbox Isolation**: Unexported sandbox paths are never passed to host applications or browsers.
3. **Decoupled Fallback Chains**: Cloud rate limits (429) and timeouts trigger immediate local/secondary model escalation without task collapse.
4. **Unified Multi-Modal Coordinate Space**: Physical screen pixels, logical Win32 coordinates, and normalized VLM bounding boxes are reconciled via a centralized DPI-aware transform.

---

## 2. Phase-by-Phase Remediation Roadmap

### Phase 1: Core Contracts & Type Normalization
- **Objective**: Standardize `ToolResult`, `Observation`, and `TaskExecutionDiagnostic` across all modules.
- **Files**: `core/errors.py`, `tools/tool_runtime.py`, `router/diagnostics.py`.
- **Target Invariant**: Zero untyped error strings; structured diagnostic envelopes for all failures.

### Phase 2: Runtime State Machine & Execution Truth
- **Objective**: Prevent illegal state jumps (`EXECUTED -> COMPLETED` without `VERIFIED`).
- **Files**: `agent/task_state.py`, `agent/executor.py`, `agent/verifier.py`.
- **Target Invariant**: Explicit separation of `EXECUTED`, `OBSERVED`, and `VERIFIED`.

### Phase 3: Model Gateway & Resilience
- **Objective**: Dynamic mid-flight fallback re-routing on 429 / 401 / Timeout.
- **Files**: `gateway/model_gateway.py`, `router/smart_router.py`, `gateway/health.py`.
- **Target Invariant**: Cloud quota failure automatically escalates to secondary cloud or local Ollama.

### Phase 4: Tool Integration & Argument Normalization
- **Objective**: Centralized argument normalizer for paths, URLs, app names, booleans.
- **Files**: `tools/tool_runtime.py`, `tools/registry.py`.
- **Target Invariant**: Arguments normalized before policy evaluation and execution.

### Phase 5: Observation & Physical Verification Engine
- **Objective**: Universal post-condition verifiers for all file, process, DOM, and system setting mutations.
- **Files**: `agent/verifier.py`, `tools/sandbox_process.py`, `tools/export_tools.py`.
- **Target Invariant**: Physical file/process check required before reporting goal completion.

### Phase 6: Memory & Context Synchronization
- **Objective**: Hybrid search (Vector + BM25 + Recency) injected into system prompt context with privacy boundaries.
- **Files**: `memory/unified_memory.py`, `memory/canonical_db.py`, `memory/sqlite_lock.py`.
- **Target Invariant**: Zero database lock errors; verified memories retrieved in < 15ms.

### Phase 7: Voice Pipeline & Acoustic Barge-In
- **Objective**: Sub-300ms latency loop with acoustic echo suppression and instant barge-in interrupt.
- **Files**: `voice/assistant.py`, `voice/tts_queue.py`, `voice/silero_vad.py`.
- **Target Invariant**: TTS audio muted in < 15ms upon user speech detection.

### Phase 8: Vision Perception & DPI Coordinate Mapping
- **Objective**: DPI-aware coordinate mapping matrix for Windows 125%/150% desktop scaling.
- **Files**: `vision/engine.py`, `computer/operator.py`, `computer/semantic_operator.py`.
- **Target Invariant**: Click coordinates match physical button center across all monitor DPI scales.

### Phase 9: Browser & Visible Web Automation
- **Objective**: Distinguish background `web_search` / `web_extractor` from visible Playwright browser actions.
- **Files**: `tools/browser_automation.py`, `actions/browser_control.py`.
- **Target Invariant**: Visible browser tasks assert window focus, page load, and DOM element presence.

### Phase 10: Artifact Sandbox & Host Export Pipeline
- **Objective**: Guarantee 100% of user-facing artifacts are exported and verified on host before browser launch.
- **Files**: `agent/artifacts.py`, `tools/export_tools.py`.
- **Target Invariant**: Browser never receives unverified sandbox path (`ERR_FILE_NOT_FOUND` permanently prevented).

### Phase 11: Workflow & DAG Task Decomposition
- **Objective**: Compound multi-intent user requests decomposed into topological DAG stages.
- **Files**: `workflow/task_dag.py`, `agent/stage_decomposer.py`, `agent/task_scheduler.py`.
- **Target Invariant**: Compound queries ("do X, then Y, then Z") executed in verified dependency order.

### Phase 12: Security & Path Confinement
- **Objective**: 6-Tuple deterministic policy engine with critical OS denylist.
- **Files**: `security/policy_engine.py`, `security/path_policy.py`, `guardian/prompt_injection_shield.py`.
- **Target Invariant**: External web/PDF/email text quarantined; model cannot self-authorize.

### Phase 13: Observability & Distributed Tracing
- **Objective**: Every task tagged with `trace_id`, `task_id`, `stage`, `provider`, `latency`, `verification`.
- **Files**: `core/logging.py`, `router/diagnostics.py`, `events/bus.py`.
- **Target Invariant**: 100% reconstructible execution trace from logs.

### Phase 14: UI & Event Dispatch Bridge
- **Objective**: Non-blocking Qt Signal/Slot bridge for all background worker threads.
- **Files**: `ui/main_window.py`, `ui/widgets.py`, `float_widget.py`.
- **Target Invariant**: Zero UI freezing during heavy background tool execution.

### Phase 15: Performance & Cache Governance
- **Objective**: Bounded memory footprint, TTL cache eviction, connection pooling.
- **Files**: `core/process.py`, `memory/unified_memory.py`.
- **Target Invariant**: Zero memory leaks across 1,000 continuous event cycles.

### Phase 16: Automated Verification Pyramid
- **Objective**: Assert physical post-conditions across unit, integration, security, and E2E suites.
- **Files**: `tests/unit/*`, `tests/e2e/*`, `tests/adversarial/*`.
- **Target Invariant**: 100% pass across all 473+ test cases.

### Phase 17: End-to-End Master Task Certification
- **Objective**: Full autonomous execution of compound multi-modal audit task.
- **Files**: `scripts/smoke_startup.py`, `scripts/test_toughest_tasks.py`.
- **Target Invariant**: Complete system certified production ready.
