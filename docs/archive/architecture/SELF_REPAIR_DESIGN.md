# SELF-REPAIR & RUNTIME RECOVERY DESIGN — BR JARVIS MK40.2

## 1. Automated Repair Architecture

The **Recovery Manager** (`core/execution/recovery_manager.py`) provides safe, transactional automated runtime healing for execution failures.

```text
EXECUTION FAILURE / EXCEPTION
             ↓
DIAGNOSE FAILURE (Regex & AST Pattern Matcher)
             ↓
CHECK REPAIR POLICY (AUTO_REPAIR_SAFE / ASK_BEFORE_REPAIR / NO_AUTO_REPAIR)
             ↓
CONSTRUCT REPAIR ACTION (Target Virtualenv Pip Command / Playwright Install)
             ↓
EXECUTE TRANSACTIONAL REPAIR (Subprocess in target environment with timeout)
             ↓
VERIFY REPAIR (Target environment test import)
             ↓
RETRY ORIGINAL TASK (Bounded retry: max 2 attempts)
             ↓
IF REPAIR FAILS -> DEGRADE SAFELY & REPORT ROOT CAUSE
```

---

## 2. Policy Governance

1. **`AUTO_REPAIR_SAFE` (Default)**:
   - Permitted: Installing missing PyPI packages into the target project virtualenv (`resolved_python -m pip install <pkg>`), installing missing Playwright browser binaries (`resolved_python -m playwright install chromium`), creating missing output directories.
   - Prohibited: Modifying global system files, altering system PATH, removing user files.
2. **`ASK_BEFORE_REPAIR`**:
   - Requires explicit user confirmation prior to any package installation or browser download.
3. **`NO_AUTO_REPAIR`**:
   - Strictly reports the error and suggests the exact manual repair command.

---

## 3. Transactional Bounded Retries

* Maximum retry count per step: `2 attempts`.
* Prevents infinite loops or cyclic failure storms.
* Every repair attempt is logged to the `ExecutionTrace` with duration, return code, and verification status.
