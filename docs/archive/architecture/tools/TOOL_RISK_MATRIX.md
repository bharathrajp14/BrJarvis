# BR JARVIS — Tool Risk & Governance Matrix

**Document Version:** MK40.2 / MK41 Canonical Rebuild  
**Classification:** Security & Risk Architecture  
**Status:** Canonical Reference  

---

## 1. Risk Tier Definitions

| Risk Tier | Definition | Default Permission | Approval Policy | Retries Allowed | Rollback Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LOW** | Pure computational, read-only queries, local search, non-mutating inspections. | `PUBLIC_READ` / `ALLOW` | Auto-approved | Yes (Max 3) | None needed |
| **MEDIUM** | Non-destructive local mutations (e.g. creating files in workspace, writing cache, setting app focus). | `USER_WRITE` / `ALLOW` | Auto-approved in standard mode | Yes (With state check) | File deletion / revert |
| **HIGH** | External communications, code execution in sandbox, OS process kills, setting changes, file overwrites. | `LOCAL_SYSTEM` / `EXTERNAL_COMMUNICATION` | Requires user confirmation if interactive | Conditional (Max 1) | Re-launch / compensatory action |
| **CRITICAL** | System shutdown/reboot, permanent file deletion, external irreversible submissions, secret modifications. | `DESTRUCTIVE` / `PRIVILEGED_SYSTEM` | Mandatory User Approval Interlock | No blind retries | Documented compensation / manual repair |

---

## 2. Canonical Tool Risk & Governance Matrix

| Tool Identifier | Canonical Namespace | Category | Risk Level | Side Effect Level | Permission Required | Approval Required | Idempotent | Verification Strategy | Rollback Available |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `file_read` | `filesystem.read` | Filesystem | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `FILE_EXISTS` | N/A |
| `file_write` | `filesystem.write` | Filesystem | **MEDIUM** | `LOCAL_MUTATION` | `USER_WRITE` | No | Yes (Atomic) | `FILE_CONTENT` | Revert backup |
| `file_list` | `filesystem.list` | Filesystem | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `FILE_EXISTS` | N/A |
| `file_delete` | `filesystem.delete` | Filesystem | **HIGH** | `DESTRUCTIVE` | `USER_WRITE` | Yes (if permanent) | Yes | `FILE_ABSENT` | Restore from trash |
| `file_search` | `filesystem.search` | Filesystem | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `browser_open_url` | `browser.open` | Browser | **LOW** | `LOCAL_MUTATION` | `PUBLIC_READ` | No | Yes | `BROWSER_DOM` | Close page |
| `browser_click` | `browser.click` | Browser | **MEDIUM** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | No | `BROWSER_DOM` | Backward navigation |
| `browser_type` | `browser.type` | Browser | **MEDIUM** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | Yes | `BROWSER_DOM` | Clear field |
| `browser_extract` | `browser.extract` | Browser | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `browser_screenshot` | `browser.screenshot`| Browser | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `FILE_EXISTS` | N/A |
| `web_search` | `web.search` | Web | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `fetch_page` | `web.fetch` | Web | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `fetch_raw` | `web.fetch_raw` | Web | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `cursor_move` | `desktop.cursor_move`| Desktop | **LOW** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | Yes | `READ_BACK_VALUE` | Move back |
| `cursor_click` | `desktop.click` | Desktop | **MEDIUM** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | No | `WINDOW_ACTIVE` | None |
| `keyboard_type` | `desktop.type` | Desktop | **MEDIUM** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | No | `READ_BACK_VALUE` | Backspace |
| `screen_find` | `desktop.screen_find`| Desktop | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `screen_capture` | `desktop.capture` | Desktop | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `FILE_EXISTS` | N/A |
| `computer_settings` | `system.settings` | System | **HIGH** | `LOCAL_MUTATION` | `PRIVILEGED_SYSTEM`| Yes (Dangerous) | Yes | `READ_BACK_VALUE` | Restore setting |
| `open_app` | `system.open_app` | System | **LOW** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | Yes | `PROCESS_RUNNING` | Close app |
| `cli_controller` | `system.cli` | System | **HIGH** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | No | `PROCESS_RUNNING` | Kill process |
| `send_email` | `communication.email`| Communication | **HIGH** | `EXTERNAL_WRITE` | `EXTERNAL_COMMUNICATION`| Yes (External) | Yes (Idempotency Key)| `NETWORK_RESPONSE`| None (Sent) |
| `send_whatsapp` | `communication.whatsapp`| Communication | **HIGH** | `EXTERNAL_WRITE` | `EXTERNAL_COMMUNICATION`| Yes (External) | Yes (Idempotency Key)| `NETWORK_RESPONSE`| None (Sent) |
| `create_calendar_event`| `calendar.create`| Calendar | **MEDIUM** | `EXTERNAL_WRITE` | `USER_WRITE` | No | Yes (Event ID) | `READ_BACK_VALUE` | Delete event |
| `run_code` | `code.run` | Code | **HIGH** | `LOCAL_MUTATION` | `LOCAL_SYSTEM` | No | No | `PROCESS_RUNNING` | Sandbox teardown |
| `create_word_document`| `document.create_word`| Document | **LOW** | `LOCAL_MUTATION` | `USER_WRITE` | No | Yes (Atomic) | `FILE_PARSED` | Delete document |
| `create_pdf_document`| `document.create_pdf`| Document | **LOW** | `LOCAL_MUTATION` | `USER_WRITE` | No | Yes (Atomic) | `FILE_PARSED` | Delete document |
| `memory_save` | `memory.save` | Memory | **LOW** | `LOCAL_MUTATION` | `USER_WRITE` | No | Yes | `READ_BACK_VALUE` | Delete memory |
| `memory_get` | `memory.get` | Memory | **LOW** | `READ_ONLY` | `PUBLIC_READ` | No | Yes | `NONE` | N/A |
| `memory_delete` | `memory.delete` | Memory | **MEDIUM** | `LOCAL_MUTATION` | `USER_WRITE` | No | Yes | `READ_BACK_VALUE` | Re-insert backup |
| `system_shutdown` | `system.shutdown` | System | **CRITICAL**| `IRREVERSIBLE` | `DESTRUCTIVE` | **Mandatory** | No | `NONE` | None |
