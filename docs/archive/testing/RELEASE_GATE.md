# BR JARVIS MK40.2 — Production Release Gate & Quality Policy

## 1. Automated Acceptance Criteria
No release or deployment candidate is authorized unless all of the following conditions pass:

```
[✓] 1. Pytest Full Suite Clean Pass (0 failures, 0 unexpected errors)
[✓] 2. Startup Smoke Acceptance Pass (start.py, start.py cli, start.py doctor, start.py web)
[✓] 3. Zero Circular Imports (Verified across all 15 core subsystems)
[✓] 4. Security Sandbox Fail-Closed (All hostile escape & traversal attempts blocked)
[✓] 5. Doctor Diagnostic Audit Healthy (Environment & dependencies validated)
[✓] 6. Cross-Task Isolation Verified (Zero context leakage under concurrency)
[✓] 7. Physical Verification Compliance (TaskCompletionGate rejecting unverified claims)
```

## 2. Release Gate Execution Commands
To evaluate a candidate build against the Release Gate:

```bash
# 1. Run Complete Automated Test Suite
.\.venv\Scripts\python.exe -m pytest -v

# 2. Run Startup Smoke Gate
.\.venv\Scripts\python.exe -m pytest tests/smoke/ -v

# 3. Run Truth Level & Isolation Invariants
.\.venv\Scripts\python.exe -m pytest tests/unit/test_contract_truth_levels.py tests/unit/test_cross_task_isolation.py -v

# 4. Run Doctor Diagnostic Audit
.\.venv\Scripts\python.exe start.py doctor
```
