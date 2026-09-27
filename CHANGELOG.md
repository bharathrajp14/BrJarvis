# Changelog

All notable BR-JARVIS changes are documented here.

## [42.0.0-canonical-two-layer-memory] - 2026-09-27

### Architecture & Memory (Decision D7)

- **Two-Layer Canonical Memory Architecture**:
  - Implemented `ExplicitFactStore` (`src/jarvis/memory/facts.py`) providing discrete, user-visible, editable, and taggable facts categorized into `identity`, `preference`, `project`, `constraint`, `workflow`, and `custom`.
  - Implemented `SessionSummarizer` (`src/jarvis/memory/summarizer.py`) performing asynchronous post-session synthesis over transcripts to extract durable facts and generate structured recaps.
  - Implemented `MemoryRetriever` (`src/jarvis/memory/retrieval.py`) enforcing token-budgeted, gated context retrieval with identity anchors to eliminate model "context rot".
  - Implemented `UnifiedMemory` (`src/jarvis/memory/unified.py`) facade consolidating explicit facts, session summaries, task repositories, and temporal facts into a single SQLite WAL store.
  - Wired `UnifiedMemory` into `AssistantRuntime` composition root (`src/jarvis/core/bootstrap.py`) and DI container.

### Cross-Surface Recall & Presentation Interop

- **One Store, Every Surface**:
  - Connected Web API endpoints (`/api/memory`) to canonical `UnifiedMemory` so memory writes and reads immediately synchronize across Web, CLI, Voice, and Career OS.
  - Added end-to-end cross-surface memory recall integration tests (`tests/integration/test_cross_surface_memory_recall.py`) proving real-time shared recall and post-session synthesis.
  - Added consent and privacy controls: toggle enable/disable, explicit deletion, and zero-trace GDPR privacy purge (`clear()`).

### Security & Packaging Cleanup (Known Structural Problem #5)

- Removed user documents, resume drafts, and profile data mistakenly tracked inside the import path (`src/brjarvis/workspace/`). Relocated all assets to root `workspace/` and ignored `src/brjarvis/workspace/` in `.gitignore`.
- All memory modules strictly adhere to Decision D6 invariants (< 600 LOC per module, single DB connection manager).
- Verification: 426 unit & integration tests passing cleanly.

## [41.0.4-runtime-and-control-plane-fixes] - 2026-09-02

### Correctness

- Stopped the voice package from importing the Qt desktop HUD at import time, so transcript refinement and CI collection no longer crash without PySide6.
- Made headless Qt stubs real classes so UI widgets can be imported without `TypeError: __mro_entries__ must return a tuple`.
- Skipped Qt widget tests when PySide6 is not installed.
- Preserved the active control-plane view and selected task across snapshot hydration so live events no longer kick the operator back to Command Center.
- Allowed same-origin WebSocket connections on non-default ports and preview hosts instead of hard-coding ports 8000/3000.
- Stopped the browser WebSocket client from reconnecting after an intentional disconnect, and bounded the event-id cache.
- Cleared login throttling after a successful sign-in and serialized desktop handoff token storage.
- Stopped health endpoints from returning fabricated CPU/memory/disk percentages when live metrics are unavailable.
- Kept installed-wheel runtime data out of `site-packages` by resolving a writable data root when the checkout is not present.

### Control plane

- Added session logout from the control-plane user card.
- Gave Memory save and Career resume actions explicit submit/click handlers.

## [41.0.3-doctor-and-requirements] - 2026-08-19

### Diagnostics and dependency safety

- Added vault-safe provider credential diagnostics that report only configured status and non-secret source labels; raw API keys are never included in Doctor reports.
- Added core-versus-optional dependency summaries, Python runtime metadata, and repair-attempt tracking to the typed Doctor report.
- Improved module version detection through installed distribution metadata and corrected the DuckDuckGo dependency/import mapping to `ddgs`.
- Added `python-multipart` to the runtime requirements and expanded system capability checks to distinguish executable tools from Python-module fallbacks.
- Updated the overall health message to identify missing core Python dependencies without masking optional capability gaps.

### Packaging and verification

- Added bounded major-version constraints to the authoritative runtime dependencies in `pyproject.toml` and bumped package metadata to **41.0.3**.
- Updated Doctor contract coverage for the new report fields and health status.
- Verification: **309 passed, 1 skipped, and 2 benchmark tests deselected**; `pip check` and correctness-focused Ruff checks pass; the wheel builds successfully with no isolation.

## [41.0.1-reliability-and-boundary-upgrade] - 2026-08-19

### Security and runtime correctness

- Contained artifact download and preview paths to approved runtime/workspace roots and stopped returning absolute host or sandbox paths in artifact metadata.
- Removed browser-visible session bearer tokens from the login JSON response while preserving HttpOnly cookie authentication.
- Routed Gemini, OpenAI, and Tavily credential lookup through the OS-backed credential vault; legacy configuration metadata no longer returns raw provider secrets.
- Enforced configured timeouts for synchronous tool handlers and repaired the sandbox code-preparation path without introducing an unisolated fallback.
- Repaired undefined-name failures across web search, memory, Career OS, agent recovery, executor, system tools, and UI paths.
- Fixed duplicate `/resume` terminal command registration so task resume and Career resume generation remain distinct.

