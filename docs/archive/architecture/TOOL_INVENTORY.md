# BR JARVIS — Universal Tool & Capability Inventory

**Total Registered Tools:** 211  
**Runtime Status:** Operational & Unified under `tools/registry.py` & `tools/tool_runtime.py`  
**Interfaces Supported:** Web UI, CLI (`jarvis-cli`), Voice (`jarvis`), Desktop HUD  

---

## Capability Categories Overview

| Category | Tool Count | Description |
| :--- | :--- | :--- |
| `application_and_os_control` | 15 | Comprehensive tools for application and os control |
| `communication` | 23 | Comprehensive tools for communication |
| `connectors_and_mcp` | 7 | Comprehensive tools for connectors and mcp |
| `developer_tools` | 7 | Comprehensive tools for developer tools |
| `filesystem_and_documents` | 24 | Comprehensive tools for filesystem and documents |
| `memory_and_context` | 15 | Comprehensive tools for memory and context |
| `security_and_redteam` | 6 | Comprehensive tools for security and redteam |
| `system_primitives` | 60 | Comprehensive tools for system primitives |
| `tasks_and_automation` | 15 | Comprehensive tools for tasks and automation |
| `vision_and_multimodal` | 14 | Comprehensive tools for vision and multimodal |
| `web_and_research` | 25 | Comprehensive tools for web and research |

---

## Category: APPLICATION AND OS CONTROL (15 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `computer_settings` | `tools.legacy_actions_tools` | Control OS-level settings: brightness, volume, wifi, dark mode, minimize/maximiz... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `execute_system_automation` | `tools.automation_tools` | Execute automated PowerShell or system shell command scripts with timeout and ou... | `DESTRUCTIVE / HIGH` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `focus_window` | `tools.pc_tools` | Bring a window to the foreground by title.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `get_system_diagnostics` | `tools.process_tools` | Retrieve real-time system performance telemetry: CPU, RAM, Top 10 memory-hogging... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `kill_process` | `tools.process_tools` | Kill or terminate a running process by Process ID (PID) or process name.... | `DESTRUCTIVE / HIGH` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `live_os_control` | `tools.live_os_tools` | Launch autonomous Live OS Visual Control loop ('Antigravity Mode'). Performs rea... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `open_app` | `tools.legacy_actions_tools` | Launch any application on the host machine.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `screen_process` | `tools.legacy_actions_tools` | Analyze screen or camera feed utilizing vision capabilities.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `system_cleanup` | `tools.system_tools` | Clean temporary cache files, old log files, and build artifacts to reclaim disk ... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `system_diagnostic` | `tools.system_diagnostic_tool` | Inspect system telemetry, CPU/RAM, active network ports, tool health status, or ... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `system_health` | `tools.system_health` | Retrieve system health metrics including CPU load, RAM usage, storage, and batte... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `system_monitor` | `tools.system_tools` | Get system health info: CPU, RAM, disk, network, top processes.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `system_optimizer` | `tools.system_tools` | Analyze and optimize CPU, RAM, and background task consumption.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `window_maximize` | `tools.pc_tools` | Maximize a window by title or process name.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |
| `window_minimize` | `tools.pc_tools` | Minimize a window by title or process name.... | `READ_ONLY / LOW` | `ApplicationVerifier (Win32 Use...` | **READY** |

