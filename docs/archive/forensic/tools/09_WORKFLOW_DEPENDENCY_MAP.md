# BR JARVIS — REAL-WORLD WORKFLOW TOOL DEPENDENCY MAP

## 1. Critical Workflow Tool Dependencies

| User Workflow Domain | Primary Tools Invoked | Fallback / Recovery Tools | Security Tier |
| :--- | :--- | :--- | :---: |
| **Voice Command Dialogue** | `manage_reminders`, `system_health`, `get_weather` | Fast-path regex heuristics | `TIER_0` / `TIER_1` |
| **Autonomous Screen Research**| `browser_navigate`, `web_extractor`, `web_search` | Optical screenshot + VLM | `TIER_0` |
| **Document & PDF Analysis** | `pdf_tool` (extract, OCR, forms), `read_file` | Native Windows OCR | `TIER_0` |
| **Coding & Refactoring** | `read_file`, `write_file`, `code_refactor`, `run_sandboxed_process` | Diff patch generator | `TIER_0` / `TIER_1` |
| **System Maintenance** | `system_cleanup`, `system_optimizer`, `system_health` | Native PowerShell scripts | `TIER_1` |
| **Artifact Generation & View**| `write_file`, `export_artifact`, `browser_open_url` | Text summary in CLI | `TIER_0` |
