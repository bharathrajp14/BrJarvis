# BRJARVIS Repair and Release Evidence

**Date:** 23 August 2026  
**Repository:** `Br-Jarvis`  
**Release target:** `41.0.3`  
**Author:** Manus AI

## Executive result

The repository was analyzed from its attached Windows working tree, beginning with the project instructions, manifests, architecture documents, forensic debt inventory, frontend source, backend route composition, credential vault, and existing tests. The repair pass addressed the reproducible runtime/API failures, removed fabricated operational state from the rebuilt client, synchronized the release/version and packaged assets, and consolidated the most important duplicated route mounts.

The maintained regression suite now passes with **351 tests passed, 1 skipped, and 2 deselected**. The editable frontend passes TypeScript typechecking and a production Vite build, and the resulting bundle is copied into the server-served packaged static directory. The repository-wide critical Ruff classes for syntax and undefined names pass, and `pip-audit` reports no known vulnerabilities for the declared requirements.

## Completed repair areas

| Area | Completed change | Evidence |
|---|---|---|
| Connector security | Connector API keys are written to `CredentialVault`; connector metadata is stored separately; legacy `config/api_keys.json` secrets are migrated and scrubbed only after secure storage succeeds. | [`connectors.py`](../../src/brjarvis/web/api/routes/connectors.py), [`test_secure_credentials.py`](../../tests/unit/test_secure_credentials.py), connector integration regressions |
| API routing | Contacts, connectors, projects, tasks, artifacts, authentication, notifications, and conversations use relative route decorators composed under `/api` and `/api/v1`. The OpenAPI contract rejects doubled `/api/v1/api/...` paths. | [`server.py`](../../src/brjarvis/web/api/server.py), [`test_fastapi_web_routes.py`](../../tests/integration/test_fastapi_web_routes.py) |
| Contact imports | Contact creation returns a structured contact object; imports accept uploads, inline content, or workspace-contained file paths; arbitrary host paths are rejected. | [`memory.py`](../../src/brjarvis/web/api/routes/memory.py) |
| Upload safety | Project and generic file uploads sanitize client filenames with `Path(...).name`; artifact downloads remain confined to approved roots. | [`projects.py`](../../src/brjarvis/web/api/routes/projects.py), [`artifacts.py`](../../src/brjarvis/web/api/routes/artifacts.py) |
| Launcher reliability | The canonical launcher no longer catches every application-factory exception and silently starts an unverified fallback application. | [`bootstrap.py`](../../src/brjarvis/apps/bootstrap.py) |
| Rebuilt UI truthfulness | Production React state no longer imports or boots from fabricated mock records. Live task, artifact, health, connector, project, memory, notification, and approval data are mapped into the snapshot; unsupported areas render explicit empty/unavailable states. | [`api-client.ts`](../../frontend/src/platform/api-client.ts), [`empty-state.ts`](../../frontend/src/platform/empty-state.ts), [`App.tsx`](../../frontend/src/app/App.tsx) |
| Mutating controls | Task creation navigates to the real command surface; task creation follows the persisted server task with a detail read; no-op notification, theme, context, refresh, preview, audit, and provider controls are disabled with explanations rather than pretending to work. | [`App.tsx`](../../frontend/src/app/App.tsx) |
| Legacy compatibility | Legacy chat attachments now submit through authenticated `/api/import/file` and show explicit success/failure feedback instead of only reporting a selected filename. Legacy connector/contact fetch failures also render visible error states. | [`app.js`](../../src/brjarvis/web/static/app.js) |
| Realtime updates | WebSocket events now trigger authoritative snapshot refreshes for task/message/server-ready events, while the client tolerates the server’s current event envelope. | [`websocket-client.ts`](../../frontend/src/platform/websocket-client.ts), [`App.tsx`](../../frontend/src/app/App.tsx) |
| Version and packaging | Runtime version resolution follows installed package metadata with a `41.0.3` source-checkout fallback. Legacy HTML/JavaScript/service-worker labels and cache identity, frontend package metadata, and packaged rebuilt assets are synchronized. | [`version.py`](../../src/brjarvis/core/version.py), [`sw.js`](../../src/brjarvis/web/static/sw.js), [`build_frontend.py`](../../scripts/build_frontend.py) |
| Desktop correctness | The final repository-wide critical undefined-name scan is clean after importing `Mapping` in the floating desktop surface. | [`floating_surface.py`](../../src/brjarvis/desktop/floating_surface.py) |

## Validation matrix

| Validation | Result |
|---|---|
| Maintained Python tests: `pytest tests -m "not benchmark" -q --tb=short --timeout=60` | **351 passed, 1 skipped, 2 deselected** |
| Focused web/API regressions | **8 passed** in the route-contract file; the broader web workspace subset reached **17 passed** |
| Frontend typecheck: `pnpm typecheck` | **Passed** |
| Frontend production/package build: `pnpm build:static` | **Passed**; Vite transformed 1,809 modules and copied output to `src/brjarvis/web/static/dist` |
| Critical correctness scan: `ruff check src --select E9,F63,F7,F82` | **Passed** |
| Repaired-module Ruff scan | **Passed** |
| Dependency vulnerability scan: `pip-audit -r requirements.txt` | **No known vulnerabilities found** |
| OpenAPI route contract | **No doubled `/api/v1/api/...` paths**; normalized versioned paths asserted by regression test |
| Legacy JavaScript syntax | **Passed**: `node --check` for `app.js` and `sw.js` |
| Working-tree whitespace check | No reported whitespace errors; Git emitted only existing line-ending normalization warnings |

