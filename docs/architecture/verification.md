# Verification Contracts Architecture

## 1. Overview
In BR JARVIS, an action is never considered complete based merely on tool invocation or return strings. Every executable capability must satisfy a physical verification contract enforced by `ActionVerifier` and `UniversalVerifier`.

## 2. Verification Contract Matrix

| Capability Category | Verification Strategy | Verification Evidence Checked |
| :--- | :--- | :--- |
| **Application Launch** | `process_or_window_verifier` | Process table existence (`psutil`), window handle detection |
| **Browser Navigation** | `browser_tab_verifier` | Browser process running, URL scheme validation, no error code |
| **System Diagnostics** | `telemetry_verifier` | Non-empty telemetry dictionary with valid CPU & RAM metrics |
| **File Generation** | `file_verifier` | File path existence on disk, file size > 0 bytes, checksum |
| **Code Execution** | `output_contract_verifier` | Return code 0, standard error empty or free of fatal exceptions |
| **Subprocess Tools** | `universal_verifier` | Exit code evaluation, absence of traceback / syntax errors |

## 3. Physical State Verification Invariant
```python
# The Universal Invariant
if not verification_outcome.verified:
    record.status = "FAILED"
    record.error = verification_outcome.details
    # Dependent actions MUST NOT run
```

## 4. Re-entrant Observation and Diagnostics
Telemetry and system diagnostic actions (`"show CPU and RAM usage"`) capture actual machine states:
- Real CPU load percentage ($0.0 - 100.0\%$)
- Available and total RAM in Gigabytes
- Process ID mapping
Ensuring that data displayed to users or consumed by subsequent workflow stages is verified and accurate.
