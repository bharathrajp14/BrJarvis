# BRJARVIS // SYSTEM EVOLUTION & UPGRADE ROADMAP
**Document Version:** 1.0.0  
**Audit Date:** 2026-09-27  
**Execution Strategy:** Incremental Strangler Migration with Rigorous Test Gates  

---

## 1. Principles of Evolution

1. **Maintain Working Functionality:** Never break the active 200 tools, FastAPI endpoints, or React control plane.
2. **Compatibility Adapters Over Blind Rewrites:** Evolve canonical abstractions and bridge legacy components into them.
3. **No Phantom Progress:** A feature is done only when verified by executable unit/integration tests and observable in runtime telemetry.
4. **Maximal Useful Intelligence Per Unit of Complexity:** Eliminate duplicated systems and prefer coherent, observable patterns.

---

## 2. Priority Phasing

### Phase 1: Full Repository Audit & Ground Truth Baseline (COMPLETED)
- [x] Complete inventory of production code (1,204 files, 293k LOC across `brjarvis` and `jarvis`).
- [x] Full test suite audit (89 test files, 402 passing automated tests).
- [x] Produce `CURRENT_SYSTEM_MAP.md`.
- [x] Produce `ARCHITECTURE_GAPS.md`.
- [x] Produce `AUTONOMY_GAP_ANALYSIS.md`.
- [x] Produce `UPGRADE_ROADMAP.md`.

---

### Phase 2: Core Runtime Convergence & Task Durability (P0)
**Focus:** Eliminating in-memory fragility and unifying task execution contracts.
- **Slice 2.1: Canonical Tool Adapter & Runtime Bridge**
  - Bridge the 200 operational tools from `brjarvis.tools.registry` into `jarvis.tools.registry.ToolRegistry`.
  - Wrap legacy tool handlers with `ToolContract` and `ToolResult` contracts, enforcing risk classification (`READ_ONLY`, `LOW_RISK_WRITE`, `HIGH_RISK_WRITE`, `SYSTEM_CONTROL`).
- **Slice 2.2: Durable Task Persistence & State Machine Enforcement**
  - Connect `TaskRepository` (`src/jarvis/memory/store.py`) to the FastAPI `/api/v1/tasks` endpoints.
  - Enforce the 14-state machine with optimistic concurrency revision checks.
  - Implement task resumption on process restart.
- **Slice 2.3: Canonical Agent Loop Unification**
  - Unify `brjarvis.agent.agent_loop` and `jarvis.agent.loop` into one robust ReAct engine.
  - Support multi-step execution, dynamic replanning on tool errors, and structured evidence accumulation in `ExecutionLedger`.
- **Slice 2.4: Comprehensive Doctor & Subsystem Health Diagnostics**
  - Expand `/health`, `/ready`, and `/api/v1/diagnostics` to return live, machine-readable status for all 10 subsystems (tools, database, gateway latency, memory, event bus).

---

### Phase 3: Layered Memory & Context Engineering (P1)
**Focus:** High-precision memory retrieval and token efficiency.
- **Slice 3.1: 7-Layer Memory Hierarchy**
  - Implement explicit repositories for Working, Episodic, Semantic, Preference, Project, Artifact, and Failure memories.
  - Structured memory schema: `id`, `type`, `content`, `source`, `confidence`, `created_at`, `updated_at`, `importance`, `scope`, `tags`, `provenance`.
- **Slice 3.2: Progressive Disclosure Context Engine**
  - Implement context ranking (`recency * relevance * importance`).
  - Summarize long historical tool observations rather than dumping raw logs into LLM prompts.

---

### Phase 4: Deterministic Computer & Browser Use (P1)
**Focus:** Eliminating fragile visual-only automation in favor of structured DOM and OS verification.
- **Slice 4.1: Structured Browser Automation**
  - Playwright-backed browser operator with DOM accessibility-tree extraction.
  - Verification contracts for every browser action (`navigate`, `click`, `fill`, `assert_state`).
- **Slice 4.2: Hardened Desktop Control**
  - Separate `OBSERVE`, `INTERACT`, and `SYSTEM_CHANGE` capabilities with permission gates.
  - Emit screenshot evidence and verified post-action states.

---

### Phase 5: Code Agent & Artifact Engine (P2)
**Focus:** Autonomous software engineering and high-fidelity artifact production.
- **Slice 5.1: High-Integrity Code Agent Pipeline**
  - Full coding workflow: `Understand Repo` -> `Plan` -> `Inspect` -> `Edit` -> `Test` -> `Static Checks` -> `Verify` -> `Diff` -> `Report`.
  - Regression-proof code patching with automated rollback on test failures.
- **Slice 5.2: Unified Artifact Engine**
  - First-class `Artifact` tracking (PDF, DOCX, XLSX, Markdown, Code Patches) with versioning, checksums, and previews.

---

### Phase 6: Controlled Self-Improvement & Benchmarking (P2)
**Focus:** Continuous system self-tuning within strict safety boundaries.
- **Slice 6.1: Evolution Pipeline**
  - `Observe` -> `Identify Weakness` -> `Form Hypothesis` -> `Design Patch` -> `Run Regression Suite` -> `Compare Against Baseline` -> `Human Approval Gate` -> `Apply Checkpoint` -> `Auto-Rollback on Regression`.
- **Slice 6.2: Automated Evaluation Framework**
  - Measurable benchmark suite measuring task success, latency, token usage, and tool accuracy.

---

### Phase 7: UI, Voice & Performance Polish (P3)
- **Slice 7.1: Frontend OS Experience Polish**
  - Live timeline view for durable tasks, approval dialogs, and artifact previews.
- **Slice 7.2: Unified Voice Engine**
  - Stream voice interactions through the same canonical `AgentLoop` and memory store.
- **Slice 7.3: Performance Optimization**
  - Async connection pooling, bounded concurrency, and context caching.

---

## 3. Slice Execution Verification Gate

Every implementation slice must satisfy the 10-step verification gate before landing:
1. Import / compile clean check across both Python interpreters.
2. Focused unit tests written/extended.
3. Related integration tests executed.
4. Full regression test suite (`pytest`) must pass.
5. Static analysis and linting (`ruff`).
6. Security checks (no secrets, path safety, permissions).
7. Frontend build verification (`npm run build`).
8. Performance / latency checks.
9. Git diff review.
10. Documentation synchronized.
