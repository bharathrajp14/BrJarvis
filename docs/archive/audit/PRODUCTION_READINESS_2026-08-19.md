# BR-JARVIS Production-Readiness Audit and Upgrade Record

**Assessment date:** 19 August 2026  
**Upgrade branch:** `upgrade/production-hardening-20260819`  
**Product version assessed:** 41.0.0  
**Assessment type:** Full repository static review, focused adversarial verification, packaging validation, and production hardening

## Executive assessment

BR-JARVIS is a substantial local agent platform rather than a prototype. Its maintained tracked tree contains **632 Python files**, including **517 package source files with 117,211 lines** and **71 test files with 5,763 lines**. Import Linter analyzed **519 package modules and 1,371 internal dependencies**. The platform contains real implementations for orchestration, memory, tools, permissions, web and desktop surfaces, Career OS, connectors, eventing, recovery, and artifact verification.

The corrected pre-upgrade assessment was **49/100 and not release-ready**. That result superseded an earlier false conclusion caused by an incomplete review snapshot: the canonical `src/brjarvis/memory` package exists, is substantive, imports correctly, and is included in built artifacts. The production upgrade addressed the seven highest release blockers: web authentication, arbitrary file download, permissive authorization defaults, unsafe code and plugin execution, plaintext credential persistence, broken installed-wheel web startup, and unreachable CI tests.

The current implementation is materially safer and more reproducible. The final maintained test suite reports **295 passed, 1 skipped, and 2 benchmark tests deselected**. The incremental Ruff gate is clean, the hardened Pyright scope reports no errors, the architecture contract is kept, Bandit reports no medium-or-higher findings in the hardened security surface, `pip-audit` reports no known vulnerabilities after dependency remediation, and the license policy no longer includes the non-default AGPL PDF backend. Final wheel and source distributions were built in a secret-free isolated context; the wheel installed into an empty external virtual environment, constructed **51 routes**, found its packaged PWA, passed `pip check`, and confirmed that no source-checkout path was used.

> **Release status:** **Conditional release candidate.** Code-level and distribution P0 blockers are corrected, but production release remains blocked until any provider credential formerly stored in the tracked `apps/web/config/api_keys.json` is rotated. Repository-wide legacy Ruff debt remains a P1 modernization program; it is isolated from the new independently runnable CI gates rather than hidden.

## Evidence and method

The audit combined repository inventory, AST/import analysis, direct source inspection, focused and full pytest execution, Ruff and Pyright checks, Bandit, `detect-secrets`, `pip-audit`, license inventory, Import Linter, wheel inspection, and clean-environment installation attempts. Sensitive file contents were not reproduced in this report. Recovery artifacts were created outside the repository before modification, including Git state, diffs, a repository bundle, untracked-file preservation, environment versions, and baseline command outputs.

The architecture report treats generated `build/`, cache, runtime database, logs, browser profiles, and user workspace content as non-source. Earlier raw inventory figures that counted duplicated build output are not used for maintained-source sizing.

## Post-upgrade scorecard

| Area | Corrected baseline | Current assessment | Rationale |
|---|---:|---:|---|
| Architecture and boundaries | 55 | **64** | The web control plane and PWA are now installable package resources; the root package-shadowing launcher is quarantined; one security-layer import contract is executable. Cycles, large modules, and fragmented composition remain. |
| Security, permissions, and privacy | 31 | **76** | REST and WebSocket auth fail closed; loopback bypasses are removed; downloads are contained; unsafe execution/plugins default off; credentials use OS keyring; dependency and secret gates exist. Historical credential rotation remains external work. |
| Runtime reliability and performance | 46 | **70** | Agent turns expose typed terminal outcomes; task deadlines and acknowledged cancellation are enforced; shutdown is bounded; event history and persistence are bounded and asynchronous. Some legacy executors and dual-write paths remain. |
| Product surfaces and contracts | 64 | **72** | Career dashboard routes and payloads match OpenAPI; PWA uses cookie sessions and one-time WebSocket tickets; packaged assets are canonical. Desktop/mobile/Telegram parity remains incomplete. |
| Packaging, testing, and delivery | 49 | **72** | Packaging metadata is consolidated, platform markers are corrected, skills/web resources enter the wheel, setup scripts are isolated, and CI jobs are independent. Repository-wide lint debt is still large. |
| **Overall** | **49** | **71** | **Release-candidate quality after credential rotation and final artifact verification.** |

