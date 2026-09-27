# RUNTIME RESOLUTION AUDIT — BR JARVIS MK40.2

## 1. Environment Selection Precedence Policy

BR JARVIS enforces a strict, deterministic 6-tier precedence hierarchy for resolving execution environments. No tool or command is executed without knowing the exact target executable and environment profile.

| Tier | Source | Description | Precedence Level |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `Explicit Configuration` | Explicit path passed in task/step arguments or API payload | Highest |
| **Tier 2** | `Project-Local Environment` | Project `.venv` (`.venv/Scripts/python.exe`), `node_modules/.bin` | Primary Project Bound |
| **Tier 3** | `Repository-Local Executables` | Repository `bin/` or `Scripts/` folder | Secondary Project Bound |
| **Tier 4** | `User Configuration` | Environment variables (`JARVIS_PYTHON_PATH`, `.env`) | User Override |
| **Tier 5** | `System Environment` | System PATH resolution (`shutil.which`, `py -3.12`) | Global Standard |
| **Tier 6** | `Global Fallback` | `sys.executable` (recorded in telemetry as fallback) | Fail-Safe Fallback |

---

## 2. Multi-Runtime Resolution Matrix

### Python Runtime
* **Resolved Path**: `d:\BRJARVIS\Br-Jarvis\.venv\Scripts\python.exe`
* **Python Version**: Python 3.12.10
* **Isolation Flags**: No `-I` flag that breaks project packages.
* **Environment Variables**: Propagates `VIRTUAL_ENV`, `PATH` with virtualenv scripts prepended, `PYTHONPATH` with project root, `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`.

### Node.js Runtime
* **Resolution**: Project `node_modules/.bin/node.cmd` > System `node.exe`.

### Git Runtime
* **Resolution**: System `git.exe` with repository directory validation.

### PowerShell / Bash
* **Resolution**: `pwsh` (PowerShell Core 7+) > `powershell.exe` (Windows PowerShell 5.1).

### Browser Automation Runtime
* **Resolution**: Playwright Chromium Cache (`AppData/Local/ms-playwright/chromium-*`) > System Chrome / Edge.

---

## 3. Project Environment Multi-Tenancy

When operating on an external project:
1. `EnvironmentResolver` resolves the environment relative to the target project's root path.
2. If the target project contains its own `.venv` or `node_modules`, executions for that project target its local runtime.
3. System Python or global fallbacks are never silently substituted without explicit warning records.