### Maintainability and compatibility

- Applied deterministic Ruff safe fixes and formatting across the maintained source and test tree.
- Made stage-decomposer generated-file links compatible with Python 3.11.
- Forwarded explicit `start.py web --host/--port` values to the canonical web launcher.
- Added regression coverage for artifact containment, session privacy, sandbox execution, synchronous timeouts, legacy credential behavior, type-hint evaluation, and search fallback behavior.

### Verification

- Full maintained result: **305 passed, 1 skipped, and 2 benchmark tests deselected**.
- Whole-tree compilation and correctness-focused Ruff checks pass.
- Broad Ruff debt reduced by safe fixes and formatting; residual findings are primarily import-star typing, import placement, unused variables/imports, and ambiguous names.
- Package-wide Pyright remains a follow-up modernization effort with 558 errors and 31 warnings.

## [41.0.2-scoped-launcher-actions-tools-memory] - 2026-08-19

### Scoped follow-up

- Added a shared actions credential adapter and removed remaining direct Gemini-key reads from action configuration JSON.
- Closed the `/tmp/../` temporary-root bypass in `FileManager` and replaced private `tempfile._time` usage with the public time API.
- Added strict-mode persistence errors for vector/SQLite memory synchronization while preserving backward-compatible non-strict saves.
- Added regressions for temporary-root traversal, strict memory failures, secure action credentials, and launcher forwarding.
- Scoped import smoke passed for 161 actions/tools/memory modules; the full maintained suite now reports 305 passed.

## [41.0.0-production-hardening] - 2026-08-19

### Security

- Made REST and WebSocket authentication fail closed with one canonical, strong `JARVIS_SERVER_API_KEY`.
- Removed loopback authentication bypasses and long-lived WebSocket query keys.
- Replaced browser API-key persistence with HttpOnly sessions and one-time WebSocket tickets.
- Added WebSocket origin validation and strict session-cookie defaults.
- Fixed Career and static-file path traversal and arbitrary existing-file disclosure.
- Changed permission defaults from unrestricted execution to destructive-action confirmation.
- Made incomplete mutating-tool metadata derive high risk, local-system permission, and approval requirements.
- Disabled unisolated host code execution and in-process community plugins by default.
- Replaced plaintext credential values with OS-keyring-backed opaque references and atomic metadata writes.
- Removed a tracked nested API-key file, expanded secret ignore rules, and added a secret baseline gate.
- Removed vulnerable ChromaDB from default dependencies, upgraded `cryptography`, and moved AGPL-risk PyMuPDF behind an explicit extra.

### Runtime

- Added typed agent outcomes for verified success, partial execution, failure, cancellation, and timeout.
- Added task deadlines, cooperative cancellation acknowledgement, and bounded graceful queue shutdown.
- Added bounded in-memory event retention, asynchronous JSONL persistence, file rotation, and shutdown flushing.
- Ensured synchronous event publication delivers asynchronous subscribers when no event loop is active.
- Added deterministic web-lifespan cleanup for task queue, event store, logging, and orchestrator.

### Packaging and delivery

- Moved FastAPI to `brjarvis.web.api` and PWA resources to `brjarvis.web.static`.
- Added packaged PWA and skill resources; retained a deprecated `apps.web.api` compatibility adapter.
- Consolidated metadata in `pyproject.toml`; reduced `setup.py` to a legacy shim.
- Added platform markers, missing `python-multipart`, OS keyring, and patched cryptography dependencies.
- Replaced unsafe setup fallbacks with project-local virtual-environment installers.
- Quarantined the root `brjarvis.py` launcher to prevent package shadowing.
- Replaced the unreachable CI chain with independent quality, test, package, architecture, security, secret, dependency, and license gates.

### Product contracts

- Aligned Career dashboard job search, resume generation, ATS scoring, and spreadsheet synchronization with canonical OpenAPI routes and payloads.
- Added an executable dashboard/OpenAPI contract test.

### Verification

- Final regression result for the production-hardening baseline: **295 passed, 1 skipped, 2 benchmark tests deselected**.

- Incremental Ruff gate passes.
- Hardened Pyright scope reports zero errors.
- Import Linter keeps the security/presentation boundary.
- Bandit hardened-surface scan passes.
- `pip-audit` reports no known vulnerabilities.
- License policy passes for the installed environment.
- Final wheel installs outside the checkout, builds 51 routes, finds packaged PWA assets, and passes dependency integrity.

### Breaking and operational changes

- A unique `JARVIS_SERVER_API_KEY` of at least 24 characters is mandatory for the web control plane.
- Code execution requires explicit `JARVIS_ENABLE_UNSAFE_HOST_EXECUTION=true`; this is not recommended for production.
- Community plugins require explicit `JARVIS_ENABLE_UNTRUSTED_PLUGINS=true`; only trusted code should be enabled.
- `apps.web.api` is deprecated; import `brjarvis.web.api`.
- ChromaDB is not installed by the default memory extra pending an upstream security fix.
- PyMuPDF requires the explicit `pdf-rendering` extra and a separate license review.
- Any real credential previously committed must be rotated outside the repository before production release.