## Implemented P0 corrections

| Former blocker | Implemented correction | Verification |
|---|---|---|
| Web authentication failed open and used inconsistent key names | `JARVIS_SERVER_API_KEY` is canonical, must be unique and at least 24 characters, placeholder values are rejected, and application creation fails closed without a key. Loopback exemptions were removed. | REST integration tests prove unauthenticated API calls return 401 and login creates an HttpOnly session. |
| WebSockets accepted loopback/direct long-lived query keys | WebSockets require an authenticated cookie or short-lived one-time ticket. Direct API-key query parameters were removed and browser origins are validated. | Integration tests prove unauthenticated rejection, successful ticket use, and ticket replay rejection. |
| PWA persisted the API key in browser storage | The dashboard exchanges the key for an HttpOnly `SameSite=Strict` session, clears legacy browser key entries, and requests one-time WebSocket tickets. | Static contract tests and authenticated route tests cover the flow. |
| Career download served arbitrary existing host files | The endpoint resolves the path, requires `relative_to(workspace_root)`, and requires a regular file. Root static serving applies equivalent containment. | Adversarial tests cover existing outside files and encoded parent traversal. |
| Tool policy defaulted to `ALLOW_ALL` | Invalid or absent modes resolve to `CONFIRM_DESTRUCTIVE`. Incomplete mutating-tool metadata derives high risk, `LOCAL_SYSTEM`, and approval required; explicit read-only tools derive low-risk public-read metadata. | Permission and canonical runtime tests cover default and invalid-mode behavior. |
| Host subprocesses were presented as isolated sandboxing | Code execution is disabled unless `JARVIS_ENABLE_UNSAFE_HOST_EXECUTION=true` is explicitly set. Failure of an isolation runtime no longer falls back to an unisolated subprocess. Community plugins are disabled unless explicitly trusted. | Sandbox tests prove code does not execute under default configuration. |
| Secrets were written to JSON | `CredentialVault` now stores values through an OS keyring adapter. JSON contains metadata only and is written atomically with restrictive POSIX permissions where supported. Legacy plaintext vault entries migrate only when a secure backend is available. | Tests prove secret values never enter JSON and legacy migration sanitizes metadata. Local sensitive files received restrictive Windows ACLs. |
| Installed `jarvis-server` depended on repository-root `apps.web.api` | The API moved to `brjarvis.web.api`; the PWA moved to `brjarvis.web.static`; skills and web assets are package data; a thin deprecated `apps.web.api` adapter remains for source compatibility. | Wheel inspection found the API server, `index.html`, and hundreds of skill resource entries. |
| CI tests depended on a red lint job | Quality, tests, packaging, and security are independent jobs. The matrix covers Linux 3.11–3.13 plus Windows and macOS 3.12. | The exact incremental Ruff gate passes locally. Import Linter keeps the security boundary. |

## Security model after upgrade

The web control plane uses a bootstrap secret only to establish a server-side session. The browser stores no long-lived API secret. REST requests use an HttpOnly cookie; WebSocket clients first obtain a short-lived one-time ticket over an authenticated REST session. Cross-origin WebSocket handshakes are rejected unless configured in `JARVIS_CORS_ORIGINS`. Deployments behind TLS must set `JARVIS_COOKIE_SECURE=true`.

The action model is now fail-safe by default. Read-only tools may be declared `PUBLIC_READ`; mutating tools without complete metadata are treated as high-risk local-system actions requiring approval. `ALLOW_ALL` remains an explicit operator override rather than an implicit fallback. Code execution and in-process community plugins remain off unless the operator knowingly enables unsafe compatibility modes.

