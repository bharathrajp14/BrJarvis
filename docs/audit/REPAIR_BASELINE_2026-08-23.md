# BRJARVIS Repair Baseline — 2026-08-23

## Scope

This baseline records the state of the attached Windows working tree before the repair implementation. Existing user modifications were detected and must be preserved unless a later change explicitly targets the same behavior.

## Working tree state

The repository had existing modifications in `config/ai_gateway.yaml`, `config/app_paths.json`, `scripts/smoke_startup.py`, `src/brjarvis/gateway/routing.py`, `src/brjarvis/integrations/backends/__init__.py`, `src/brjarvis/orchestrator/core.py`, `src/brjarvis/web/static/app.js`, `src/brjarvis/web/static/index.html`, `src/brjarvis/web/static/style.css`, `src/brjarvis/workspace/Career/master_profile.json`, `tests/adversarial/test_prompt_injection_guard.py`, and `tests/smoke/test_startup_smoke_suite.py`. Untracked paths included `docs/interview/`, `src/brjarvis/integrations/backends/manus.py`, and `workspace/Projects/`.

These changes predate this repair pass and are not to be reset or discarded.

## Baseline commands

| Check | Result |
|---|---|
| Python maintained tests | `347 passed, 1 skipped, 2 deselected in 33.55s` |
| Editable frontend build | Passed: TypeScript build and Vite production bundle completed successfully; Vite transformed 1,809 modules. |
| Broad Ruff scan | `940 errors`; summary included 530 F405, 120 E402, 78 F401, 57 F841, 44 W293, 19 E741, 16 F821, 9 F541, 8 W291, 5 E401, 2 E722, and 2 E731. 140 fixes were reported as automatically fixable. |
| Tracked-file count | 1,424 tracked files. |

## Confirmed functional and contract discrepancies

| Severity | Finding | Evidence |
|---|---|---|
| P0/P1 | Connector configuration writes raw API keys to `config/api_keys.json`. | `src/brjarvis/web/api/routes/connectors.py` reads `_API_FILE` and assigns `data[key_name] = val` before writing JSON. This bypasses the existing `CredentialVault`. |
| P1 | API versioning is duplicated and inconsistent. | Connector routes declare both `/api/*` and `/api/v1/*` decorators while `server.py` mounts the router again with `prefix='/api/v1'`. Other routers follow similar inline versioning. |
| P1 | Contacts exist but are incompletely integrated. | `memory.py` already exposes `/api/contacts`, `/api/import/contacts`, and `POST /api/contacts`, but only unversioned paths are present; the create response stringifies the contact instead of returning a typed object; the import `file_path` accepts arbitrary host paths; API authentication and full CRUD/search contract coverage are incomplete. |
| P1 | Canonical launcher masks application-factory failures. | `src/brjarvis/apps/bootstrap.py` catches every exception from `create_app()` and silently falls back to `brjarvis.web.api.app`. |
| P1 | Realtime contract drift exists between the React client and server. | Frontend websocket code expects normalized events such as `connection.ready` and `task.updated`, while the server emits `ServerReady`, `Heartbeat`, `task.started`, `message.created`, and raw EventBus topics. |
| P1/P2 | The rebuilt React frontend still has a live-data fallback to hardcoded mock state. | `frontend/src/platform/api-client.ts` imports `initialSnapshot`, uses it when individual snapshot requests fail, and supports an explicit demo mode; `frontend/src/state/app-store.ts` initializes from `mock-data.ts`. |
| P2 | Rebuilt React views contain hardcoded operational-looking values and non-mutating controls. | `frontend/src/app/App.tsx` renders metrics, workspace/index values, provider rows, operations checks, Business OS pipeline/priority data, and simple Career/Memory cards from literals; several buttons only show a toast or have no handler. |
| P2 | Legacy client contains incomplete and silent flows. | `src/brjarvis/web/static/app.js` reports file selection without upload, calls `/api/contacts` without versioned contract, silently swallows connector/contact errors, and uses fabricated fallback text such as `Task completed.` when the backend response is missing. |
| P2 | Version authority is stale. | `src/brjarvis/core/version.py` reports `41.0.0`, while `pyproject.toml` is `41.0.3`; the legacy HTML, style cache-buster, service-worker cache marker, and visible labels also identify `41.0.0`. |
| P2 | Generated/static frontend ownership needs consolidation. | The editable source is under `frontend/src`, generated output under `frontend/dist`, and packaged output under `src/brjarvis/web/static/dist`; the server defaults to the packaged dist while legacy static assets remain separately served. |
| Deferred P1 | Broad legacy quality debt remains. | Ruff broad scan reported 940 findings; correctness classes such as undefined names, syntax/import errors, duplicate registrations, and silent exception handling must be triaged before cosmetic debt. |

## Repair order

1. Preserve the existing working-tree changes and complete the hard runtime/API repairs.
2. Remove mock/fake operational behavior and make unsupported controls explicit.
3. Correct credential, route, version, dependency, and generated-asset migrations.
4. Consolidate architecture in bounded, tested increments.
5. Run the full validation and clean-wheel/release evidence gates.

## Initial acceptance baseline

The current repository can pass its maintained Python test suite and build the editable React client, but those green checks do not prove live-data truthfulness, complete route parity, secure connector persistence, version consistency, or successful user-facing mutations. The repair is complete only when the acceptance criteria in `docs/MASTER_REBUILD_PLAN.md` and the approved execution plan are met and any external credential-rotation requirement is explicitly recorded.


## Executed repairs

The repair pass normalized contacts, connectors, projects, tasks, and artifacts to relative route decorators composed under `/api` and `/api/v1`; this removed the doubled `/api/v1/api/...` paths that were present in the OpenAPI surface. Contact file imports are now confined to the configured workspace root, upload filenames are sanitized, and connector API keys are stored through `CredentialVault` with a one-time scrub of legacy `api_keys.json` entries after successful migration.

The rebuilt React client no longer boots from fabricated task, artifact, timeline, capability, Business OS, workspace, memory, or Career OS records. It hydrates from live tasks, artifacts, health, connectors, projects, memory, and notifications; it displays explicit empty/unavailable states where no authoritative endpoint exists; and task creation performs a follow-up read of the persisted task rather than inventing progress. Stale controls are disabled with explanatory labels or route to the real command surface.

The launcher no longer catches all application-factory exceptions and silently starts a fallback app. Runtime version resolution now reads installed package metadata with a source-checkout fallback of 41.0.3; legacy HTML, JavaScript, service-worker, and frontend package metadata were synchronized to 41.0.3. Validation at this checkpoint: focused web regressions 8 passed, full maintained Python suite 349 passed / 1 skipped / 2 deselected, and the rebuilt frontend/static packaging completed successfully.


## Upgrade and migration checkpoint

Dependency review found no known vulnerabilities in `requirements.txt` under `pip-audit`. The installed environment already satisfies the declared safe ranges; major candidates such as `google-genai` 2.x and `youtube-transcript-api` 1.x were not adopted blindly because they exceed the project’s declared compatibility caps. The frontend package metadata is now 41.0.3, and `pnpm build:static` regenerates and copies the packaged bundle successfully.

A route-contract regression now asserts that the OpenAPI surface contains no `/api/v1/api/...` paths and that normalized task, project, artifact, contact, and connector paths exist under `/api/v1`. Targeted Ruff checks pass for all repaired backend modules, and `pip-audit` reports no known vulnerabilities.
