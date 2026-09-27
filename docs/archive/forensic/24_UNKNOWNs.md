# 24 — UNKNOWNS & RESOLUTION REGISTER

## 1. Unresolved Questions & Resolution Status

### UNKNOWN 01: Is `dashboard/server.py` dynamically invoked by the desktop UI?
- **Investigation**: Static search for `dashboard.server` in `ui/` and `core/`.
- **Finding**: Not imported statically. Referenced in `brjarvis.py` as an optional background daemon command (`brjarvis web`).
- **Status**: **RESOLVED** (Standalone utility).

### UNKNOWN 02: Are files in `skills/library/` dynamically loaded at runtime?
- **Investigation**: `skills/loader.py` scans `skills/library/` on startup and parses YAML frontmatter in `SKILL.md` files.
- **Finding**: All 380+ skill markdown documents are dynamically indexed by `skills/registry.py` for contextual prompt injection.
- **Status**: **RESOLVED** (Active runtime assets).

### UNKNOWN 03: Why does `workspace/` contain 500+ browser user data files?
- **Investigation**: Inspected files in `workspace/browser_user_data/`.
- **Finding**: Artifact of Playwright / Chrome persistent context runs during web automation testing.
- **Status**: **RESOLVED** (Cache artifacts to be ignored via `.gitignore`).
