# BR JARVIS — TOOLS FILE DISPOSITION MATRIX

## 1. Disposition Accounting (63 Files)

| Path | Final Disposition | Architectural Rationale | Callers | Replacement | Risk Level |
| :--- | :---: | :--- | :--- | :--- | :---: |
| `tools/__init__.py` | **`KEEP`** | Active registered tool module | 0 files | `tools/__init__.py` | LOW |
| `tools/agent_tools.py` | **`KEEP`** | Canonical tool architecture core component | 1 files | `tools/agent_tools.py` | LOW |
| `tools/app_analyzer_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/app_analyzer_tools.py` | LOW |
| `tools/app_connectors.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/app_connectors.py` | LOW |
| `tools/app_tracker_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/app_tracker_tools.py` | LOW |
| `tools/audit_tools.py` | **`KEEP`** | Active registered tool module | 3 files | `tools/audit_tools.py` | LOW |
| `tools/automation_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/automation_tools.py` | LOW |
| `tools/autonomous_browser_agent.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/autonomous_browser_agent.py` | LOW |
| `tools/background_monitor_tools.py` | **`KEEP`** | Active registered tool module | 0 files | `tools/background_monitor_tools.py` | LOW |
| `tools/batch_file_tool.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/batch_file_tool.py` | LOW |
| `tools/browser_agent_v2.py` | **`KEEP + IMPROVE`** | Browser automation and scraping tools | 2 files | `tools/browser_agent_v2.py` | LOW |
| `tools/browser_automation.py` | **`KEEP + IMPROVE`** | Browser automation and scraping tools | 7 files | `tools/browser_automation.py` | LOW |
| `tools/calendar_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/calendar_tools.py` | LOW |
| `tools/code_refactor_tool.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/code_refactor_tool.py` | LOW |
| `tools/code_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/code_tools.py` | LOW |
| `tools/connector_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/connector_tools.py` | LOW |
| `tools/contact_tools.py` | **`KEEP`** | Active registered tool module | 0 files | `tools/contact_tools.py` | LOW |
| `tools/custom_command_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/custom_command_tools.py` | LOW |
| `tools/doc_tools.py` | **`KEEP`** | Active registered tool module | 4 files | `tools/doc_tools.py` | LOW |
| `tools/excel_tools.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/excel_tools.py` | LOW |
| `tools/export_tools.py` | **`KEEP`** | Canonical tool architecture core component | 1 files | `tools/export_tools.py` | LOW |
| `tools/file_import_tools.py` | **`KEEP`** | Active registered tool module | 0 files | `tools/file_import_tools.py` | LOW |
| `tools/file_processor_tools.py` | **`KEEP`** | Active registered tool module | 0 files | `tools/file_processor_tools.py` | LOW |
| `tools/file_search_semantic.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/file_search_semantic.py` | LOW |
| `tools/file_tools.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/file_tools.py` | LOW |
| `tools/files.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/files.py` | LOW |
| `tools/git_repo_tool.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/git_repo_tool.py` | LOW |
| `tools/gmail_auth_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/gmail_auth_tools.py` | LOW |
| `tools/image_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/image_tools.py` | LOW |
| `tools/legacy_actions_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/legacy_actions_tools.py` | LOW |
| `tools/live_os_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/live_os_tools.py` | LOW |
| `tools/mcp_connector.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/mcp_connector.py` | LOW |
| `tools/memory_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/memory_tools.py` | LOW |
| `tools/pc_tools.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/pc_tools.py` | LOW |
| `tools/pdf_tools.py` | **`KEEP + IMPROVE`** | Document OCR and PDF manipulation suite | 1 files | `tools/pdf_tools.py` | LOW |
| `tools/proactive_listener_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/proactive_listener_tools.py` | LOW |
| `tools/process_tools.py` | **`KEEP`** | Active registered tool module | 4 files | `tools/process_tools.py` | LOW |
| `tools/qa_testing_tool.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/qa_testing_tool.py` | LOW |
| `tools/rag_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/rag_tools.py` | LOW |
| `tools/recall_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/recall_tools.py` | LOW |
| `tools/redteam_tools.py` | **`KEEP`** | Active registered tool module | 3 files | `tools/redteam_tools.py` | LOW |
| `tools/registry.py` | **`KEEP`** | Canonical tool architecture core component | 87 files | `tools/registry.py` | LOW |
| `tools/reminder_tools.py` | **`KEEP`** | Canonical tool architecture core component | 0 files | `tools/reminder_tools.py` | LOW |
| `tools/sandbox.py` | **`KEEP`** | Active registered tool module | 11 files | `tools/sandbox.py` | LOW |
| `tools/sandbox_process.py` | **`KEEP`** | Canonical tool architecture core component | 10 files | `tools/sandbox_process.py` | LOW |
| `tools/scratchpad_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/scratchpad_tools.py` | LOW |
| `tools/skills_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/skills_tools.py` | LOW |
| `tools/smart_email_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/smart_email_tools.py` | LOW |
| `tools/system_diagnostic_tool.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/system_diagnostic_tool.py` | LOW |
| `tools/system_health.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/system_health.py` | LOW |
| `tools/system_tools.py` | **`KEEP`** | Canonical tool architecture core component | 2 files | `tools/system_tools.py` | LOW |
| `tools/telegram_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/telegram_tools.py` | LOW |
| `tools/tool_ranker.py` | **`KEEP`** | Active registered tool module | 9 files | `tools/tool_ranker.py` | LOW |
| `tools/tool_runtime.py` | **`KEEP`** | Canonical tool architecture core component | 4 files | `tools/tool_runtime.py` | LOW |
| `tools/transcription_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/transcription_tools.py` | LOW |
| `tools/video_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/video_tools.py` | LOW |
| `tools/web.py` | **`KEEP`** | Active registered tool module | 3 files | `tools/web.py` | LOW |
| `tools/web_app_tools.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/web_app_tools.py` | LOW |
| `tools/web_extractor.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/web_extractor.py` | LOW |
| `tools/web_tools.py` | **`KEEP`** | Active registered tool module | 1 files | `tools/web_tools.py` | LOW |
| `tools/whatsapp_tools.py` | **`KEEP`** | Active registered tool module | 2 files | `tools/whatsapp_tools.py` | LOW |
| `tools/window_manager.py` | **`KEEP`** | Active registered tool module | 3 files | `tools/window_manager.py` | LOW |
| `tools/workspace_tools.py` | **`KEEP`** | Active registered tool module | 3 files | `tools/workspace_tools.py` | LOW |
