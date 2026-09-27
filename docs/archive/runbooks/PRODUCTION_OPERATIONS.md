# BR-JARVIS Production Operations Runbook

## Purpose

This runbook defines the supported setup, security configuration, validation, startup, shutdown, incident response, and rollback procedures for BR-JARVIS 41.0.0 after the August 2026 production-hardening upgrade.

## Supported environment

Use Python 3.11–3.13 in a project-local virtual environment. Python dependencies must be installed from `pyproject.toml`; do not use `--no-deps`, `--break-system-packages`, or global system Python. On Windows run `setup_env.bat --dev` for a development environment. On Linux run `./setup_linux.sh --dev`.

## Required security configuration

Copy `.env.template` to `.env` and replace every placeholder. Generate the server key with a cryptographically secure generator:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The production baseline is:

```dotenv
JARVIS_SERVER_API_KEY=<unique random value of at least 24 characters>
JARVIS_PERMISSION_MODE=confirm_destructive
JARVIS_HEADLESS=false
JARVIS_ENABLE_UNSAFE_HOST_EXECUTION=false
JARVIS_ENABLE_UNTRUSTED_PLUGINS=false
JARVIS_COOKIE_SECURE=true
JARVIS_CORS_ORIGINS=https://your-approved-origin.example
```

`JARVIS_COOKIE_SECURE=true` requires HTTPS. Terminate TLS at a trusted reverse proxy, restrict the listening interface and firewall, and never expose the control plane directly to an untrusted network.

Secrets used by connectors must be stored through `CredentialVault`, which uses the operating-system credential store. JSON metadata files must not contain secret values. Environment-variable fallback is suitable for managed deployment secrets but must not be written into logs, prompts, or artifacts.

## Credential incident response

A tracked nested API-key file was removed during the upgrade. Treat every real secret that ever appeared in that file or another commit as compromised.

1. Revoke or rotate the secret at the provider.
2. Invalidate associated sessions, refresh tokens, and application passwords.
3. Review provider audit logs for unknown access.
4. Update the OS keyring or managed deployment secret.
5. Verify that `detect-secrets scan --baseline .secrets.baseline` passes.
6. Decide whether coordinated Git history rewriting is required. History rewriting does not replace provider-side rotation.
7. Record completion outside the repository without storing the new secret.

## Preflight validation

Run from the repository root with the virtual environment active:

```bash
python -m pip check
python -m pytest tests -m "not benchmark" -q --tb=short --timeout=60
ruff check src/brjarvis/security src/brjarvis/events src/brjarvis/web \
  src/brjarvis/plugins/plugin_manager.py src/brjarvis/tools/domain.py \
  src/brjarvis/tools/registry.py src/brjarvis/tools/runtime.py \
  src/brjarvis/tools/sandbox.py src/brjarvis/agent/agent_loop.py \
  src/brjarvis/agent/task_queue.py
pyright src/brjarvis/security/credentials.py src/brjarvis/events/store.py \
  src/brjarvis/agent/task_queue.py src/brjarvis/web/api/state.py
lint-imports
bandit -q -r src/brjarvis/security src/brjarvis/web src/brjarvis/tools/sandbox.py -ll
pip-audit --skip-editable
python scripts/check_licenses.py
detect-secrets scan --baseline .secrets.baseline
```

The broader repository Ruff scan is a measured modernization backlog and is not yet a release gate. Any new or modified production file must be included in the clean incremental scope.

## Build and installed-artifact verification

Build outside the source-of-truth workflow only after tests pass:

```bash
python -m build
python -m venv /tmp/brjarvis-wheel-smoke
/tmp/brjarvis-wheel-smoke/bin/python -m pip install dist/*.whl
cd /tmp
JARVIS_SERVER_API_KEY=<test-only-random-key> \
  /tmp/brjarvis-wheel-smoke/bin/python -c \
  "from brjarvis.web.api.server import create_app; from brjarvis.web.api.state import WEB_DIR; app=create_app(); assert (WEB_DIR/'index.html').is_file(); assert len(app.routes) >= 40"
```

On Windows replace `/tmp/.../bin/python` with the external virtual environment's `Scripts\python.exe`. The smoke test must run outside the repository to prove the wheel has no source-checkout dependency.

Delete generated `build/`, `dist/`, and `*.egg-info` directories after the verified artifacts have been copied to the release location.

## Startup

The canonical installed commands are:

```bash
jarvis status
jarvis-cli
jarvis-server
```

For a source checkout, `python start.py web` is a compatibility adapter. Startup fails when the server key is missing, weak, or still a template placeholder. This is expected fail-closed behavior.

Web startup builds the runtime, starts the task queue, runs crash recovery, and activates WebSocket logging. Recovery marks interrupted tasks with checkpoints as paused for user-directed resume and tasks without checkpoints as failed for review.

## Shutdown

Use the normal process termination signal. The web lifespan deactivates WebSocket logging, requests cooperative cancellation, waits a bounded period for workers, closes event persistence, and shuts down the orchestrator. Do not terminate the process forcibly unless the grace period expires and investigation confirms a stuck external dependency.

A task in `cancelling` has received a cancellation request but has not yet acknowledged it. `cancelled` and `timed_out` are terminal only after worker exit.

## Monitoring and audit evidence

Monitor:

| Signal | Healthy condition | Escalation condition |
|---|---|---|
| Health endpoint | Auth-exempt health response is available locally | Repeated failure or degraded runtime dependencies |
| Task statuses | Terminal states match actual outcomes | Tasks remain `running`/`cancelling` beyond deadline plus grace period |
| Event writer | `dropped_writes == 0` | Any dropped writes or repeated rotation/write failures |
| Agent terminal event | `agent.completed` only for verified success | Completion after tool/verification failure |
| Auth logs | Expected login and ticket activity | Repeated invalid login, origin rejection, or ticket replay |
| Dependency gates | No known vulnerabilities | New advisory or prohibited license |

The local event store is bounded and rotating. It is suitable for a single-user local deployment, not as the sole audit system for a distributed or regulated environment.

## Rollback

Recovery material for this upgrade was created under the external recovery directory `C:\Users\bhara\Documents\BR-JARVIS\recovery\20260819-production-upgrade`.

Preferred rollback is Git-based:

1. Stop BR-JARVIS cleanly.
2. Preserve new runtime data separately; do not copy it over older databases blindly.
3. Switch from `upgrade/production-hardening-20260819` to the prior branch or commit.
4. Recreate `.venv` from that revision's dependency metadata.
5. Restore only the specific configuration or untracked file required from the external recovery snapshot.
6. Run the prior revision's smoke tests before startup.

If repository metadata is damaged, clone from `repository.bundle` into a new directory rather than overwriting the working tree. Never use rollback to restore revoked credentials; provision newly rotated values.

## Known compatibility changes

The root `brjarvis.py` launcher is quarantined under `legacy/launchers` because it shadowed the installable package. Import `brjarvis.web.api` instead of `apps.web.api`; the latter is a deprecated adapter. Code execution and community plugins are disabled by default. ChromaDB is not part of the default memory installation pending an upstream security fix. PyMuPDF is available only through the explicit `pdf-rendering` extra and requires a separate license review.
