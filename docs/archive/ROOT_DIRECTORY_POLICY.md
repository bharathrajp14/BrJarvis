# ROOT DIRECTORY POLICY & GOVERNANCE RULES: BR JARVIS MK40.2+

## 1. Absolute Rule
The root directory of the BR JARVIS repository MUST remain clean, uncluttered, and strictly limited to canonical entry points and repository metadata.

---

## 2. Permitted Root Items

### Version-Controlled Metadata Files
- `README.md` — Authoritative project README
- `LICENSE` — Project open source license
- `pyproject.toml` — Standard packaging configuration
- `setup.py` — Backward-compatible packaging script
- `pytest.ini` — Pytest runner configuration
- `pyrightconfig.json` — Pyright static analysis configuration
- `requirements.txt` — Production dependencies
- `requirements-dev.txt` — Development dependencies
- `.env.template` — Environment variable template
- `.gitignore` — Git exclusion manifest

### Version-Controlled Top-Level Directories
- `.github/` — GitHub workflows and CI/CD actions
- `.vscode/` — VSCode editor configuration
- `src/` — Canonical source code package root (`src/brjarvis/`)
- `apps/` — Application runner entrypoints
- `config/` — Declarative configurations and schemas
- `docs/` — System documentation and audit reports
- `scripts/` — Maintenance, migration, and build scripts
- `tests/` — Automated test suites
- `assets/` — Templates and static resources
- `runtime/` — Isolated runtime execution data (Git-ignored)
- `workspace/` — Isolated user workspace (Git-ignored)

### Canonical Backward-Compatible Launcher Shims
- `start.py` — Canonical system bootstrap & interactive launcher
- `brjarvis.py` — Canonical unified CLI launcher
- `main.py` — Legacy execution entrypoint
- `server.py` — Canonical FastAPI server entrypoint
- `ui.py` — UI package entrypoint shim
- `ui_mark.py` — Cyberpunk HUD entrypoint shim
- `float_widget.py` — Floating HUD widget shim
- `permissions.py` — Security engine compatibility shim
- `setup_native.py` — Native builder wrapper shim
- `brjarvis.bat` / `jarvis.bat` — Windows terminal launcher scripts
- `setup_env.bat` / `setup_linux.sh` / `startup.bat` — Environment bootstrap scripts

---

## 3. Forbidden Root Items
- No random `.md` audit/analysis files (all belong in `docs/architecture/` or `docs/audits/`).
- No runtime logs (`*.log` belongs in `runtime/logs/`).
- No screen captures (`*.png`, `*.jpg` belong in `runtime/captures/`).
- No SQLite databases (`*.db`, `*.sqlite3` belong in `runtime/state/`).
- No generated output deliverables (`*.pdf`, `*.docx`, `*.xlsx` belong in `runtime/artifacts/` or `workspace/`).
- No scratchpad scripts (`runtime/temporary/`).
