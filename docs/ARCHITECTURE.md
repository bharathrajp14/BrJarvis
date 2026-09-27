# BRJARVIS — Current Architecture

This document describes the system **as it is**, verified against the tree, not as it is
intended to become. The rebuild target and the reasoning behind it live in
[DECISIONS.md](DECISIONS.md).

Last verified: 2026-08-28, commit following Phase 0 dead-code removal.

## Scale

| Measure | Value |
|---|---|
| Python modules under `src/brjarvis/` | 477 |
| Python LOC (tracked, whole repo) | 128,643 |
| Subpackages under `src/brjarvis/` | 34 |
| Test files / tests | 81 files, 361 passing + 1 skipped |
| Frontend | React 19 + Vite + TypeScript, 13 source files |

Largest subpackages, by LOC: `tools/` 15,639 · `actions/` 15,133 · `core/` 14,611 ·
`career/` 12,315 · `memory/` 8,502 · `agent/` 7,770 · `voice/` 5,274 · `ui/` 4,503.

## Surfaces

All five surfaces resolve one runtime rather than constructing their own provider
clients. `start.py` is the dispatcher.

| Surface | Launch | Entry module |
|---|---|---|
| Web control plane | `python start.py web` | `brjarvis.web.api.server:create_app` |
| CLI REPL | `python start.py cli` | `brjarvis.apps.cli` |
| Voice (Qt) | `python start.py voice` | `brjarvis.voice.assistant` |
| Floating widget / HUD | `python start.py floating` | `brjarvis.ui.main_window` |
| Career OS | `python start.py career` | `brjarvis.career` |
| Diagnostics | `python start.py doctor` | `brjarvis.diagnostics.doctor` |

`server.py` at the repo root is a shim that exposes `app` for ASGI servers; it resolves
`brjarvis.web.api.server.create_app`. The root `main.py`, `ui.py`, `ui_mark.py`,
`float_widget.py` and `permissions.py` are similar thin shims.

## Composition root

`src/brjarvis/core/bootstrap.py` (194 LOC) is the maintained composition root.
`build_assistant_runtime()` loads model backends, creates the `AgentRouter` and
`JarvisOrchestrator`, registers shared instances in the DI container
(`core/di.py`), installs shutdown handling (`core/lifecycle.py`), and publishes the
startup event.

## Request path

`orchestrator/core.py` (1,384 LOC) runs the canonical loop: recall context → select
provider → parse structured tool calls → evaluate policy → dispatch permitted tools →
persist evidence → synthesise a response from recorded tool results. It applies a
maximum tool-iteration cap and a cyclic-call threshold.

Tool dispatch goes through `tools/registry.py` (1,036 LOC), a decorator-based registry.
Plugins load in two stages — core plugins eagerly, an extended list on demand — by
dynamic `importlib` calls over a hardcoded list of module names.

## Known structural problems

These are measured, not speculative. Each is a target of a numbered rebuild phase.

1. **`actions/` and `tools/` implement the same domains.** 15,133 and 15,639 LOC
   respectively, both covering browser control, web search, WhatsApp, Telegram,
   reminders, calendar, file operations, PDF, Excel and system control.
   `tools/legacy_actions_tools.py` exists only to wrap `actions/` in the newer
   `ToolResult` contract.
2. **Three model layers.** `gateway/` (11 modules), `router/` (4 modules) and
   `integrations/backends/`. There is no single call path to a provider.
3. **Fragmented memory.** 31 modules in `memory/` with overlapping ownership
   (`store.py`, `persistent_store.py`, `unified_memory.py`, `canonical_db.py`,
   `memory_manager.py`, `working.py`, `workspace_store.py`), plus a checked-in
   `long_term.json`. Around 20 modules open their own SQLite file.
4. **God modules.** `core/intent_engine.py` 2,394 · `core/terminal/commands.py` 2,068 ·
   `ui/main_window.py` 1,723 · `orchestrator/core.py` 1,384.
5. **User data inside the package.** `src/brjarvis/workspace/` holds tracked resumes and
   a career profile — application data living in the import path.
6. **Weak lint and contract gates.** `ruff` reports 780 findings under a narrow
   `E,F,W,I` ruleset (530 are `F405`, from `import *`). `.importlinter` defines a single
   contract.

## Quality gates that exist today

```bash
python -m pytest -q                    # 361 passed, 1 skipped, ~40s
python -m ruff check src tests apps    # 780 findings
lint-imports                           # 1 contract, kept
python -m compileall -q src apps       # clean
```

## Diagrams

Editable Mermaid sources with rendered PNGs in `docs/architecture/`:
`system-context`, `request-lifecycle`, `task-state-machine`, `production-architecture`.
They predate Phase 0 and are regenerated at cutover.

## Archived documentation

`docs/archive/` holds 282 files from prior remediation cycles — around twenty `FINAL_*`
documents, three competing master plans, and two different top-20 problem lists. They
are kept for provenance and are not maintained. Treat anything in there as a historical
claim, not a description of the system.
