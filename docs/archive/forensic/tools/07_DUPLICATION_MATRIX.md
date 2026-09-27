# BR JARVIS — TOOL DUPLICATION & OVERLAP ANALYSIS

## 1. Overlapping Capability Matrix

| Feature Domain | Discovered Tools / Scripts | Relationship | Canonical Retained Tool | Action |
| :--- | :--- | :---: | :--- | :--- |
| **Reminders** | `tools/reminder_tools.py`, `actions/reminder.py`, `actions/reminders.py` | TRUE DUPLICATE | `tools/reminder_tools.py` (`schedule_reminder`, `manage_reminders`) | Procedural scripts merged into tool |
| **System Cleanup** | `tools/system_tools.py`, `actions/system_cleanup.py`, `actions/system_optimizer.py` | TRUE DUPLICATE | `tools/system_tools.py` (`system_cleanup`, `system_optimizer`) | Procedural scripts merged into tool |
| **Browser Control** | `tools/browser_automation.py`, `actions/browser_control.py`, `actions/web_search.py` | OVERLAPPING | `tools/browser_automation.py` + `connectors/web_search.py` | Unified under declarative browser tool |
| **File Operations** | `tools/filesystem_tools.py`, `actions/file_processor.py`, `tools/semantic_file_search.py` | COMPLEMENTARY | `tools/filesystem_tools.py` + `tools/semantic_file_search.py` | Actions refactored into declarative tools |
| **PDF Processing** | `tools/pdf_tools.py`, `actions/pdf_analyzer.py` | TRUE DUPLICATE | `tools/pdf_tools.py` (`pdf_tool`) | Unified single tool handler |
