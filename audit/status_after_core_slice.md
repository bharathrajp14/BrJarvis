# BrJarvis Rebuild Status — Core Slice

**Date:** 2026-08-28  
**Working tree:** `main`, one commit ahead of `origin/main`; changes remain uncommitted.

## Current project status

The repository is still running the legacy `src/brjarvis/` runtime. It contains 477 Python modules under that package, approximately 128,643 tracked Python lines across the repository, 81 test files, and a React/Vite frontend. The current full regression suite passes with 367 tests and one skip.

Phase 0 has already been partially applied in the working tree: historical documentation has been moved to `docs/archive/`, and the current architecture and decisions documents are present. The old `apps/web/dashboard/`, the legacy `src/brjarvis/` package, the duplicate model layers, and the fragmented memory implementation still exist, so the full rebuild is not complete.

A conservative static import report was generated at `audit/reachability.json`. It found 477 legacy-package modules, 246 reachable from the selected entrypoint union, and 231 static candidates for further review. This report does not account for every dynamic import and must not be used alone for deletion.

## Implemented development slice

A new `src/jarvis/` package now contains the Phase 1 core skeleton:

- `core/config.py`: validated Pydantic Settings configuration, dotenv loading, provider credential detection, and production startup validation.
- `core/paths.py`: canonical project, runtime, data, config, and workspace layout with workspace containment checks.
- `core/di.py`: thread-safe instance, singleton, and transient dependency registration.
- `core/lifecycle.py`: reverse-order, idempotent asynchronous shutdown hooks.
- `core/errors.py`: structured `JarvisError`, `ConfigurationError`, and `TaskExecutionDiagnostic` types.
- `core/logging.py`: centralized logging configuration.
- `core/bootstrap.py`: the new `AssistantRuntime` composition root and core doctor report.

The existing launcher now exposes `python start.py core-doctor`, and `python start.py doctor` includes the new core readiness report while preserving the existing diagnostics. Both `pyproject.toml` and `requirements.txt` include `pydantic-settings` and package discovery includes `jarvis*`.

## Verification

| Check | Result |
|---|---|
| Full regression suite before slice | 361 passed, 1 skipped |
| Full regression suite after slice | 367 passed, 1 skipped |
| New core unit tests | 6 passed |
| New core Ruff check | Passed |
| New core Pyright check | 0 errors, 0 warnings, 0 informations |
| New core compilation | Passed |
| `python start.py core-doctor` | Healthy; development environment; Python 3.12.10 |
| `python start.py doctor` | Completed and saved to `audit/doctor_after_core_slice.txt` |
| Import-linter baseline | 1 contract kept, 0 broken |
| Full-project Ruff baseline | Existing legacy findings remain; the new core slice is clean |
| Full-project Pyright baseline | Existing legacy findings remain: 565 errors, 33 warnings |

## Next recommended slice

The next implementation phase should be the new `src/jarvis/gateway/` package. It should define the provider protocol and model gateway without importing provider SDKs anywhere outside gateway adapters, then add recorded-response adapter contracts and mid-stream failover tests before deleting the old router/backends copies.