## Category: COMMUNICATION (23 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `email_assistant` | `actions.email_assistant` | Send emails via SMTP, check recent inbox messages via IMAP, or draft mail templa... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `get_gmail_auth_status` | `tools.gmail_auth_tools` | Check whether a Gmail account is currently logged in, showing active email addre... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `gmail_list_unread` | `tools.app_connectors` | List unread emails from Gmail inbox with subject, sender, and snippet.... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **MOCK_STUB (Needs Rewiring)** |
| `gmail_login` | `tools.gmail_auth_tools` | Log in to Gmail. Mode 'browser' opens Google Sign-In page in browser. Mode 'cred... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `gmail_logout` | `tools.gmail_auth_tools` | Sign out of Gmail and clear stored credentials and session tokens from local sto... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `gmail_reply` | `tools.web_app_tools` | Search Gmail inbox for an email thread and send a reply message.... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `gmail_send` | `tools.web_app_tools` | Compose and send an email via Gmail online in the browser.... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **READY** |
| `gmail_send_email` | `tools.app_connectors` | Draft or send an email via Gmail connector.... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **MOCK_STUB (Needs Rewiring)** |
| `import_contacts` | `tools.contact_tools` | Import mobile contacts from a vCard (.vcf) file or CSV (.csv) file path or raw t... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `manage_contacts` | `tools.contact_tools` | Add, list, or search contacts in JARVIS memory. Args: 'action' ('add', 'list', '... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `manage_email_contacts` | `tools.smart_email_tools` | Add or list saved email contact address mappings. Args: 'action' ('add' or 'list... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `manage_telegram_contacts` | `tools.telegram_tools` | Add a new Telegram contact mapping (name → chat_id or @username) or list all sav... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `manage_whatsapp_contacts` | `tools.whatsapp_tools` | Add a new contact mapping or list saved contacts. Args: 'action' ('add' or 'list... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `resolve_contact` | `tools.contact_tools` | Look up phone number, email address, or WhatsApp target by contact name or alias... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `schedule_email` | `tools.smart_email_tools` | Schedule an email for future automated sending to any recipient.... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `schedule_telegram_message` | `tools.telegram_tools` | Schedule a Telegram message to be automatically sent to a contact at a specified... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `schedule_whatsapp_message` | `tools.whatsapp_tools` | Schedule a WhatsApp message to be automatically sent to a contact at a specified... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `send_email` | `tools.smart_email_tools` | Compose and send an email to any recipient email address (e.g. 'alex@example.com... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **READY** |
| `send_telegram` | `tools.telegram_tools` | Send a Telegram message to any contact, @username, or chat_id. NEVER use open_ap... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **READY** |
| `send_whatsapp` | `tools.whatsapp_tools` | Send a WhatsApp message or greeting directly to any contact name (e.g. 'Appa', '... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **READY** |
| `slack_send_message` | `tools.app_connectors` | Post a message to a Slack or Discord dev channel.... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **MOCK_STUB (Needs Rewiring)** |
| `telegram_bot_info` | `tools.telegram_tools` | Check the status of the configured Telegram bot and get a shareable link for con... | `READ_ONLY / LOW` | `ConnectorVerifier (API respons...` | **READY** |
| `telegram_get_updates` | `tools.telegram_tools` | Fetch recent messages received by the Telegram bot to discover chat_ids of users... | `WRITE / MEDIUM` | `ConnectorVerifier (API respons...` | **READY** |

## Category: CONNECTORS AND MCP (7 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `connector_add_mcp` | `tools.connector_tools` | Dynamically connect JARVIS to a new MCP server at runtime. Works with any MCP-co... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `connector_call` | `tools.connector_tools` | Call a specific tool on a JARVIS connector plugin. Use connector_status first to... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `connector_list_tools` | `tools.connector_tools` | List all available tools for a specific connector plugin.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `connector_status` | `tools.connector_tools` | Show the status of all JARVIS connectors (Wikipedia, GitHub, Notion, Slack, Weat... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `mcp_call_tool` | `tools.mcp_connector` | Connect to an external Model Context Protocol (MCP) server and execute a tool ca... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `notion_create_page` | `tools.app_connectors` | Create a new page in a Notion database or workspace root.... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **MOCK_STUB (Needs Rewiring)** |
| `weather_report` | `tools.legacy_actions_tools` | Get real-time weather information for a city.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |

## Category: DEVELOPER TOOLS (7 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `audit_codebase` | `tools.audit_tools` | Perform an automated security & code quality audit on the codebase. Detects synt... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **READY** |
| `code_helper` | `tools.legacy_actions_tools` | Write, edit, run, or build code in specific file paths.... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **READY** |
| `code_refactor` | `tools.code_refactor_tool` | Analyze, validate syntax, format, or refactor source code files using Python AST... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **READY** |
| `git_repo_mgr` | `tools.git_repo_tool` | Inspect git repository status, view diffs/logs, switch branches, create branches... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **READY** |
| `github_create_issue` | `tools.app_connectors` | Create a new issue on GitHub repository.... | `WRITE / MEDIUM` | `GitVerifier / CommandVerifier ...` | **MOCK_STUB (Needs Rewiring)** |
| `github_list_prs` | `tools.app_connectors` | List open Pull Requests or Issues in a GitHub repository.... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **MOCK_STUB (Needs Rewiring)** |
| `run_code` | `tools.code_tools` | Execute code in a sandboxed environment. Supports python, javascript, bash.... | `READ_ONLY / LOW` | `GitVerifier / CommandVerifier ...` | **READY** |

## Category: FILESYSTEM AND DOCUMENTS (24 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `analyze_project_to_excel` | `tools.excel_tools` | Perform a comprehensive architectural analysis of the JARVIS codebase and export... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `batch_file_ops` | `tools.batch_file_tool` | Perform batch regex file search/replace, directory tree rendering, or zip archiv... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `create_excel_sheet` | `tools.excel_tools` | Create a formatted Excel spreadsheet (.xlsx) with styled headers, custom data ro... | `WRITE / MEDIUM` | `FileVerifier (existence, non-z...` | **READY** |
| `create_pdf_document` | `tools.doc_tools` | Create a formatted PDF (.pdf) document and auto-launch in default PDF viewer.... | `WRITE / MEDIUM` | `FileVerifier (existence, non-z...` | **READY** |
| `create_word_document` | `tools.doc_tools` | Create a formatted Microsoft Word (.docx) document with cover page, headers, tab... | `WRITE / MEDIUM` | `FileVerifier (existence, non-z...` | **READY** |
| `document_creator` | `tools.doc_tools` | Universal Executive Document Engine. Creates styled Word (.docx), PDF (.pdf), HT... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `fast_file_search` | `tools.registry` | High-speed desktop file search by filename or text content. Args: 'action' ('nam... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `file_controller` | `tools.legacy_actions_tools` | Perform file and directory management actions (read, write, delete, move, create... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `file_list` | `tools.file_tools` | List files in a workspace directory.... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `file_read` | `tools.file_tools` | Read a file from the workspace.... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `file_search_semantic` | `tools.file_search_semantic` | Search workspace files by natural language keywords, filename patterns, or exten... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `file_write` | `tools.file_tools` | Write content to a file in the workspace.... | `WRITE / MEDIUM` | `FileVerifier (existence, non-z...` | **READY** |
| `generate_walkthrough` | `tools.doc_tools` | Generate a rich GitHub-flavored Markdown Walkthrough document (walkthrough.md) d... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `import_file_to_knowledge` | `tools.file_import_tools` | Import a document (.txt, .pdf, .docx, .md, .csv, .vcf) from local filesystem int... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `open_workspace_file` | `tools.workspace_tools` | Smart natural language file opener for BR_WORKSPACE/. Accepts query like 'open y... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `pdf_tool` | `tools.pdf_tools` | Comprehensive PDF operations tool - merge, split, compress, convert (PDF<->Word/... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `process_universal_file` | `tools.file_processor_tools` | Process, analyze, read, convert, OCR, or summarize any file type (image, PDF, DO... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `scratchpad_clear` | `tools.scratchpad_tools` | Clean temporary scratch workspace files and notes.... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `scratchpad_eval` | `tools.scratchpad_tools` | Execute a code snippet or script in ./scratch/ and capture stdout/stderr and ret... | `DESTRUCTIVE / HIGH` | `FileVerifier (existence, non-z...` | **READY** |
| `scratchpad_list` | `tools.scratchpad_tools` | List active temporary files in the ./scratch/ workspace.... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `scratchpad_read` | `tools.scratchpad_tools` | Read content from a scratch file in ./scratch/.... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `scratchpad_write` | `tools.scratchpad_tools` | Write content or code to a scratch file in ./scratch/ for temporary work or eval... | `WRITE / MEDIUM` | `FileVerifier (existence, non-z...` | **READY** |
| `semantic_file_search` | `tools.file_search_semantic` | Search workspace files by natural language keywords, filename patterns, or exten... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |
| `transcribe_file` | `tools.transcription_tools` | Transcribe an audio or video file to text offline using local Whisper. Supports ... | `READ_ONLY / LOW` | `FileVerifier (existence, non-z...` | **READY** |

## Category: MEMORY AND CONTEXT (15 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `memory_delete` | `tools.memory_tools` | Delete a persistent memory entry by name.... | `DESTRUCTIVE / HIGH` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_forget` | `tools.memory_tools` | Forget or invalidate memories matching a concept or query.... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_get` | `tools.memory_tools` | Retrieve a specific memory entry by name.... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_list` | `tools.memory_tools` | List all persistent memory entries across user and project scopes.... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_reindex` | `tools.memory_tools` | Rebuild and synchronize memory indices across Markdown files, SQLite database, a... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_save` | `tools.memory_tools` | Save or create a persistent memory entry with taxonomy type (user, preference, f... | `WRITE / MEDIUM` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `memory_stats` | `tools.memory_tools` | Show memory diagnostics: total count by type, scope, storage size, and vector st... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `mouse_drag` | `tools.pc_tools` | Click and drag from one point to another.... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `rag_chat` | `tools.rag_tools` | Chat with your personal document library. Ask questions and get AI-generated ans... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `rag_delete` | `tools.rag_tools` | Delete a document from the local RAG library by name.... | `DESTRUCTIVE / HIGH` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `rag_ingest` | `tools.rag_tools` | Ingest a document (PDF, DOCX, TXT, CSV, MD) into the local RAG library for later... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `rag_list` | `tools.rag_tools` | List all documents currently in the local RAG library.... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `rag_query` | `tools.rag_tools` | Search the local document library for information relevant to a question. Return... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `remember_that` | `tools.recall_tools` | Save a new memory note to disk by voice or text ('Remember that...'), live-spawn... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |
| `visual_drag` | `tools.live_os_tools` | Click and drag from a source UI element to a target UI element identified by vis... | `READ_ONLY / LOW` | `MemoryVerifier (SQLite row cou...` | **READY** |

## Category: SECURITY AND REDTEAM (6 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `audit_prompt_security` | `tools.redteam_tools` | Audit user prompt or screen/web content for injection attacks.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `dns_enum` | `tools.redteam_tools` | Enumerate DNS records for a domain (scope-checked).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `headers_audit` | `tools.redteam_tools` | Audit HTTP security headers of a URL (scope-checked).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `nmap_scan` | `tools.redteam_tools` | Run an nmap service scan on a host (scope-checked, requires nmap installed).... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `port_scan` | `tools.redteam_tools` | Scan TCP ports on a host (scope-checked). Returns open/closed status.... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `whois_lookup` | `tools.redteam_tools` | Perform a WHOIS lookup on a domain (scope-checked).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |

## Category: SYSTEM PRIMITIVES (60 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `agent_task` | `tools.legacy_actions_tools` | Complex multi-step autonomous task to run in parallel or nested.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `artifact_export` | `tools.export_tools` | Export a user-facing artifact generated inside the sandbox to the verified safe ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `artifact_list` | `tools.export_tools` | List all verified exported host artifacts and their integrity hashes.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `automate_app` | `tools.automation_tools` | Perform application lifecycle automation actions: 'launch', 'close', or 'focus'.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `check_agent` | `tools.agent_tools` | Check the status and result of a spawned sub-agent task.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `cli_controller` | `tools.system_tools` | Full terminal/shell access. Run ANY shell command, manage persistent shell sessi... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `clipboard_history` | `actions.clipboard_history` | Retrieve, list, or search clipboard history logged by the background tracker.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `clipboard_read` | `tools.pc_tools` | Read the current clipboard content.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `clipboard_write` | `tools.pc_tools` | Write text to the clipboard and paste it.... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **READY** |
| `computer_control` | `tools.pc_tools` | Mouse, keyboard, and screen automation engine (click, move, drag, type, hotkey, ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `cursor_click` | `tools.pc_tools` | Click the mouse at the current position or specified coordinates.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `cursor_get_position` | `tools.pc_tools` | Get current mouse cursor (X, Y) coordinates on screen.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `cursor_move` | `tools.pc_tools` | Move the mouse cursor to specific screen coordinates.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `custom_command_add` | `tools.custom_command_tools` | Add or update a custom command. You can define triggers (including variable anch... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `custom_command_delete` | `tools.custom_command_tools` | Delete a custom command using its trigger phrase.... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `custom_command_list` | `tools.custom_command_tools` | List all user-configured custom voice and text commands.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `desktop_control` | `tools.legacy_actions_tools` | Wallpaper management or desktop organizing utilities.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `dev_agent` | `tools.legacy_actions_tools` | Build complete multi-file software projects autonomously.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `display_resolution` | `tools.pc_tools` | Query screen display dimensions (width, height).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `export_chat` | `tools.export_tools` | Export the current conversation/chat history to a file. Formats: pdf, md (Markdo... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `fetch_page` | `tools.web_tools` | Fetch and extract text content from a URL using a headless browser.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `fetch_raw` | `tools.web_tools` | Fetch raw HTML/text content from a URL via HTTP GET.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `game_updater` | `tools.legacy_actions_tools` | Manage Steam/Epic games (updating, launching, checking status).... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **READY** |
| `generate_project_product_analysis` | `tools.doc_tools` | Generate a complete Product Analysis Report for B.R. JARVIS as Word (.docx) and ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `generate_report` | `tools.redteam_tools` | Generate a professional penetration test report in markdown.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `get_app_launch_history` | `tools.app_tracker_tools` | Retrieve the persistent log of application start events recorded on this machine... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `get_app_usage_statistics` | `tools.app_tracker_tools` | Retrieve analytics on application starts, including total launches, most launche... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `get_pending_channel_actions` | `tools.proactive_listener_tools` | Retrieve all unhandled incoming Email and WhatsApp messages requiring user opini... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `get_workspace_timeline` | `tools.workspace_tools` | Retrieve the chronological workspace action timeline stream (file creations, cod... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `init_project_workspace` | `tools.workspace_tools` | Create a standardized self-contained Project Workspace (source, docs, architectu... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `keyboard_hotkey` | `tools.pc_tools` | Press a key combination (e.g., ctrl+c, alt+tab).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `keyboard_key_down` | `tools.pc_tools` | Press and hold a specific key down.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `keyboard_key_up` | `tools.pc_tools` | Release a held key.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `keyboard_press` | `tools.pc_tools` | Press a single key (enter, tab, escape, etc.).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `keyboard_type` | `tools.pc_tools` | Type text at the current cursor position.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_agent_types` | `tools.agent_tools` | List all available agent types (built-in and custom).... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_agents` | `tools.agent_tools` | List all sub-agent tasks and their statuses.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_installed_applications` | `tools.app_analyzer_tools` | Scan and list all installed applications on the system (Windows Registry/Start M... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_running_applications` | `tools.app_analyzer_tools` | List all active running desktop applications and processes on the system with PI... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_skills` | `tools.skills_tools` | List all available user-invocable skills.... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `longform_builder` | `tools.registry` | Build comprehensive multi-volume books, technical manuals, research publications... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `mouse_scroll` | `tools.pc_tools` | Scroll the mouse wheel.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `ms365_control` | `tools.web_app_tools` | Launch and interact with Microsoft 365 / Office Online web apps (Word, Excel, Po... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `native_grid_transform` | `tools.system_tools` | Transform target visual grid coordinates to screen pixel coordinates via C exten... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `native_hash_fast` | `tools.system_tools` | High-speed C-native FNV-1a hashing for screen frame delta detection or content i... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `native_proc_telemetry` | `tools.system_tools` | Low-overhead C-native process page count and RAM usage reader.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `qa_assert_page_state` | `tools.qa_testing_tool` | Assert background page conditions (URL match, text presence, selector existence,... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `qa_generate_report` | `tools.qa_testing_tool` | Generate a comprehensive Markdown QA Audit Report from test execution results.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `respond_channel_action` | `tools.proactive_listener_tools` | Execute user approval decision ('reply', 'add_to_calendar', or 'dismiss') for a ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `run_skill` | `tools.skills_tools` | Execute a named skill (reusable prompt template). Use list_skills to see availab... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `send_message` | `tools.agent_tools` | Send a follow-up message to a running background agent.... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **READY** |
| `smart_click` | `tools.pc_tools` | Smartly click a UI element by its natural language description.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `spawn_agent` | `tools.agent_tools` | Spawn a sub-agent to handle a task autonomously. NOTE: available in CLI mode (st... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `start_multichannel_listener` | `tools.proactive_listener_tools` | Start the proactive background listener monitoring incoming Emails and WhatsApp ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `stop_multichannel_listener` | `tools.proactive_listener_tools` | Stop the proactive background listener.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `sync_app_paths` | `tools.app_analyzer_tools` | Automatically scan host OS (Windows Registry, Start Menu, LocalAppData, Program ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `transcribe_batch` | `tools.transcription_tools` | Transcribe multiple audio/video files in batch. Returns results for each file.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `visual_click` | `tools.live_os_tools` | Use AI vision to locate a specific UI element by description on the screen and c... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `visual_type` | `tools.live_os_tools` | Use AI vision to locate an input field by description and type text into it.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `wait_for_element` | `tools.pc_tools` | Wait until a UI element appears on screen.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |

## Category: TASKS AND AUTOMATION (15 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `add_background_monitor` | `tools.background_monitor_tools` | Add a new topic for JARVIS to monitor daily via background news checks (e.g. AI ... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `calendar_create_event` | `tools.app_connectors` | Schedule a new meeting or event in Google Calendar.... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **MOCK_STUB (Needs Rewiring)** |
| `calendar_list_events` | `tools.app_connectors` | List upcoming events and meetings from Google Calendar.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **MOCK_STUB (Needs Rewiring)** |
| `check_monitored_topics` | `tools.background_monitor_tools` | Manually trigger an immediate check across all monitored topics for new headline... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `create_calendar_event` | `tools.calendar_tools` | Create a calendar event or task (like Mobile Gemini). Args: 'title' (event title... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **READY** |
| `delete_calendar_event` | `tools.calendar_tools` | Delete a calendar event by ID.... | `DESTRUCTIVE / HIGH` | `CommandVerifier (structured JS...` | **READY** |
| `list_calendar_events` | `tools.calendar_tools` | List upcoming calendar events and tasks. Args: 'days' (integer number of days to... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_monitored_topics` | `tools.background_monitor_tools` | List all topics currently monitored by JARVIS.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_monitors` | `tools.system_tools` | List all available monitors with resolution and position.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `manage_reminders` | `tools.reminder_tools` | Add, list, or check pending smart desktop reminders with audio alerts.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `reminder` | `tools.registry` | Set or list smart reminders and desktop toast notifications. Args: 'action' ('ad... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `remove_background_monitor` | `tools.background_monitor_tools` | Stop monitoring a previously added news topic.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `run_automation_workflow` | `tools.automation_tools` | Execute a multi-step macro automation workflow script. Pass steps as a JSON list... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `schedule_reminder` | `tools.reminder_tools` | Schedule an OS-native reminder notification.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `scheduler` | `actions.scheduler` | Schedule automated goals to run at intervals or specific times.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |

## Category: VISION AND MULTIMODAL (14 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `edit_image` | `tools.image_tools` | Edit an existing image using AI. Supports inpainting with optional mask.... | `WRITE / MEDIUM` | `CommandVerifier (structured JS...` | **READY** |
| `generate_image` | `tools.image_tools` | Generate an AI image from a text description. Providers: gemini (Imagen), openai... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `generate_video` | `tools.video_tools` | Generate an AI video from a text description. Providers: veo (Google Veo), kling... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `list_generated_videos` | `tools.video_tools` | List all previously generated AI videos.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `live_screen_analyze` | `tools.live_os_tools` | Analyze the current screen using vision AI and return a structured visual breakd... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `native_audio_meter` | `tools.system_tools` | High-speed C-native RMS audio energy calculator for microphone and voice level m... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_click` | `tools.pc_tools` | Find a UI element by description and click on it.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_describe` | `tools.pc_tools` | Get a natural language description of what is on the screen.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_find` | `tools.pc_tools` | Use AI vision to find a UI element on screen by description. Returns coordinates... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_read` | `tools.pc_tools` | Read and OCR the entire screen via vision.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_share_start` | `tools.system_tools` | Start real-time screen sharing over WebSocket.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_share_status` | `tools.system_tools` | Get the current screen sharing status.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `screen_share_stop` | `tools.system_tools` | Stop the active screen sharing session.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |
| `take_screenshot` | `tools.pc_tools` | Capture a screenshot of the current screen.... | `READ_ONLY / LOW` | `CommandVerifier (structured JS...` | **READY** |

## Category: WEB AND RESEARCH (25 tools)

| Tool Name | Module | Description | Permission Level | Verifier Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `browser_auto_navigate_and_extract` | `tools.autonomous_browser_agent` | Navigate to any URL in background browser, clean page clutter, and extract main ... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_click` | `tools.browser_automation` | Click a button, link, tab, or element on the current web page by visible text, A... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_eval_js` | `tools.browser_automation` | Evaluate a custom JavaScript snippet inside the active web page context and retu... | `DESTRUCTIVE / HIGH` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_execute_web_task` | `tools.autonomous_browser_agent` | Autonomously execute a multi-step web task in a background browser (e.g. search,... | `DESTRUCTIVE / HIGH` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_fill_and_submit_form` | `tools.autonomous_browser_agent` | Automatically fill out input fields on the active browser page and submit the fo... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_history` | `tools.browser_automation` | Execute browser history actions: 'back', 'forward', or 'reload'.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_new_tab` | `tools.browser_automation` | Open a new browser tab with an optional URL.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_open_url` | `tools.browser_automation` | Open a website in the interactive browser (e.g. Gmail, Microsoft 365, Outlook, o... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_read_page` | `tools.browser_automation` | Read visible text and interactive form fields from the current web page.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_screenshot` | `tools.browser_automation` | Capture a screenshot of the active browser web page and save it to workspace.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_scroll` | `tools.browser_automation` | Scroll the active web page up or down, or scroll to top/bottom.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_strawberry_agent` | `tools.browser_agent_v2` | Execute intelligent autonomous browser interaction with semantic accessibility p... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_switch_tab` | `tools.browser_automation` | Switch active browser focus to a specific tab by 0-based index.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `browser_type` | `tools.browser_automation` | Type text into an input field or contenteditable area on the active web page.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `connector_search` | `tools.connector_tools` | Smart search that automatically queries the best available connectors for a give... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `flight_finder` | `tools.legacy_actions_tools` | Search flights details between origin and destination on a specific date.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `memory_search` | `tools.memory_tools` | Search persistent memories by keyword with relevance, freshness, and confidence ... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `notion_search_pages` | `tools.app_connectors` | Search Notion workspace for pages, databases, or documentation notes.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **MOCK_STUB (Needs Rewiring)** |
| `qa_run_browser_test` | `tools.qa_testing_tool` | Run an autonomous background end-to-end browser test flow on a target URL or loc... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `rag_ingest_webpage` | `tools.rag_tools` | Ingest a webpage into the local RAG library by fetching and indexing its content... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `search_applications` | `tools.app_analyzer_tools` | Search both installed and currently running applications on the system by keywor... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `search_calendar_events` | `tools.calendar_tools` | Search calendar events by title, description, or location keyword.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `web_extractor` | `tools.web_extractor` | Fetch web page HTML and extract clean text content, headers, and main body text.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `web_search` | `tools.web_tools` | Search the web using DuckDuckGo. Returns a list of results with titles, URLs, an... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
| `youtube_video` | `tools.legacy_actions_tools` | Play or summarize a YouTube video.... | `READ_ONLY / LOW` | `BrowserVerifier (HTTP response...` | **READY** |
