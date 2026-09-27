# UNIVERSAL EXECUTION ARCHITECTURE — BR JARVIS MK40.2

## Executive Overview

The **Universal Execution Runtime (UER)** is the central governance, resolution, execution, verification, and recovery engine of BR JARVIS MK40.2. It replaces fragmented, ad-hoc execution patterns across tools, code execution (`run_code`), sub-processes, agents, and multi-tool DAGs with a deterministic, environment-aware, dependency-aware, and verification-driven architecture.

---

## 1. Core Architectural Pipeline

Every user task and execution request proceeds through a strictly governed lifecycle:

```text
USER TASK
   ↓
UNDERSTAND (Intent & Goal Parsing)
   ↓
PLAN (Multi-Stage Decomposition / Tool DAG)
   ↓
CAPABILITY CHECK (Preflight verification)
   ↓
ENVIRONMENT CHECK (6-Tier Precedence Resolution)
   ↓
DEPENDENCY CHECK (Universal Detection & Target Env Import Verification)
   ↓
TOOL HEALTH CHECK (Active readiness validation)
   ↓
PERMISSION CHECK (Fail-Closed Policy Engine)
   ↓
EXECUTE (Process Tree Containment & Job Object)
   ↓
CAPTURE RESULT (returncode, stdout, stderr, execution_ms)
   ↓
VALIDATE RESULT (Semantic Output Contract Validation)
   ↓
VERIFY REAL-WORLD EFFECT (File / Doc / App / Window / Browser / Artifact)
   ↓
RECOVER / RETRY / REPLAN (Safe Auto-Repair under RepairPolicy)
   ↓
TASK COMPLETION GATE (Mandatory Completion Verification)
   ↓
UPDATE MEMORY / LESSONS (L6 Operational Experience Memory)
   ↓
FINAL VERIFIED RESPONSE (Truthful Evidence-Backed User Report)
```

---

## 2. Core Subsystems & Components

### 2.1 EnvironmentResolver (`core/execution/environment_resolver.py`)
Deterministic 6-tier runtime precedence engine resolving:
* **Python Runtime**: project `.venv` > repo-local > user-configured > system PATH > global fallback.
* **Node.js Runtime**: `node_modules/.bin` > system PATH.
* **Git Runtime**: system PATH.
* **PowerShell / Bash**: `pwsh` core > Windows PowerShell / `bash`.
* **Browser Runtime**: Playwright Chromium binary cache > system Chrome/Edge.

### 2.2 DependencyResolver (`core/execution/dependency_resolver.py`)
Universal machine-readable dependency engine:
* Dynamic AST-based Python import extraction.
* Import Failure Intelligence mapping import names to PyPI distributions (`fitz` → `PyMuPDF`, `docx` → `python-docx`, `cv2` → `opencv-python`, `PIL` → `pillow`, `sklearn` → `scikit-learn`, `yaml` → `PyYAML`, `bs4` → `beautifulsoup4`, `dotenv` → `python-dotenv`, `pypdf` → `pypdf`, `openpyxl` → `openpyxl`, `playwright` → `playwright`, etc.).
* Target environment import verification via subprocess execution inside the resolved runtime.

### 2.3 CapabilityChecker (`core/execution/capability_checker.py`)
Preflight capability validation before expensive multi-stage workflows:
* Code execution readiness.
* Document generation formats (DOCX, PDF, XLSX, PPTX, HTML, MD).
* Playwright & Chromium browser installation.
* Git repository status.
* Artifact workspace directory writability.

### 2.4 ProcessRunner (`core/execution/process_runner.py`)
Centralized subprocess lifecycle management:
* Windows Kernel32 Job Objects with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and memory ceilings.
* Guaranteed process-tree termination on timeout or cancellation (`taskkill /F /T /PID`).
* Virtualenv inheritance propagating `VIRTUAL_ENV`, `PATH`, `PYTHONPATH`, `PYTHONIOENCODING=utf-8`.

### 2.5 UniversalVerifier (`core/execution/verifier.py`)
Physical side-effect and output contract verifiers:
* `FileVerifier`: existence, non-zero byte size, readability.
* `DirectoryVerifier`: existence, item counts.
* `DocumentVerifier`: structural parsing of DOCX paragraphs/tables, PDF header `%PDF-` and page tree, XLSX OpenXML zip archive, JSON root structure, CSV rows.
* `ApplicationVerifier`: active process PID in OS process table (via `psutil`), visible window handles matching title on Windows (`EnumWindows`).
* `BrowserVerifier`: reachable URL, no `ERR_FILE_NOT_FOUND` / `ERR_ACCESS_DENIED`, sandbox jail containment.
* `OutputContractValidator`: semantic evaluation of stdout/stderr, detecting hidden exception traces.

### 2.6 RecoveryManager (`core/execution/recovery_manager.py`)
Automated diagnostic repair and recovery:
* Policy governance: `AUTO_REPAIR_SAFE`, `ASK_BEFORE_REPAIR`, `NO_AUTO_REPAIR`.
* Transactional package installations into resolved virtualenv (`resolved_python -m pip install ...`).
* Playwright browser component installation (`resolved_python -m playwright install chromium`).
* Bounded retries and fallback execution.

### 2.7 TaskCompletionGate (`core/execution/completion_gate.py`)
Mandatory centralized completion gatekeeper:
* Evaluates all executed steps, step outputs, artifacts on disk, and error indicators.
* Prevents the LLM from declaring a task completed unless approved by verified physical evidence.

### 2.8 ExecutionTrace (`core/execution/trace.py`)
Structured lifecycle telemetry recording every stage:
`[REQUEST] → [PLAN] → [CAPABILITY] → [ENVIRONMENT] → [DEPENDENCY] → [EXECUTION] → [VALIDATION] → [VERIFICATION] → [RECOVERY] → [GATE] → [FINAL STATUS]`.
Secret redaction for API keys and tokens.

---

## 3. Cross-Interface Consistency

The Universal Execution Runtime provides an identical execution and verification pipeline across:
* **CLI Terminal (`start.py cli`)**
* **Web UI / Fast API Server (`server.py`)**
* **Voice Assistant Engine**
* **Background Task Workers**