Credential values are owned by the operating-system credential store. Environment variables remain an explicit runtime fallback, but secret material is not serialized into the credential metadata file. The tracked historical key file was removed and wildcard ignore rules now cover nested credential files.

> **Mandatory external action:** rotate any provider key, OAuth client secret, or token that ever appeared in `apps/web/config/api_keys.json` or another committed file. Deleting a working-tree file does not remove secrets from Git history, forks, backups, or caches.

## Runtime reliability model

Agent execution now retains an `AgentTurnResult` with one of `success_verified`, `partial`, `failed`, `cancelled`, or `timed_out`. The legacy text-returning method remains compatible, while callers that require orchestration truth can use `run_turn_result`. Backend failures emit `agent.failed`; verification or permission failures yield `agent.partial`; only verified turns emit successful completion.

Task cancellation is cooperative and acknowledged. Pending tasks terminate immediately. Running tasks transition to `cancelling` and become `cancelled` only when the worker returns. Deadlines set a cancellation token and become `timed_out` after worker acknowledgement. Queue shutdown requests cancellation, wakes workers, and joins for a bounded grace period.

The event store retains a bounded in-memory deque, writes through a bounded queue on a dedicated writer thread, rotates JSONL logs, exposes dropped-write counts, and supports bounded shutdown. Synchronous event publication no longer silently skips asynchronous subscribers when no loop exists.

## Packaging and dependency decisions

`pyproject.toml` is the authoritative metadata source. `setup.py` is only a legacy setuptools shim. Windows-only dependencies carry platform markers. Ruff is the formatter/linter and Pyright is the type checker. The setup scripts create `.venv`, install the project with dependency resolution, run `pip check`, and never retry with `--no-deps` or mutate system Python.

The optional ChromaDB backend was removed from the default dependency graph because the installed release had an unfixed 2026 advisory. Canonical SQLite memory remains available. `cryptography` was raised to the patched 50.x line. PyMuPDF was moved behind an explicit `pdf-rendering` extra because its AGPL/commercial dual licensing is unsuitable as an unreviewed default dependency. The default document stack retains `pypdf`, `fpdf2`, and the Office document libraries.

## Current architecture and ownership

| Layer | Canonical owner | Responsibilities | Remaining concern |
|---|---|---|---|
| Adapters | `brjarvis.apps`, `brjarvis.web`, `brjarvis.ui`, `brjarvis.desktop` | CLI, ASGI, PWA, desktop presentation | Several legacy launchers and UI-specific lifecycle paths remain. |
| Orchestration | `brjarvis.orchestrator`, `brjarvis.agent`, `brjarvis.workflow` | Planning, turns, tasks, approvals, recovery, DAG execution | Similar task/status models and multiple execution loops still overlap. |
| Tool platform | `brjarvis.tools`, `brjarvis.security` | Catalog, normalization, policy, approval, execution, verification | Metadata migration is secure-by-default but not yet fully explicit for every tool. |
| Domain capabilities | `brjarvis.career`, `brjarvis.memory`, `brjarvis.connectors`, `brjarvis.voice` | Product workflows and external capability adapters | Direct storage and presentation dependencies remain in some domains. |
| Infrastructure | `brjarvis.core`, `brjarvis.events`, canonical memory/database managers | Configuration, paths, DI, lifecycle, persistence, events | Persistence authority is still split across task, DAG, session, ledger, and domain stores. |

Import Linter now enforces that `brjarvis.security` cannot depend on desktop, UI, or web presentation modules. Additional contracts should be introduced only after current cycles are migrated; adding contracts that are already broken would create ceremonial CI rather than executable architecture.

## Persistence ownership map

