# WINDOWS APPLICATION LAUNCH AUDIT — BR JARVIS MK40.2

## 1. Native Windows Launch Strategy

Launching applications and documents on Windows requires handling a diverse matrix of input forms:
1. **Host Executables**: `notepad.exe`, `chrome.exe`, `code.cmd`, `powershell.exe`.
2. **Associated Documents**: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.html`, `.png`, `.jpg`.
3. **Complex Paths**: Spaces (`C:\Program Files\...`), parentheses (`Report (Final).pdf`), Unicode characters, and relative paths.

### Multi-Level Application State Machine:
```text
LAUNCH_NOT_ATTEMPTED
        ↓
LAUNCH_REQUESTED
        ↓
PROCESS_STARTED (PID allocated in OS process table)
        ↓
WINDOW_FOUND (Visible HWND detected via EnumWindows)
        ↓
APPLICATION_READY (Main window handle responsive)
        ↓
DOCUMENT_LOADED (Window title contains document filename)
        ↓
OPEN_VERIFIED (Physical verification complete)
        ↓ (or on failure)
OPEN_FAILED
```

---

## 2. Windows-Specific Invocation Implementation

In `actions/open_app.py`:
- Target paths are normalized and resolved to absolute Windows paths.
- For files with associated applications, `os.startfile(str(p.resolve()))` is invoked, falling back to `ctypes.windll.shell32.ShellExecuteW(None, "open", str(p.resolve()), None, None, 1)`.
- Non-zero return codes ($>32$) verify OS dispatch.
- Verification polls `ctypes.windll.user32.EnumWindows` to confirm window title matches the document stem or basename.
- If window is not found after polling latency, returns `[SUCCESS_UNVERIFIED]`, ensuring `TaskCompletionGate` marks the task `PARTIAL_SUCCESS` and does not claim false verification.
