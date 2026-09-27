# REPOSITORY INVENTORY & CLASSIFICATION MATRIX: BR JARVIS MK40.2+

## Overview
This document contains the complete, authoritative inventory and classification of all directories, source packages, applications, configuration files, test suites, scripts, assets, and runtime directories across the reorganized BR JARVIS repository.

---

## Classification Taxonomy
- **SOURCE**: Core system engine, domain models, algorithms, and application logic.
- **APPS**: Application entry points, launchers, and user interface runners.
- **CONFIG**: Configuration settings, schemas, model routing declarations, and environment templates.
- **TEST**: Automated unit, integration, end-to-end, adversarial, and reliability test suites.
- **DOCUMENTATION**: Architectural blueprints, operational walkthroughs, threat models, and audit records.
- **SCRIPT**: Development tools, build scripts, migration engines, and diagnostic utilities.
- **ASSET**: Templates, static UI web assets, icons, and document schemas.
- **RUNTIME_DATA**: Ephemeral execution logs, captures, generated reports, databases, and temporary state.
- **USER_DATA**: User workspaces, career applications, custom resumes, and projects.
- **NATIVE**: C/C++ low-latency libraries and shared object bindings.

---

## Complete Top-Level Inventory & Location Matrix

| Entity Name | Classification | Target Location | Description & Ownership |
|---|---|---|---|
| `src/brjarvis/core` | SOURCE | `src/brjarvis/core/` | System kernel, DI container, event bus, config, lifecycle, paths |
| `src/brjarvis/career` | SOURCE | `src/brjarvis/career/` | Career OS (CRM, Resume Engine, ATS Scorer, Job Matcher, Cover Letter) |
| `src/brjarvis/agent` | SOURCE | `src/brjarvis/agent/` | Autonomous agent loop, planner, executor, artifacts manager, verifier |
| `src/brjarvis/memory` | SOURCE | `src/brjarvis/memory/` | Episodic, semantic, vector, working memory, lessons database |
| `src/brjarvis/tools` | SOURCE | `src/brjarvis/tools/` | Agent-callable tool registry, validation schemas, tool runtime |
| `src/brjarvis/actions` | SOURCE | `src/brjarvis/actions/` | Reusable system actions, OS automation, longform document builder |
| `src/brjarvis/connectors` | SOURCE | `src/brjarvis/connectors/` | External service connectors (Gmail, Outlook, Calendar, GitHub, Canva) |
| `src/brjarvis/voice` | SOURCE | `src/brjarvis/voice/` | Wake word detection, STT (Whisper), TTS (Neural), VAD, audio stream |
| `src/brjarvis/vision` | SOURCE | `src/brjarvis/vision/` | OCR screen analyzer, UI element locator, accessibility tree, vision engine |
| `src/brjarvis/ui` | SOURCE | `src/brjarvis/ui/` | Desktop PySide6 UI widgets, floating HUD backend, canvas renderers |
| `src/brjarvis/desktop` | SOURCE | `src/brjarvis/desktop/` | Cyberpunk HUD interface, floating HUD widget implementations |
| `src/brjarvis/skills` | SOURCE | `src/brjarvis/skills/` | Skill execution engine, skill library, Claude/Antigravity skill manifests |
| `src/brjarvis/orchestrator` | SOURCE | `src/brjarvis/orchestrator/` | Master JARVIS orchestrator, multi-agent coordinator |
| `src/brjarvis/router` | SOURCE | `src/brjarvis/router/` | Intent router, model capability router, complexity dispatcher |
| `src/brjarvis/gateway` | SOURCE | `src/brjarvis/gateway/` | LLM Gateway proxy, load balancer, circuit breaker |
| `src/brjarvis/guardian` | SOURCE | `src/brjarvis/guardian/` | Security guardian, file integrity hashes, redteam testing |
| `src/brjarvis/security` | SOURCE | `src/brjarvis/security/` | Deterministic 6-tuple policy engine, sandbox permissions |
| `src/brjarvis/workflow` | SOURCE | `src/brjarvis/workflow/` | Directed Acyclic Graph (DAG) parallel workflow engine |
| `src/brjarvis/integrations` | SOURCE | `src/brjarvis/integrations/` | Multi-LLM provider backends (Gemini, Claude, GPT, Ollama) and mobile bridge |
| `src/brjarvis/native` | NATIVE | `src/brjarvis/native/` | C/C++ native source and low-latency shared libraries |
| `src/brjarvis/diagnostics` | SOURCE | `src/brjarvis/diagnostics/` | Doctor engine, self-healing repairs, system health checks |
| `src/brjarvis/apps` | APPS | `src/brjarvis/apps/` | Canonical application bootstrap, CLI, Web, Desktop, Voice controllers |
| `apps/cli` | APPS | `apps/cli/` | Command line application runner |
| `apps/web` | APPS | `apps/web/` | FastAPI Web server runner & API gateway |
| `apps/desktop` | APPS | `apps/desktop/` | PySide6 Desktop HUD runner |
| `apps/voice` | APPS | `apps/voice/` | Hands-free Voice assistant runner |
| `tests/unit` | TEST | `tests/unit/` | Fast unit test suite covering all modules |
| `tests/integration` | TEST | `tests/integration/` | Cross-module integration test suite |
| `tests/e2e` | TEST | `tests/e2e/` | Real-world end-to-end user scenario tests |
| `tests/adversarial` | TEST | `tests/adversarial/` | Security redteaming & prompt injection tests |
| `tests/reliability` | TEST | `tests/reliability/` | Long-running soak, chaos, and resilience tests |
| `tests/benchmarks` | TEST | `tests/benchmarks/` | Latency and throughput benchmark suite |
| `config/default` | CONFIG | `config/default/` | Default models, keymaps, vocabulary, and MCP server configs |
| `config/schemas` | CONFIG | `config/schemas/` | Pydantic and JSON validation schemas |
| `config/examples` | CONFIG | `config/examples/` | `.env.template` and example configurations |
| `scripts/development` | SCRIPT | `scripts/development/` | Developer setup scripts, simulated voice environment |
| `scripts/build` | SCRIPT | `scripts/build/` | Native C compiler builders and packaging scripts |
| `scripts/migration` | SCRIPT | `scripts/migration/` | Filesystem reorganization and database migration tools |
| `scripts/diagnostics` | SCRIPT | `scripts/diagnostics/` | System smoke tests, model probes, hardware diagnostic tools |
| `scripts/release` | SCRIPT | `scripts/release/` | Versioning and release manifest utilities |
| `assets/templates` | ASSET | `assets/templates/` | Native resume templates, cover letters, HTML/DOCX renderers |
| `assets/static` | ASSET | `assets/static/` | Web dashboard static frontend assets |
| `runtime/logs` | RUNTIME_DATA | `runtime/logs/` | System application logs, audit logs, voice logs |
| `runtime/captures` | RUNTIME_DATA | `runtime/captures/` | Screen captures, OCR crops, vision screenshots |
| `runtime/reports` | RUNTIME_DATA | `runtime/reports/` | Test execution reports, diagnostic output dumps |
| `runtime/temporary` | RUNTIME_DATA | `runtime/temporary/` | Scratchpad files and temporary operational files |
| `runtime/state` | RUNTIME_DATA | `runtime/state/` | Local SQLite databases, PID files, vector indexes |
| `runtime/artifacts` | RUNTIME_DATA | `runtime/artifacts/` | Generated deliverables (PDFs, DOCX resumes, exports) |
| `workspace/documents` | USER_DATA | `workspace/documents/` | User documents and text files |
| `workspace/resumes` | USER_DATA | `workspace/resumes/` | Tailored resumes and candidate assets |
| `workspace/career` | USER_DATA | `workspace/career/` | Career tracker workbooks and application logs |
| `workspace/projects` | USER_DATA | `workspace/projects/` | User code repositories and workspaces |
| `workspace/user-data` | USER_DATA | `workspace/user-data/` | User profiles and local cache data |