| State | Present owner | Desired authority | Migration direction |
|---|---|---|---|
| Memory and workspace conversations | `CanonicalDatabaseManager`, `WorkspaceStore` | Canonical memory database | Retain; expose ports to domains rather than direct cross-layer imports. |
| Agent task state and approvals | `TaskStateManager` | Task aggregate repository | Migrate queue, approvals, and recovery through one injected unit of work. |
| Workflow DAG state | Workflow-specific SQLite | Task/workflow aggregate repository | Introduce schema migration and move DAG checkpoints behind the same persistence port. |
| Execution evidence | Execution ledger in canonical DB | Append-only evidence repository | Retain; link by task, step, correlation, and causation IDs. |
| Session state | Session store plus compatibility dual writes | Session repository with outbox | Remove suppressed dual writes after migration telemetry proves parity. |
| Career CRM | Career database and projections | Career aggregate repository | Keep domain ownership; spreadsheet remains a projection, never source of truth. |
| Events | Bounded memory plus rotating JSONL | Durable audit adapter | Current implementation is safe for local deployment; high-scale deployments should use a transactional outbox or external broker. |

## Startup and shutdown map

The canonical installed entry points are `jarvis`, `jarvis-cli`, and `jarvis-server`, all under `brjarvis.apps`. `start.py` remains a source-checkout compatibility dispatcher. The root `brjarvis.py` module was moved to `legacy/launchers/brjarvis.py` because it shadowed the real package and prevented architecture tooling from resolving `brjarvis` as a package.

For the web adapter, startup validates the server key, builds the assistant runtime, starts the task queue, runs crash recovery, and activates WebSocket logging. Shutdown deactivates logging, requests bounded queue cancellation, closes the event writer, and shuts down the orchestrator. The same lifecycle should become the shared composition root for CLI and desktop adapters in the next migration phase.

## Product contract corrections

The Career OS dashboard now uses `query` for job search and reads `matches`; resume generation calls `POST /api/career/resumes/create` with `template_id`; ATS scoring calls `POST /api/career/ats/score` and reads `overall_score`; spreadsheet synchronization uses the existing canonical endpoint. An integration test compares these dashboard strings with the generated OpenAPI paths to prevent silent client/server drift.

## Residual risks and prioritized backlog

| Priority | Residual risk | Required next action | Release effect |
|---:|---|---|---|
| P0 | Potential credential exposure in Git history | Rotate affected credentials, invalidate sessions, review provider audit logs, and optionally rewrite history with coordinated force-push procedures. | **Blocks production release.** |
| Completed | Final rebuilt artifact smoke test | Final wheel installed outside the checkout, built 51 routes, resolved packaged PWA assets, and passed dependency integrity. | Distribution blocker closed. |
| P1 | 2,907 repository-wide Ruff findings remain across legacy modules, including 37 undefined names and 2 syntax findings in the broad scope | Triage correctness classes first (`F821`, syntax, repeated keys), then migrate imports and whitespace in bounded subsystem PRs. | Does not block the hardened CI scope; blocks declaring the whole tree clean. |
| P1 | Composition and persistence are still fragmented | Introduce a typed application factory and storage ports; migrate one aggregate at a time with compatibility adapters and parity tests. | Reliability and maintainability risk. |
| P1 | Large modules and cyclic responsibilities | Split terminal commands, intent engine, main UI, document tools, orchestrator, and workflow orchestration by cohesive responsibility. | Change-risk and testability concern. |
| P1 | Some tools still rely on derived rather than explicit governance metadata | Generate a catalog audit and require explicit metadata for newly added or modified tools; backfill existing registrations by domain. | Security debt, currently fail-safe. |
| P2 | Desktop, mobile, Telegram, and web feature parity is incomplete | Publish a capability matrix and declare unsupported operations rather than exposing placeholder controls. | UX and supportability concern. |
| P2 | High-scale durability is not provided by rotating JSONL | Add a transactional outbox and external broker only when deployment topology requires it. | Not a local-single-user blocker. |

## File disposition and migration strategy

