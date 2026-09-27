# BR JARVIS MK40.2+ — Startup & Entry Point Audit

## 1. Authoritative Entry Points
- `python start.py`: Unified Rich launcher menu with sequence 12 (`CAREER OS`) and direct flags (`python start.py career`, `python start.py career-sync`).
- `python brjarvis.py`: Global command router routing `career`, `applications`, `interviews`, `offers`, `emails`, `jobs`, `ats`.
- `python -m core.cli`: Terminal REAct orchestrator with full `/career` family commands.
- `python start.py web`: FastAPI server with mounted Career Studio endpoints and static Web client.
- `python start.py voice`: Hands-free voice assistant with continuous background career event awareness.
- `python start.py doctor`: Comprehensive system diagnostic and self-healing engine.

## 2. Boot Integrity
- All entry points load configuration via `core/config.py`, establish SQLite WAL connectivity, verify tool registry schemas, and report accurate readiness states.
