# BR JARVIS MK40.2+ — Career OS Dependency Graph

Acyclic dependency hierarchy ensuring zero circular imports and strict layering.

```
                  ┌──────────────────────────────────────────────────┐
                  │                 ENTRY POINTS                     │
                  │ (start.py, brjarvis.py, core/cli.py, web, voice) │
                  └────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────────────┐
                  │            APPLICATION SERVICE LAYER             │
                  │  (career/api_routes.py, career/tools.py)         │
                  └────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────────────┐
                  │               DOMAIN / SERVICE LAYER             │
                  │ (crm, email_intelligence, job_engine, resume)    │
                  └────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────────────┐
                  │             CANONICAL DOMAIN MODELS              │
                  │               (career/models.py)                 │
                  └────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────────────┐
                  │              INFRASTRUCTURE / DATA               │
                  │   (memory/canonical_db.py, SQLite WAL, Excel)    │
                  └──────────────────────────────────────────────────┘
```

## Layering Rules Enforced:
1. Entry Points $\rightarrow$ Service Layer $\rightarrow$ Domain Layer $\rightarrow$ Models $\rightarrow$ Infrastructure.
2. Web UI / CLI / Voice never import infrastructure directly; they communicate via canonical services.
3. Zero circular imports between `career/models.py`, `career/crm/database.py`, and `career/crm/state_machine.py`.
