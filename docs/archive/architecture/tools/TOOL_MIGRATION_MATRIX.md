# BR JARVIS — Tool Migration Matrix

**Document Version:** MK40.2 / MK41 Canonical Rebuild  
**Classification:** Migration & Compatibility Reference  
**Status:** Authoritative  

---

## 1. Tool Migration Overview

All legacy tools, flat names, and ambiguous wrappers are migrated to the Canonical Tool Runtime. Legacy aliases remain fully supported through semantic routing.

---

## 2. Exhaustive Tool Migration Mapping

| Legacy Name | Canonical Tool Name | Namespace | Old Provider | New Canonical Provider | Schema Changes | Behavior & Verification Changes | Migration Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `file_read` | `file_read` | `filesystem.read` | `tools.file_tools` | `tools.file_tools` | Added path normalization & bounds | Returns structured content, size, and encoding | **MIGRATED** |
| `file_write` | `file_write` | `filesystem.write` | `tools.file_tools` | `tools.file_tools` | Added overwrite & encoding flags | Atomic write via tempfile, SHA-256 hash check, verified size | **MIGRATED** |
| `file_list` | `filesystem.list` | `filesystem.list` | `tools.file_tools` | `tools.file_tools` | Added recursive & pattern filters | Returns structured directory entry list with types and sizes | **MIGRATED** |
| `file_delete` | `file_delete` | `filesystem.delete`| `tools.file_tools` | `tools.file_tools` | Added `trash` bool flag | Soft delete by default; checks file absence post-delete | **MIGRATED** |
| `file_controller` | `file_write` / `read` / `list` | `filesystem.*` | `tools.legacy_actions_tools` | Semantic Dispatch | Deprecated umbrella tool | Routes to specific atomic filesystem tools | **ADAPTED** |
| `browser_control` | `browser_open_url` | `browser.open` | `tools.registry` (Lossy rewrite) | `tools.browser_automation` | Strict URL validation | Replaced lossy Chrome launch with real Playwright session | **MIGRATED** |
| `browser_open_url`| `browser_open_url` | `browser.open` | `tools.browser_automation` | `tools.browser_automation` | Added wait_until & headless | Verified DOM navigation, checks for error screens | **MIGRATED** |
| `browser_click` | `browser_click` | `browser.click` | `tools.browser_automation` | `tools.browser_automation` | Strict selector & text target | Verifies DOM mutation post-click | **MIGRATED** |
| `browser_type` | `browser_type` | `browser.type` | `tools.browser_automation` | `tools.browser_automation` | Added clear_first & press_enter | Verifies field value populated in DOM | **MIGRATED** |
| `web_search` | `web_search` | `web.search` | `tools.web_tools` | `tools.web_tools` | Added max_results & freshness | Returns structured search records (title, URL, snippet) | **MIGRATED** |
| `fetch_page` | `fetch_page` | `web.fetch` | `tools.web_tools` | `tools.web_tools` | Added selector & clean_text | Distinguishes HTTP errors, empty content, extraction | **MIGRATED** |
| `open_app` | `open_app` | `system.open_app` | `tools.legacy_actions_tools` | `actions.open_app` | Added url & wait_active | Verifies running process PID & active window handle | **MIGRATED** |
| `computer_settings`| `computer_settings`| `system.settings` | `tools.legacy_actions_tools` | `actions.computer_settings` | Strict action enums & values | Read-back verification for volume, brightness, wifi | **MIGRATED** |
| `system_control` | `computer_settings`| `system.settings` | `tools.registry` (Rewrite) | Semantic Dispatch | Deprecated umbrella tool | Preserves original parameter semantics | **ADAPTED** |
| `screen_process` | `screen_capture` / `screen_find` | `desktop.screen` | `tools.legacy_actions_tools` | `actions.screen_processor` | Added analysis & prompt | Returns actual analysis text and confidence | **MIGRATED** |
| `send_email` | `send_email` | `communication.email` | `tools.smart_email_tools` | `actions.smart_email_sender`| Added idempotency_key | Distinguishes DRAFTED, QUEUED, SENT; duplicate protection | **MIGRATED** |
| `send_whatsapp` | `send_whatsapp` | `communication.whatsapp`| `tools.whatsapp_tools` | `actions.whatsapp_automation`| Added idempotency_key | Tracks PREPARED vs SENT; no false delivery claims | **MIGRATED** |
| `create_calendar_event`| `create_calendar_event`| `calendar.create` | `tools.calendar_tools` | `actions.calendar_engine` | Added event_id & recurrence | Read-back event verification; duplicate prevention | **MIGRATED** |
| `run_code` | `run_code` | `code.run` | `tools.code_tools` | `tools.sandbox` | Added cwd & resource limits | Structured output (stdout, stderr, exit_code, artifacts) | **MIGRATED** |
| `create_word_document`| `create_word_document`| `document.create_word`| `tools.doc_tools` | `tools.doc_tools` | Added template & styling options | Verifies .docx ZIP integrity & paragraph counts | **MIGRATED** |
| `create_pdf_document` | `create_pdf_document` | `document.create_pdf` | `tools.doc_tools` | `tools.doc_tools` | Added title, author, formatting | Verifies PDF magic header `%PDF-` & size > 0 | **MIGRATED** |
| `memory_save` | `memory_save` | `memory.save` | `tools.memory_tools` | `memory.unified_memory` | Added namespace & taxonomy | Routes via canonical memory service; invalidates cache | **MIGRATED** |
| `memory_get` | `memory_get` | `memory.get` | `tools.memory_tools` | `memory.unified_memory` | Added scope filter | Returns typed memory entity | **MIGRATED** |
| `memory_delete` | `memory_delete` | `memory.delete` | `tools.memory_tools` | `memory.unified_memory` | Added confirmation flag | Read-back verification of memory deletion | **MIGRATED** |
