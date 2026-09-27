# BR JARVIS — LEGACY INVENTORY & CONSOLIDATION LEDGER

## 1. Consolidated Entrypoints & Deprecated Shims

| Legacy / Duplicate File | Responsibility | Canonical Replacement | Consolidation Action |
| :--- | :--- | :--- | :--- |
| `main_mk37.py` | Legacy monolithic startup script | `core/bootstrap.py` + `start.py` | **DELETED** (Consolidated into modular lifecycle) |
| `requirements_mk37.txt` | Unpinned legacy dependency list | `pyproject.toml` + `requirements-dev.txt` | **DELETED** (Standardized under PEP 621) |
| `actions/reminder.py` | Standalone reminder script | `tools/reminder_tools.py` | **CONSOLIDATED** (Merged into declarative schema) |
| `actions/system_cleanup.py` | Standalone cleanup script | `tools/system_tools.py` | **CONSOLIDATED** (Merged into declarative schema) |
| `actions/system_optimizer.py`| Standalone memory optimization | `tools/system_tools.py` | **CONSOLIDATED** (Merged into declarative schema) |
| `memory/contacts.enc` | Legacy encrypted contacts store | `memory/canonical_db.py` (`contacts` table) | **CONSOLIDATED** (Migrated to SQLite WAL DB) |
