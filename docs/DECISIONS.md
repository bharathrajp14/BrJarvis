# Rebuild Decisions

One entry per decision that shapes the rebuild. Append; do not rewrite history. The
current state of the system is described in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## D1 — Rebuild by strangler, not greenfield

**Date:** 2026-08-28 · **Status:** accepted

Build a clean `src/jarvis/` package. Port one subsystem at a time, deleting the
`src/brjarvis/` equivalent in the same commit. The system stays runnable throughout.

Rejected: a new empty repository. 128k LOC across five surfaces encodes behaviour that is
not recoverable from documentation — DPI quirks in desktop automation, Qt threading
fixes, Career OS data shapes. Rejected: consolidating in place. `docs/archive/` records
several attempts at exactly that, none of which converged.

---

## D2 — Same stack; PySide6 retained

**Date:** 2026-08-28 · **Status:** accepted

Python 3.11+, FastAPI, Pydantic v2, SQLite in WAL mode, React 19 + Vite + TypeScript.
Code can be ported rather than translated. PySide6 stays because the voice HUD and
floating widget are in-scope surfaces; replacing them with web equivalents is a product
change, not a rebuild.

Note: the repository currently has two interpreters — `.venv` on 3.12.10 (fully
provisioned) and a system 3.14.0. Development uses `.venv`.

---

## D3 — One model gateway, multi-provider

**Date:** 2026-08-28 · **Status:** accepted

A single `jarvis/gateway/` exposing `ModelGateway.generate()` / `.stream()`, with one
`ProviderAdapter` protocol per provider (Gemini, Claude, OpenAI, Ollama), capability
filtering, and circuit-breaker failover. `router/` and `integrations/backends/` are
deleted and their routing logic folded into `gateway/routing.py`.

Multi-provider is kept rather than collapsing to one provider because `config/models.yaml`
and the existing quota-failover behaviour depend on it.

---

## D4 — Delete only what three independent checks agree is dead

**Date:** 2026-08-28 · **Status:** accepted, applied in Phase 0

A module is removed only when all three agree:

1. `audit/reachability.py` — static import graph from every real entrypoint, resolving
   the dynamic plugin loads in `tools/registry.py` and `connectors/hub.py`.
2. `audit/runtime_probe.py` — boots tool registry, connectors, skills, backends, web app,
   CLI, desktop, voice and career, then records `sys.modules`.
3. `audit/confirm_deletions.py` — import-form reference sweep over code, config and CI,
   iterated to a fixpoint so modules held only by other dead modules are also cleared.

Static analysis alone was wrong by a wide margin: it called 119 modules dead, of which the
runtime probe revived 55. Naive stem-based reference matching was wrong in the other
direction, holding back `computer/operator.py` because a React file contains the word
"operator". Both errors are worth remembering — either one alone would have produced a
bad delete list.

Applied: 49 modules plus `legacy/launchers/brjarvis.py`, 10,079 LOC.

---

## D5 — `docs/` archived rather than deleted

**Date:** 2026-08-28 · **Status:** accepted, applied in Phase 0

282 files moved to `docs/archive/`. `docs/` now holds this file, `ARCHITECTURE.md`, and
the four Mermaid diagram pairs the README links.

Correction to an earlier count: the repository has 672 markdown files, but 369 of those
are `SKILL.md` files under `src/brjarvis/skills/library/` — runtime skill *data*, not
documentation. Actual documentation was 266 files in `docs/` plus 25 in `notes/`.

---

## D6 — Invariants enforced by CI, not convention

**Date:** 2026-08-28 · **Status:** accepted, enforcement lands in Phase 7

- `surfaces/*` may import `core`, `gateway`, `tools`, `memory`, `agent` — never each other.
- Only `memory/db.py` opens a SQLite connection; every write goes through the
  serialiser ported from `memory/sqlite_lock.py`.
- Only `gateway/adapters/` imports a provider SDK.
- Every tool returns `ToolResult`; none returns a bare string.
- No module exceeds 600 LOC.

Conventions stated in prose have already failed here once — `docs/archive/` asserts
several of these as done. They become `.importlinter` contracts and CI checks instead.
