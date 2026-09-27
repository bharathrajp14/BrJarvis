# BR JARVIS — FINAL TOOL & ACTION ARCHITECTURE

## 1. Architectural Invariants
1. **Single Tool Registry**: `tools/registry.py` is the single source of truth for tool schemas (`TOOL_SCHEMAS`) and execution handlers (`TOOL_REGISTRY`).
2. **Schema & Contract Requirement**: Every tool MUST define:
   - `name`: Unique snake_case identifier.
   - `description`: Clear purpose and parameters description for LLM calling.
   - `parameters`: JSON Schema specification with property types and required fields.
   - `risk_level`: Classified as `LOW` (Read-only), `MEDIUM` (Safe write in workspace), or `HIGH` (Host execution / Destructive).
   - `timeout`: Maximum execution budget (default: 30.0s).
   - `verification_handler`: Post-condition state checker in `agent/verifier.py`.
3. **Legacy Actions Deprecation**: Procedural routines in `actions/` are refactored into declarative tools in `tools/` and external connectors in `connectors/`.

---

## 2. Tool Classification & Domain Partitioning
The 81 active tools are partitioned into 8 cohesive functional domains:

| Functional Domain | Key Registered Tools | Policy Tier | Verification Method |
| :--- | :--- | :---: | :--- |
| **Filesystem & Search** | `semantic_file_search`, `read_file`, `write_file`, `list_directory`, `file_importer` | Tier 1 (Sandbox) / Tier 2 (User Docs) | `verify_file_exists()`, `verify_file_content()` |
| **Desktop & Window Control** | `live_os_control`, `focus_window`, `list_desktop_windows`, `hotkey_trigger` | Tier 2 (Confirmation on close) | `verify_window_focused()` |
| **Web & Browser Automation** | `browser_navigate`, `browser_click`, `browser_type`, `web_extractor`, `web_search` | Tier 1 (Sandbox context) | `verify_dom_element_present()`, `verify_url()` |
| **Document & PDF Processing**| `pdf_tool` (Extract, OCR, Merge, Redact, Forms), `code_refactor` | Tier 1 (Sandbox) | `verify_file_exists()`, PDF header check |
| **System & Process Telemetry**| `cli_controller`, `system_monitor`, `system_cleanup`, `system_optimizer`, `native_proc_telemetry` | Tier 3 (High-Risk Confirmation) | `verify_process_running()` |
| **Communication & Contacts** | `send_email`, `manage_contacts`, `manage_reminders`, `schedule_reminder` | Tier 2 (Prompt before send) | `verify_email_sent()`, SQLite row check |
| **Audio & Screen Streaming** | `screen_share_start`, `screen_share_stop`, `native_audio_meter`, `list_monitors` | Tier 2 | `verify_stream_active()` |
| **Security & Diagnostics** | `port_scan`, `dns_enum`, `whois_lookup`, `nmap_scan`, `generate_report` | Tier 3 (Explicit Scope Auth) | `verify_report_generated()` |
