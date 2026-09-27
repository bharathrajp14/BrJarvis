# Production-Hardening Change Manifest

**Branch:** `upgrade/production-hardening-20260819`  
**Date:** 19 August 2026

This manifest distinguishes the production-hardening work from changes that were already present in the user's working tree. No pre-existing uncommitted work was discarded, reset, or overwritten as part of repository protection.

## Upgrade-owned changes

| Scope | Principal files | Change |
|---|---|---|
| Web security | `src/brjarvis/web/api/state.py`, `server.py`, `routes/auth.py`, `routes/websocket.py`, packaged `static/app.js` | Fail-closed strong-key startup, authenticated cookie sessions, one-time WebSocket tickets, origin validation, no browser key persistence, contained static serving |
| Web packaging | `src/brjarvis/web/**`, `apps/web/api/__init__.py`, `src/brjarvis/apps/web.py`, `src/brjarvis/apps/bootstrap.py`, root `server.py` | Moved API/PWA into installable namespace and retained a deprecated compatibility adapter |
| File security | `src/brjarvis/career/api_routes.py` | Enforced workspace containment and regular-file checks; aligned Career client/server contracts |
| Policy and tool governance | `src/brjarvis/security/policy_engine.py`, `permissions.py`, `src/brjarvis/tools/domain.py`, `registry.py`, `runtime.py` | Confirmation-first defaults, secure metadata derivation, protected-permission approval enforcement |
| Credentials | `src/brjarvis/security/credentials.py`, `.gitignore`, `.secrets.baseline` | OS keyring values, metadata-only atomic files, nested credential ignores, secret regression gate |
| Execution and plugins | `src/brjarvis/tools/sandbox.py`, `src/brjarvis/plugins/plugin_manager.py` | Fail-closed code execution and explicit trusted-plugin opt-in |
| Agent reliability | `src/brjarvis/agent/agent_loop.py`, `task_queue.py` | Typed terminal results, truthful events, deadlines, acknowledged cancellation, bounded shutdown |
| Events | `src/brjarvis/events/store.py`, `bus.py` | Bounded history, asynchronous rotating persistence, non-skipped async subscribers |
| Lifecycle | `src/brjarvis/web/api/server.py` | Recovery startup and deterministic queue/event/orchestrator shutdown |
| Dependencies and packaging | `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `setup.py` | Authoritative metadata, package resources, platform markers, patched dependencies, isolated high-risk optional dependencies |
| Setup and CI | `setup_env.bat`, `setup_linux.sh`, `.github/workflows/ci.yml`, `.importlinter`, `scripts/check_licenses.py` | Virtual-environment-only setup and independent quality/test/package/security gates |
| Legacy quarantine | `legacy/launchers/brjarvis.py` | Removed root package shadowing while preserving the launcher |
| Tests | Updated integration/adversarial/unit files plus new credential, event, and queue lifecycle suites | Negative-path and release-gate coverage |
| Documentation | `README.md`, `CHANGELOG.md`, `docs/audit/**`, `docs/runbooks/**`, `docs/architecture/production-architecture.*` | Production assessment, architecture, operations, rollback, and compatibility guidance |
| Sensitive tracked file | Deleted `apps/web/config/api_keys.json` | Removed from current tree; provider-side rotation remains mandatory |

Ruff's safe fixes also normalized imports and removed unused symbols within the hardened security, event, and packaged web scopes. The complete test suite passed after those changes.

## Pre-existing working-tree changes preserved

The protection snapshot showed user work that was not created as part of this hardening effort. Examples visible in the final status include the deletion of `pytest.ini`, modifications to `src/brjarvis/__init__.py`, `src/brjarvis/core/version.py`, and `start.py`, and untracked work such as `_tmp_fix.py`, `src/brjarvis/evolution/engine.py`, `tests/unit/test_evolution_engine.py`, and `upgrade_plan.md`. These items were preserved and must be reviewed by the user when separating or committing the upgrade.

## External recovery and build artifacts

Recovery material and final distributions are stored outside the repository under:

`C:\Users\bhara\Documents\BR-JARVIS\recovery\20260819-production-upgrade`

This directory contains the repository bundle, baseline status/diffs, untracked-file preservation, validation outputs, the final wheel and source distribution, an isolated build context, and the external wheel smoke environment. Sensitive values are not reproduced in this manifest.
