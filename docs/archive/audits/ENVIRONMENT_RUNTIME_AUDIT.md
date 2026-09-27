# ENVIRONMENT RUNTIME AUDIT — BR JARVIS MK40.2

## 1. Multi-Tier Environment Resolution Hierarchy

BR JARVIS enforces a deterministic 6-tier precedence hierarchy for locating and activating runtimes:

```text
Tier 1: Explicit Task Configuration (task.runtime_path)
   ↓
Tier 2: Project Virtualenv (.venv/Scripts/python.exe)
   ↓
Tier 3: Active Process sys.executable
   ↓
Tier 4: Tool-Specific Isolated Environment (.jarvis_tools_env)
   ↓
Tier 5: System PATH Binary (shutil.which)
   ↓
Tier 6: Fallback Default Executable
```

---

## 2. Virtualenv Isolation & Package Preservation

### The Historical `-I` Sandbox Flaw:
Running `python.exe -I -c "import docx"` disables `sys.path` site-packages inheritance, preventing installed packages in `.venv\Lib\site-packages` from loading.

### MK40.2 Resolution:
`EnvironmentResolver` generates sanitized environment variables with `PYTHONPATH` explicitly targeting the resolved virtualenv's `site-packages`, while filtering out hazardous external process injection tokens (`PYTHONSTARTUP`, `PYTHONHOME`). Subprocesses inherit full access to required libraries:
- `pypdf`, `pymupdf` (fitz)
- `python-docx`
- `openpyxl`
- `playwright`
- `pillow`
- `reportlab`
- `pytest`
