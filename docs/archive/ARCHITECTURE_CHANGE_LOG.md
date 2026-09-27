# BR JARVIS — ARCHITECTURE CHANGE CONTROL LOG

## 1. Architecture Change Ledger

| Change ID | Old Design | Forensic Evidence | Problem | New Target Design | Impact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **ACC-01** | Tool execution return value directly mapped to `TaskStatus.COMPLETED`. | Forensic audit found 27 sites returning unverified success. | False success responses presented to users when real action failed. | `TaskStatus.COMPLETED` strictly requires `ActionVerifier.verify_action() == True`. | Prevents false-positive completions across all workflows. | **APPROVED** |
| **ACC-02** | `sandbox_path` passed to `webbrowser.open()` without host export check. | Browser threw `ERR_FILE_NOT_FOUND` on unexported virtual paths. | Host browser cannot access sandboxed memory paths. | Mandatory `ensure_host_artifact()` export with SHA256 verification before browser launch. | Permanently eliminates `ERR_FILE_NOT_FOUND` regression. | **APPROVED** |
| **ACC-03** | DXGI capture physical pixels passed directly to Win32 `SendInput`. | Click offset on 125%/150% DPI Windows displays. | Mouse clicks miss button target centers on high-DPI monitors. | Centralized DPI scale transform applied in `computer/operator.py`. | Accurate UI element interaction across all monitor resolutions. | **APPROVED** |
| **ACC-04** | Gateway threw fatal error on provider 429 quota exhaustion. | "All backends failed" error message when primary cloud key was exhausted. | Single provider failure collapsed entire cognitive plan. | Automatic mid-flight failover to secondary cloud or local Ollama profile. | High-availability cognitive routing with graceful degradation. | **APPROVED** |
