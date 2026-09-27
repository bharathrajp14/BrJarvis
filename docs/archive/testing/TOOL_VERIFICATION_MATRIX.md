# TOOL VERIFICATION MATRIX: BR JARVIS Capability Audit

**Date:** 2026-08-15  
**Version:** BR JARVIS MK40.2  
**Audit Scope:** All Registered Tools, Verifiers, Interfaces, and Operational Statuses  

---

## 1. Universal Capability Verification Matrix

| Capability / Domain | Tool Name(s) | Interfaces | Verifier Strategy | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Web Research** | `web_search`, `fetch_page`, `fetch_raw` | Web, CLI, Voice | `BrowserVerifier` / Content check | Response length > 0, JSON results parsed | **PASS** |
| **Repo Analysis** | `git_repo_mgr`, `file_read`, `file_list` | Web, CLI, Voice | `FileVerifier` / `GitVerifier` | File existence, non-zero bytes, branch parse | **PASS** |
| **DOCX Generation** | `create_word_document`, `document_creator` | Web, CLI, Voice | `FileVerifier.verify_file_parsed` | Python-DOCX paragraph/table extraction | **PASS** |
| **PDF Generation** | `create_pdf_document`, `pdf_create` | Web, CLI, Voice | `FileVerifier.verify_file_parsed` | PDF `%PDF-` magic header & binary size | **PASS** |
| **Excel Analysis** | `excel_analyze`, `openpyxl` | Web, CLI, Voice | `FileVerifier.verify_file_parsed` | OpenXML ZIP archive & sheet validation | **PASS** |
| **Walkthrough Builder**| `generate_walkthrough` | Web, CLI, Voice | `FileVerifier.verify_file_content` | Markdown heading & diff verification | **PASS** |
| **App Launching** | `open_app`, `launch_app` | Web, CLI, Voice | `ApplicationVerifier` | Process PID active & Win32 window visible | **PASS** |
| **Browser Control** | `browser_open_url`, `open_browser` | Web, CLI, Voice | `BrowserVerifier` | No `ERR_FILE_NOT_FOUND`, host path check | **PASS** |
| **Screen Vision** | `screen_find`, `screen_click` | Web, CLI, Voice | `ApplicationVerifier` | Desktop screen resolution & coordinates | **PASS** |
| **OS Controls** | `computer_settings` | Web, CLI, Voice | `CommandVerifier` | OS volume/brightness setting applied | **PASS** |
| **Code Execution** | `run_code`, `scratchpad_eval` | Web, CLI, Voice | `CommandVerifier` | Subprocess return code 0, stdout capture | **PASS** |
| **Artifact Export** | `artifact_export`, `artifact_list` | Web, CLI, Voice | `ArtifactVerifier` | SHA-256 hash match, user read permissions | **PASS** |
| **Hierarchical Memory**| `memory_save`, `memory_search`, `remember` | Web, CLI, Voice | State assertion | SQLite row count, ChromaDB recall | **PASS** |
| **System Telemetry** | `system_diagnostic`, `system_health` | Web, CLI, Voice | Telemetry validator | CPU/RAM/Disk metrics parsed | **PASS** |
| **Telegram Connect** | `send_telegram`, `manage_telegram` | Web, CLI, Voice | Connector check | Bot token configured & API ping | **PASS** |
| **Gmail Connect** | `send_email`, `gmail_login` | Web, CLI, Voice | Connector check | OAuth credential existence (`credentials.json`) | **PASS** |
| **WhatsApp Connect** | `send_whatsapp`, `schedule_whatsapp` | Web, CLI, Voice | Connector check | Web launcher available, QR pairing standby | **STANDBY** |

---

## 2. Verifier Strategy Matrix

| Verifier Name | Target Resource | Pass Criteria | Fail Criteria |
| :--- | :--- | :--- | :--- |
| **`FileVerifier`** | Local Files, Reports, Scripts | File exists, size >= min_bytes, readable by user | Missing file, 0 bytes, permission denied |
| **`FileVerifier.verify_file_parsed`** | `.docx`, `.pdf`, `.xlsx`, `.json` | Document structure extracted without parse exception | Corrupt archive, zero paragraphs, missing header |
| **`ApplicationVerifier`** | OS Processes & Applications | Target PID in process table OR window detected | Process not found, launch exception |
| **`BrowserVerifier`** | URLs, Local HTML Artifacts | Host artifact exists, zero error patterns in response | Sandbox path leak, `ERR_FILE_NOT_FOUND` |
| **`ArtifactVerifier`** | Exported Artifacts | Target in host directory, SHA-256 integrity match | Unexported artifact, checksum mismatch |
| **`GitVerifier`** | Git Repositories | Git binary available, clean or committed working tree | Non-git directory, merge conflict error |
| **`CommandVerifier`** | Shell & CLI Scripts | Return code 0, clean stdout without traceback | Non-zero exit code, unhandled exception |

---

## 3. Tool Health Diagnostic Command

To verify real-time status of all capabilities at any moment:
```pwsh
python -c "from tools.registry import execute_tool; print(execute_tool('system_diagnostic', {'aspect': 'tool_health'}))"
```

To run safe end-to-end self-tests:
```pwsh
python -c "from tools.registry import execute_tool; print(execute_tool('system_diagnostic', {'aspect': 'self_test'}))"
```
