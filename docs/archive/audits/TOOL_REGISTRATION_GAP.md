# TOOL REGISTRATION GAP AUDIT REPORT

**Audit Objective:** Identify capabilities that exist in source code files but were omitted from the universal tool registry or lazy loading maps.

## 1. Unregistered Tool Modules Discovered & Repaired

The following 8 tool modules (containing 22 decorated tools) existed in `tools/` with `@register_tool` decorators but were missing from `registry.py` plugin loader lists:

| Module | Tools Implemented | Purpose / Capability | Root Cause | Status |
| :--- | :--- | :--- | :--- | :--- |
| `tools.background_monitor_tools` | `add_background_monitor`, `remove_background_monitor`, `list_monitored_topics`, `check_monitored_topics` | Background topic and news monitoring | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.connector_tools` | `connector_status`, `connector_call`, `connector_search`, `connector_add_mcp`, `connector_list_tools` | Gateway to `connectors/hub.py` (GitHub, Slack, Notion, Weather, YouTube, RSS, etc.) | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.contact_tools` | `import_contacts`, `manage_contacts`, `resolve_contact` | Mobile vCard (.vcf) & CSV contact management & alias resolution | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.file_import_tools` | `import_file_to_knowledge` | Universal document ingestion into persistent knowledge memory | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.file_processor_tools` | `process_universal_file` | Multi-format file OCR, extraction, and transformation | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.recall_tools` | `remember_that` | Voice/text note capture with 3D Knowledge Galaxy indexing | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.reminder_tools` | `schedule_reminder`, `manage_reminders` | OS-native smart reminder scheduling and toast alerts | Omitted from `extended_plugins` list | **REPAIRED** |
| `tools.scratchpad_tools` | `scratchpad_write`, `scratchpad_read`, `scratchpad_eval`, `scratchpad_list`, `scratchpad_clear` | Dynamic code scratchpad execution and inspection | Omitted from `extended_plugins` list | **REPAIRED** |

## 2. Lazy Loading and Intent Pruning Map Gaps

In `tools/registry.py`, `get_pruned_tool_prompt_block()` uses `keyword_to_plugins` and `domain_map` to filter tools provided to LLMs. The following domain mappings were missing or incomplete:
- Contact management (`contact`, `vcf`, `phone`, `mobile`)
- External Connectors (`connector`, `hub`, `notion`, `slack`, `rss`, `wikipedia`)
- Reminders & Alarms (`reminder`, `alarm`, `notify`)
- Code Scratchpad (`scratchpad`, `scratch`)
- Background Topic Monitoring (`monitor`, `topics`, `news_check`)

These have all been synchronized to ensure the LLM receives the correct schema in both full and intent-pruned modes.