## Preserved existing work

The repair was performed in the attached working tree without resetting or discarding pre-existing modifications. In particular, existing changes in gateway configuration, application paths, startup smoke tooling, routing, backend registration, orchestration, legacy static files, Career profile data, adversarial tests, and smoke tests remain in the working tree. The final Git status must therefore be reviewed as a combined change set rather than interpreted as a clean-branch diff.

## Bounded residual work

A broad Ruff scan still reports **744 repository-wide findings**, dominated by legacy `F405` import-star usage, `E402` import ordering, `F841` unused variables, `F401` unused imports, and naming/whitespace debt. These are quality and maintainability findings rather than failures in the critical correctness classes; they were intentionally not mass-fixed because automatic edits across legacy modules could overwrite or alter existing user work without behavior-specific tests. The critical scan for syntax, undefined names, and related runtime correctness classes is clean.

The legacy static dashboard remains in the repository for compatibility, while the server’s default rebuilt UI is generated from `frontend/src` and packaged by `scripts/build_frontend.py`. External connector credentials should still be rotated by the operator if the legacy plaintext file was ever committed, copied, or exposed before this repair; secure migration prevents future plaintext persistence but cannot revoke a secret already issued by a provider.

## References

[1]: ../../docs/MASTER_REBUILD_PLAN.md "BRJARVIS master rebuild plan"
[2]: ../../docs/CURRENT_ARCHITECTURE.md "BRJARVIS current architecture"
[3]: ../../docs/forensic/21_TECHNICAL_DEBT.md "BRJARVIS technical debt inventory"
[4]: ../../docs/audit/PRODUCTION_READINESS_2026-08-19.md "BRJARVIS production-readiness assessment"
[5]: ../../pyproject.toml "BRJARVIS package metadata and dependency declarations"

## Second full-update pass

The post-publication re-audit found additional partial surfaces and corrected them without replacing the existing architecture. The rebuilt client now maps live connector summaries, persistent memory entries, Career profile data, project files, and notification-derived timeline data. Workspace search is functional, artifact previews call the protected preview endpoint, Career OS can invoke live ATS-ready resume generation, and task/approval/artifact views render explicit zero-record states. The legacy chat attachment control now submits files to the authenticated import endpoint and reports import failures visibly.

The backend now exposes mutable contact update and delete operations through the normalized API, reports missing persistent-memory deletes as HTTP 404, and exposes Career OS under both `/api/career` and `/api/v1/career`. The new regressions cover contact CRUD, missing-memory behavior, Career profile access, and the versioned route contract.

The focused regression checkpoint for this pass is **29 passed**. The frontend package build and static asset regeneration also pass after the new live views and actions were added.

## Final regression repair

The final full-suite run exposed a race in the desktop context card: asynchronous task-history refresh could overwrite an active approval context and duplicate its action buttons. The widget now suppresses history refresh while a task is running or awaiting approval. The targeted Qt regression passes, and the complete maintained suite now reports **353 passed, 1 skipped, and 2 deselected**.


## Third full-project workability pass

The third pass completed the remaining exposed rebuilt-surface interactions and closed additional backend defects. Command Center context attachments now use authenticated multipart upload into a contained persistent `.imports` workspace, with filename normalization and a 25 MiB limit. Workspace file rows are selectable and use a project/file-scoped preview endpoint with a 1 MiB text-preview bound, binary-file handling, and no absolute host-path disclosure. Project-file uploads are bounded and written atomically; project metadata responses no longer expose stored host paths.

Memory now supports live create and delete operations from the rebuilt UI and refreshes from canonical state. The snapshot includes encrypted contact summaries, nested Career profile normalization, and project/file identities. Business OS is a live summary of stored projects, contacts, active work, and artifacts rather than fabricated CRM data; external CRM/invoicing data remains connector-dependent. Notifications open the live Operations timeline, theme switching is functional, and Career feedback no longer claims verification unless the backend status is `SUCCESS_VERIFIED`.

Generic document import now rejects server paths outside the configured workspace root, bounds uploads to 25 MiB, and preserves uploaded source files inside the contained workspace import directory so vector metadata does not point to deleted temporary files. New route regressions cover contained workspace preview and generic import path rejection.

The fresh final gates report **355 passed, 1 skipped, and 2 deselected**; frontend typecheck, packaged Vite build, both legacy JavaScript syntax checks, critical Ruff, and `pip-audit` all pass. The packaged rebuilt assets were regenerated into `src/brjarvis/web/static/dist`.


## Fake-data cleanup pass

A production-focused audit removed the unused `MockAndroidDevice` implementation and its package export, removed the fabricated `CarolynAddison` example workspace, and deleted the tracked generated `config/proxy_test_results.json` benchmark snapshot. The generated proxy-result path is now ignored so stale model probe output cannot be recommitted. Cross-device WhatsApp planning no longer injects the hard-coded recipient `Rahul`; it derives an explicit recipient query from the user goal and otherwise leaves recipient resolution to authorized contact state.

Intentional test fixtures under `tests/fixtures` remain isolated test inputs and are not imported by production code. The committed Career profile is retained as user-provided profile data rather than treated as demo content. A second production-source scan found no remaining recognizable fabricated records such as the removed mock contacts, sample device, CarolynAddison workspace, or demo companies. The post-cleanup suite reports **355 passed, 1 skipped, and 2 deselected**; critical Ruff and legacy JavaScript syntax checks also pass.
