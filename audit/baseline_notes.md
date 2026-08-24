# Baseline Notes

## Repository state

- Repository: `Br-Jarvis`
- Branch: `main`
- Latest observed commits: `3a718a5 Remove fabricated production data and mock device`, `45be3ab Complete live project surfaces and safe workspace previews`, `abaf6ba fix: complete remaining live flows and desktop state`, `73d8de4 feat: complete live workspace and career flows`, `5de3d12 fix: remove web launcher fallback`.
- No root or parent `AGENTS.md` was present.
- The repository was already dirty only because this audit created the untracked `audit/` directory; no pre-existing modified files were shown by the captured `git status`.

## Scope signal

The source tree is broad and includes `actions`, `agent`, `apps`, `career`, `computer`, `config`, `connectors`, `context`, `contracts`, `core`, `desktop`, `diagnostics`, `events`, `execution`, `gateway`, `guardian`, `history`, `integrations`, `memory`, `multi_agent`, `native`, `orchestrator`, `plugins`, `reasoning`, `router`, `security`, `screen_server`, `skills`, `tools`, `ui`, `vision`, `voice`, `web`, `workflow`, and `workspace`. The initial recursive inventory contained generated `__pycache__` and `.pyc` entries, so the next inventory must distinguish maintained source from generated artifacts.

## Verified architectural entry points

- `src/brjarvis/core/bootstrap.py` defines a process-wide `AssistantRuntime` singleton guarded by a `threading.Lock`; it builds available backends, `AgentRouter`, `JarvisOrchestrator`, event bus, and lifecycle shutdown hook.
- `src/brjarvis/web/api/server.py` builds the runtime in FastAPI lifespan, sets a global orchestrator, runs recovery inspection, activates a process-global WebSocket log handler, stops the queue/event store, and shuts down the orchestrator.
- The web factory mounts unversioned and `/api/v1` routers, serves a rebuilt or legacy UI, uses global middleware for auth/security/CORS, and has a root static/fallback handler.

## Initial risk hypotheses requiring source/test confirmation

1. Runtime lifecycle is owned in multiple places: `bootstrap.py` registers a shutdown hook while the web lifespan also calls `orch.shutdown()` directly. This may be idempotent or may double-shutdown resources.
2. `reset_assistant_runtime()` clears only the singleton reference and does not visibly reset `CoreRuntime`, event bus, queue, or lifecycle state; test isolation and repeated startup need verification.
3. The server CSP allows `unsafe-inline`, `unsafe-eval`, broad `connect-src`, and CDN script/style hosts; this may be intentional for legacy/rebuilt UI but should be measured against actual assets and tightened if possible.
4. CORS allows credentials and wildcard methods/headers with default localhost origins; the effective security posture and browser auth behavior need route-by-route testing.
5. Authentication middleware exempts broad path prefixes such as `/web`, `/static`, `/galaxy`, and `/3d`; exact exposure and session/auth route behavior require verification.
6. WebSocket log broadcasting creates an independent task per active socket for every log line, with a short send timeout and no explicit backpressure; high-volume logging may create task pressure or message loss.
7. Router duplication and legacy/rebuilt UI coexistence increase the chance of route precedence, stale client, and API contract drift; route enumeration and frontend client comparison are required.

## Baseline checks

- `compileall -q src` completed successfully.
- A pytest baseline log was produced but the wrapper did not create a reliable terminal status file; the log visibly begins with passing dots and one skip and must be rerun with a simpler status-capture command before using it as a completed-suite claim.

## Next action

Trace the canonical runtime, task execution, auth, persistence, and frontend flows; enumerate maintained `.py`, frontend, test, migration, and deployment files while excluding generated artifacts; then write the current-state architecture map and evidence-backed findings register before editing source.
