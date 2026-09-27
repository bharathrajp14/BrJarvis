# EXECUTION VERIFICATION AUDIT — BR JARVIS MK40.2

## 1. Physical Side-Effect Verification Suite

BR JARVIS MK40.2 mandates that execution success is never inferred solely from exit codes, empty stderr, or optimistic tool returns. Every action must be corroborated with physical real-world evidence.

---

## 2. Verifier Taxonomy

### 2.1 File & Directory Verifier (`FileVerifier`, `DirectoryVerifier`)
* **Verification Criteria**:
  - File exists at the absolute/relative host destination path.
  - File size > 0 bytes (`st_size > 0`).
  - Read permissions verified (`os.access(p, os.R_OK)`).
  - Directory exists and contains expected files.
* **Failure Classifications**: `FILE_NOT_FOUND`, `FILE_EMPTY`, `PERMISSION_DENIED`.

### 2.2 Document Structural Verifier (`DocumentVerifier`)
* **DOCX Documents**:
  - Valid ZIP archive format with `word/document.xml`.
  - Parsed with `python-docx` verifying > 0 paragraphs or tables.
* **PDF Documents**:
  - Starts with valid magic bytes `%PDF-`.
  - Parsed with `pypdf` or `PyMuPDF` verifying page tree contains $\ge 1$ readable pages.
* **XLSX Spreadsheets**:
  - Valid OpenXML ZIP archive with `xl/workbook.xml`.
  - Parsed with `openpyxl` verifying non-empty sheet structure.
* **JSON / CSV Documents**:
  - JSON parses without `json.JSONDecodeError`.
  - CSV contains valid delimiter-separated rows.

### 2.3 Application & Window Verifier (`ApplicationVerifier`)
* **Process Table Check**:
  - Queries OS process table via `psutil` verifying active PID.
* **Window Handle Matching (Windows)**:
  - Calls `kernel32` and `user32.EnumWindows` to confirm window title matches the launched application or document.

### 2.4 Browser & Web Verifier (`BrowserVerifier`)
* **Reachable Destination**:
  - Confirms target URL or local HTML file exists.
  - Verifies no `ERR_FILE_NOT_FOUND`, `ERR_ACCESS_DENIED`, or `ERR_LOAD_FAILED`.
* **Sandbox Containment**:
  - Rejects browser opening internal ephemeral sandbox jail paths (`SANDBOX_PATH_EXPOSURE`).

### 2.5 Semantic Output Contract Validator (`OutputContractValidator`)
* **Silent Error Detection**:
  - Scans stdout/stderr for Python tracebacks, `ModuleNotFoundError`, `ImportError`, `ZeroDivisionError`, `UnboundLocalError`, `SyntaxError`, `PermissionError`, or structured failure payloads (`"status": "failure"`).
  - Prevents processes exiting with code 0 from falsely claiming success when an exception was printed.
