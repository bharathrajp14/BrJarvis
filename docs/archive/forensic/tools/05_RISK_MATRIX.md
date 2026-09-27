# BR JARVIS — MASTER TOOL RISK & ATTACK SURFACE MATRIX

## 1. Risk Tier Definitions
- **READ_ONLY**: No state mutation, zero disk writes, safe for unattended autonomous execution.
- **LOW_RISK**: Creates workspace files or inspects non-sensitive system metrics.
- **MODERATE_RISK**: Modifies user documents, sends network requests, or manages reminders.
- **HIGH_RISK**: Spawns OS subprocesses, executes shell commands, or modifies system settings.
- **CRITICAL**: Alters security policy, deletes directories, or interacts with system credentials.

---

## 2. Tool Risk Matrix

| Tool Name | Risk Tier | Attack Surface | Required Permission | Confirmation Needed | Sandbox Confined | Physical Verification |
| :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| `read_file` | **READ_ONLY** | Local Filesystem Read | `TIER_0` / `TIER_1` | No | Yes | `verify_file_exists` |
| `semantic_file_search` | **READ_ONLY** | File Metadata & Index | `TIER_0` | No | Yes | Non-empty result |
| `write_file` | **LOW_RISK** | Workspace Disk Write | `TIER_0` | No | Yes | `verify_file_created` |
| `pdf_tool` | **LOW_RISK** | Document Parser / OCR | `TIER_0` | No | Yes | Output file check |
| `web_extractor` | **LOW_RISK** | Outbound HTTP GET | `TIER_0` | No | Yes | Status 200 check |
| `schedule_reminder` | **MODERATE_RISK** | Desktop Notifications | `TIER_1` | No | No | SQLite row check |
| `send_email` | **MODERATE_RISK** | Outbound SMTP / Email | `TIER_1` | Yes (Prompt) | No | `verify_email_sent` |
| `browser_click` | **MODERATE_RISK** | Web Session Interaction | `TIER_0` | No | Yes | DOM state check |
| `system_cleanup` | **MODERATE_RISK** | Temp File Deletion | `TIER_1` | No | No | Disk space check |
| `run_sandboxed_process`| **HIGH_RISK** | Subprocess Execution | `TIER_1` | Yes | Yes (Restricted) | Exit code & Process check |
| `cli_controller` | **HIGH_RISK** | Shell Command Invocation | `TIER_1` / `TIER_2` | Yes (Destructive) | No | Process exit check |
| `nmap_scan` | **HIGH_RISK** | Raw Network Socket | `TIER_2` | Yes | No | Report check |