| Scope | Disposition | Reason |
|---|---|---|
| `src/brjarvis/memory` | Keep and consolidate consumers | It is the canonical substantive memory implementation; its earlier absence was a snapshot false positive. |
| `src/brjarvis/web/api`, `src/brjarvis/web/static` | Keep as canonical | Installable control plane and PWA resources. |
| `apps/web/api` | Compatibility adapter, then remove | Supports old imports without maintaining a second implementation. |
| `legacy/launchers` | Quarantine | Historical adapters must not shadow packages or define new architecture. |
| Root `start.py`, `server.py`, `main.py` | Deprecate gradually | Preserve operator workflows while console entry points become canonical. |
| `build/`, `dist/`, `*.egg-info`, caches | Delete after verification | Generated artifacts are never source of truth. |
| `src/brjarvis/workspace`, logs, databases, browser profiles | Relocate outside source and ignore | Runtime/user data must not be packaged or reviewed as source. |
| Duplicate task/status and persistence models | Migrate with adapters | Replace only after schema parity, checkpoint recovery, and rollback tests. |

## Verification record

| Gate | Result |
|---|---|
| Focused web/security/permission/sandbox/credential suite | **22 passed** before later broader regression runs. |
| Canonical agent outcome tests | **4 passed**; Ruff clean. |
| Task deadline/cancellation/shutdown tests | **4 passed**. |
| Event runtime tests | **3 passed**. |
| Canonical tool runtime and registry tests | **15 passed** after secure metadata migration. |
| Web package and legacy adapter tests | **16 passed**. |
| Incremental CI Ruff scope | **Pass**. |
| Hardened Pyright scope | **0 errors**. |
| Import Linter | **1 contract kept; 519 files and 1,371 dependencies analyzed**. |
| Bandit hardened surface | **Pass, no medium-or-higher findings**. |
| `pip-audit` after remediation | **No known vulnerabilities found**; local project correctly skipped as non-PyPI. |
| License policy after dependency isolation | **Pass for 214 installed distributions**; network-copyleft dependencies absent from default install. |
| Secret scan | Baseline generated after deleting tracked nested API-key file; remaining detections are retained for explicit audit rather than suppressed globally. |
| Final full pytest | **295 passed, 1 skipped, 2 benchmark tests deselected** in 86.81 seconds. |
| Wheel contents | Canonical API server, PWA `index.html`, and packaged skill resources present. |
| Clean wheel runtime | **Pass.** The first attempt correctly exposed missing `python-multipart`; after declaration, the final wheel installed externally, built 51 routes, loaded packaged PWA assets, passed `pip check`, and did not use the source checkout. |

## Release checklist

1. Rotate every credential that may have entered repository history and record provider-side completion.
2. Run Ruff, Pyright, Import Linter, Bandit, `pip-audit`, license policy, and secret-baseline verification exactly as CI defines them.
3. Confirm `.env` contains a unique server key, `JARVIS_COOKIE_SECURE=true` behind HTTPS, explicit CORS origins, `confirm_destructive`, and both unsafe execution/plugin flags set to false.
4. Create a signed/tagged release commit only after the working tree diff and generated artifacts are reviewed.

## Architecture decisions recorded

**ADR-001 — Canonical installable web namespace.** `brjarvis.web` owns API and PWA resources; repository-root web code is an adapter only.

**ADR-002 — Fail-closed local control plane.** Localhost is not an authentication boundary. All API and WebSocket control paths require credentials.

**ADR-003 — No unisolated code execution by default.** Temporary directories and process groups are not security sandboxes. Compatibility execution requires explicit unsafe opt-in.

**ADR-004 — OS-owned secrets.** The project stores opaque references and metadata; the operating system stores values.

**ADR-005 — Truthful terminal states.** Runtime completion status must distinguish verified success, partial execution, failure, cancellation, and timeout.

**ADR-006 — Independent CI evidence.** Lint, tests, packaging, and security report independently; one gate cannot hide the state of another.

**ADR-007 — Incremental quality migration.** New and hardened surfaces are clean and gated now; legacy debt is measured and retired by subsystem rather than reformatted blindly in one risk-heavy change.
