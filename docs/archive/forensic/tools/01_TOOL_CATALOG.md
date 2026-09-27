# BR JARVIS — MASTER TOOL CATALOG & SPECIFICATION RECORD

## 1. Catalog Summary
- **Total Registered Capabilities**: **185**
- **Source Registry**: `tools/registry.py` (`TOOL_SCHEMAS` and `TOOL_REGISTRY`)

---

## 2. Master Tool Catalog

### Tool: `agent_task`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_agent_task`
- **Category**: **General & Skill Execution**
- **Description**: Complex multi-step autonomous task to run in parallel or nested.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `goal` (string, Required): 
  - `priority` (string, Optional): normal, high, low
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `analyze_project_to_excel`
- **Implementation File**: `tools/excel_tools.py`
- **Function**: `analyze_project_to_excel`
- **Category**: **General & Skill Execution**
- **Description**: Perform a comprehensive architectural analysis of the JARVIS codebase and export a styled multi-tab Excel workbook (Executive Summary, File Inventory, Subsystem Audit).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `project_path` (string, Optional): Root path of codebase to analyze (default: current workspace)
  - `output_filename` (string, Optional): Output Excel file name
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `artifact_export`
- **Implementation File**: `tools/export_tools.py`
- **Function**: `tool_artifact_export`
- **Category**: **Security & Network Recon**
- **Description**: Export a user-facing artifact generated inside the sandbox to the verified safe host workspace directory.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `path` (string, Required): Source path of the artifact inside sandbox or workspace
  - `filename` (string, Optional): Optional custom filename on host
  - `task_id` (string, Optional): Optional task ID
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `artifact_list`
- **Implementation File**: `tools/export_tools.py`
- **Function**: `tool_artifact_list`
- **Category**: **General & Skill Execution**
- **Description**: List all verified exported host artifacts and their integrity hashes.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `audit_codebase`
- **Implementation File**: `tools/audit_tools.py`
- **Function**: `audit_codebase`
- **Category**: **General & Skill Execution**
- **Description**: Perform an automated security & code quality audit on the codebase. Detects syntax errors, security vulnerabilities, hardcoded secrets, and unsafe execution patterns.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `target_dir` (string, Optional): Target folder path to audit (defaults to workspace root)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `audit_prompt_security`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `audit_prompt_security`
- **Category**: **Security & Network Recon**
- **Description**: Audit user prompt or screen/web content for injection attacks.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `content` (string, Required): Content to inspect for injection vulnerabilities
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `automate_app`
- **Implementation File**: `tools/automation_tools.py`
- **Function**: `tool_automate_app`
- **Category**: **General & Skill Execution**
- **Description**: Perform application lifecycle automation actions: 'launch', 'close', or 'focus'. Args: 'action' ('launch', 'close', or 'focus'), 'app_name' (application name or window title), 'url' (optional target URL).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): Action to perform
  - `app_name` (string, Required): Application name, executable name, PID, or window title
  - `url` (string, Optional): Optional web URL if opening a browser app
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `batch_file_ops`
- **Implementation File**: `tools/batch_file_tool.py`
- **Function**: `batch_file_ops`
- **Category**: **Filesystem & Storage**
- **Description**: Perform batch regex file search/replace, directory tree rendering, or zip archive compression/extraction.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `action` (string, Required): Batch operation to perform
  - `target_dir` (string, Optional): Target root directory path
  - `pattern` (string, Optional): Regex pattern or glob file filter
  - `replace_text` (string, Optional): Replacement string for batch_replace
  - `zip_path` (string, Optional): Archive file path for create_zip/extract_zip
  - `max_depth` (integer, Optional): Max depth for tree view (default: 3)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_auto_navigate_and_extract`
- **Implementation File**: `tools/autonomous_browser_agent.py`
- **Function**: `browser_auto_navigate_and_extract`
- **Category**: **Web & Browser Automation**
- **Description**: Navigate to any URL in background browser, clean page clutter, and extract main structured content.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `url` (string, Required): Target website URL
  - `max_lines` (integer, Optional): Max text lines to return (default 40)
  - `headless` (boolean, Optional): Run in background without opening window (default true)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_click`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_click`
- **Category**: **Web & Browser Automation**
- **Description**: Click a button, link, tab, or element on the current web page by visible text, ARIA label, or CSS selector.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `target` (string, Required): Text, button label, or CSS selector to click (e.g., 'Compose', 'Send', 'Reply', '#btn')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_eval_js`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_eval_js`
- **Category**: **Web & Browser Automation**
- **Description**: Evaluate a custom JavaScript snippet inside the active web page context and return the result.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `script` (string, Required): JavaScript code string to evaluate (e.g. 'document.title' or 'document.links.length')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_execute_web_task`
- **Implementation File**: `tools/autonomous_browser_agent.py`
- **Function**: `browser_execute_web_task`
- **Category**: **Web & Browser Automation**
- **Description**: Autonomously execute a multi-step web task in a background browser (e.g. search, navigate, extract information, summarize).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `goal` (string, Required): High-level goal statement e.g. 'Search for Python 3.14 release features and extract key points'
  - `start_url` (string, Optional): Starting URL (default: https://www.google.com)
  - `max_steps` (integer, Optional): Maximum navigation steps to execute (default 5)
  - `headless` (boolean, Optional): Run in background without opening browser window (default true)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_fill_and_submit_form`
- **Implementation File**: `tools/autonomous_browser_agent.py`
- **Function**: `browser_fill_and_submit_form`
- **Category**: **Web & Browser Automation**
- **Description**: Automatically fill out input fields on the active browser page and submit the form.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `url` (string, Optional): URL of the page containing the form (optional if page is already open)
  - `form_fields` (object, Required): Dictionary of field selectors/names/placeholders to values e.g. {'username': 'john', 'email': 'john@example.com'}
  - `submit_button` (string, Optional): CSS selector or button text to click for submission (optional)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_history`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_history`
- **Category**: **Web & Browser Automation**
- **Description**: Execute browser history actions: 'back', 'forward', or 'reload'.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `action` (string, Required): Action name: 'back', 'forward', or 'reload'
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_new_tab`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_new_tab`
- **Category**: **Web & Browser Automation**
- **Description**: Open a new browser tab with an optional URL.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `url` (string, Optional): URL to open in the new tab (default 'about:blank')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_open_url`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_open_url`
- **Category**: **Web & Browser Automation**
- **Description**: Open a website in the interactive browser (e.g. Gmail, Microsoft 365, Outlook, or verified host HTML reports). Reuses logged-in sessions.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `url` (string, Required): URL or host artifact path to open (e.g. https://mail.google.com or C:/Users/.../report.html)
  - `headless` (boolean, Optional): Run in background without opening window (default false)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_read_page`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_read_page`
- **Category**: **Filesystem & Storage**
- **Description**: Read visible text and interactive form fields from the current web page.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_screenshot`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_screenshot`
- **Category**: **Web & Browser Automation**
- **Description**: Capture a screenshot of the active browser web page and save it to workspace.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `filename` (string, Optional): Target PNG filename, default is browser_screenshot.png
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_scroll`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_scroll`
- **Category**: **Web & Browser Automation**
- **Description**: Scroll the active web page up or down, or scroll to top/bottom.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `direction` (string, Optional): Scroll direction: 'down', 'up', 'top', or 'bottom'
  - `amount` (integer, Optional): Pixel amount to scroll (default 500)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_strawberry_agent`
- **Implementation File**: `tools/browser_agent_v2.py`
- **Function**: `browser_strawberry_agent`
- **Category**: **Web & Browser Automation**
- **Description**: Execute intelligent autonomous browser interaction with semantic accessibility parsing, structured click/type/scroll actions, and automatic error recovery.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (8)**:
  - `action` (string, Required): The browser operation to perform.
  - `url` (string, Optional): Target webpage URL (for navigate)
  - `target_id` (integer, Optional): Element ID from prior observation (for click/type)
  - `selector` (string, Optional): CSS selector or text selector
  - `text` (string, Optional): Text to type into the target field
  - `direction` (string, Optional): Scroll direction
  - `amount` (integer, Optional): Scroll pixel amount (default 500)
  - `headless` (boolean, Optional): Run in background headless mode (default true)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_switch_tab`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_switch_tab`
- **Category**: **Web & Browser Automation**
- **Description**: Switch active browser focus to a specific tab by 0-based index.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `index` (integer, Required): 0-based tab index to bring to focus
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `browser_type`
- **Implementation File**: `tools/browser_automation.py`
- **Function**: `browser_type`
- **Category**: **Web & Browser Automation**
- **Description**: Type text into an input field or contenteditable area on the active web page.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `target` (string, Required): Field text label, placeholder, name, or selector (e.g. 'To', 'Subject', 'Message body')
  - `text` (string, Required): Text content to type
  - `press_enter` (boolean, Optional): Whether to press Enter after typing
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `calendar_create_event`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `calendar_create_event`
- **Category**: **General & Skill Execution**
- **Description**: Schedule a new meeting or event in Google Calendar.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `summary` (string, Required): Title/summary of the meeting
  - `start_time` (string, Required): ISO start time e.g. '2026-07-22T16:00:00'
  - `duration_minutes` (integer, Optional): Duration in minutes (default: 30)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `calendar_list_events`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `calendar_list_events`
- **Category**: **General & Skill Execution**
- **Description**: List upcoming events and meetings from Google Calendar.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `days` (integer, Optional): Number of days ahead to search (default: 7)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `check_agent`
- **Implementation File**: `tools/agent_tools.py`
- **Function**: `tool_check_agent`
- **Category**: **General & Skill Execution**
- **Description**: Check the status and result of a spawned sub-agent task.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `task_id` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `cli_controller`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_cli_controller`
- **Category**: **Process & OS Execution**
- **Description**: Full terminal/shell access. Run ANY shell command, manage persistent shell sessions with state (env vars, cwd), execute Python code, send input to interactive programs, manage background processes. Actions: run, run_session, send_input, cd, pwd, python, pipe, bg, which, env, session_new, session_end, history, auto.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (8)**:
  - `action` (string, Required): 
  - `cmd` (string, Optional): 
  - `name` (string, Optional): 
  - `cwd` (string, Optional): 
  - `timeout` (integer, Optional): 
  - `key` (string, Optional): 
  - `value` (string, Optional): 
  - `code` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `clipboard_history`
- **Implementation File**: `actions/clipboard_history.py`
- **Function**: `tool_clipboard_history`
- **Category**: **Process & OS Execution**
- **Description**: Retrieve, list, or search clipboard history logged by the background tracker.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): list, search
  - `query` (string, Optional): Keyword to search for (required for action='search')
  - `limit` (integer, Optional): Max entries to return (default 10)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `clipboard_read`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_clipboard_read`
- **Category**: **Filesystem & Storage**
- **Description**: Read the current clipboard content.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `clipboard_write`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_clipboard_write`
- **Category**: **Filesystem & Storage**
- **Description**: Write text to the clipboard and paste it.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `text` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `code_helper`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_code_helper`
- **Category**: **General & Skill Execution**
- **Description**: Write, edit, run, or build code in specific file paths.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `action` (string, Required): write, edit, run, build
  - `description` (string, Optional): 
  - `language` (string, Optional): 
  - `file_path` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `code_refactor`
- **Implementation File**: `tools/code_refactor_tool.py`
- **Function**: `code_refactor`
- **Category**: **General & Skill Execution**
- **Description**: Analyze, validate syntax, format, or refactor source code files using Python AST and linter checks.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): Refactoring action to perform
  - `file_path` (string, Optional): Target source code file path
  - `code` (string, Optional): Optional inline code snippet to check
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `computer_control`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_computer_control`
- **Category**: **General & Skill Execution**
- **Description**: Mouse, keyboard, and screen automation engine (click, move, drag, type, hotkey, press, scroll, screenshot, screen_find, screen_click).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (15)**:
  - `action` (string, Required): type, smart_type, click, double_click, right_click, move, drag, hotkey, press, scroll, copy, paste, screenshot, wait, clear_field, focus_window, screen_find, screen_click, random_data, user_data
  - `text` (string, Optional): 
  - `x` (number, Optional): 
  - `y` (number, Optional): 
  - `x1` (number, Optional): 
  - `y1` (number, Optional): 
  - `x2` (number, Optional): 
  - `y2` (number, Optional): 
  - `keys` (string, Optional): 
  - `key` (string, Optional): 
  - `direction` (string, Optional): 
  - `amount` (number, Optional): 
  - `seconds` (number, Optional): 
  - `title` (string, Optional): 
  - `description` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `computer_settings`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_computer_settings`
- **Category**: **General & Skill Execution**
- **Description**: Control OS-level settings: brightness, volume, wifi, dark mode, minimize/maximize.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): set_volume, set_brightness, toggle_wifi, toggle_dark_mode, minimize_all, maximize_all
  - `description` (string, Optional): 
  - `value` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `create_calendar_event`
- **Implementation File**: `tools/calendar_tools.py`
- **Function**: `tool_create_calendar_event`
- **Category**: **General & Skill Execution**
- **Description**: Create a calendar event or task (like Mobile Gemini). Args: 'title' (event title), 'start_time' (e.g. 'tomorrow 3pm', '2026-08-01 10:00', 'in 2 hours'), 'end_time' (optional), 'description' (optional), 'location' (optional), 'attendees' (optional list of contacts/emails), 'reminder_minutes' (default: 15), 'notify_whatsapp' (boolean).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (8)**:
  - `title` (string, Required): Title or task summary
  - `start_time` (string, Required): Start time expression (e.g. 'tomorrow 3pm', 'in 2 hours', '2026-08-01 10:00')
  - `end_time` (string, Optional): Optional end time expression
  - `description` (string, Optional): Optional event details/notes
  - `location` (string, Optional): Optional event location or meeting link
  - `attendees` (array, Optional): Optional list of attendee contacts or phone numbers
  - `reminder_minutes` (integer, Optional): Minutes before event to alert (default: 15)
  - `notify_whatsapp` (boolean, Optional): Whether to send WhatsApp invites to attendees
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `create_excel_sheet`
- **Implementation File**: `tools/excel_tools.py`
- **Function**: `create_excel_sheet`
- **Category**: **General & Skill Execution**
- **Description**: Create a formatted Excel spreadsheet (.xlsx) with styled headers, custom data rows, auto-column sizing, and optional auto-launch.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (5)**:
  - `title` (string, Optional): Title of the main worksheet sheet
  - `headers` (array, Required): List of column header names
  - `rows` (array, Required): List of data rows (each row is a list of cell values)
  - `filename` (string, Required): Output filename ending in .xlsx (e.g. report.xlsx)
  - `auto_open` (boolean, Optional): Whether to launch Microsoft Excel automatically after creation
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `create_pdf_document`
- **Implementation File**: `tools/doc_tools.py`
- **Function**: `create_pdf_document`
- **Category**: **General & Skill Execution**
- **Description**: Create a formatted PDF (.pdf) document and auto-launch in default PDF viewer.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `title` (string, Required): Document title
  - `content` (string, Required): Main text content or markdown
  - `filename` (string, Optional): Output filename ending in .pdf
  - `auto_open` (boolean, Optional): Whether to auto-launch PDF viewer
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `create_word_document`
- **Implementation File**: `tools/doc_tools.py`
- **Function**: `create_word_document`
- **Category**: **General & Skill Execution**
- **Description**: Create a formatted Microsoft Word (.docx) document with cover page, headers, tables, callouts, and auto-launch.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `title` (string, Required): Document title
  - `content` (string, Required): Main document text content or markdown
  - `filename` (string, Optional): Output filename ending in .docx
  - `auto_open` (boolean, Optional): Whether to auto-launch Word
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `cursor_click`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_cursor_click`
- **Category**: **Process & OS Execution**
- **Description**: Click the mouse at the current position or specified coordinates.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `x` (integer, Optional): 
  - `y` (integer, Optional): 
  - `button` (string, Optional): left, right, double
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `cursor_get_position`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_cursor_get_position`
- **Category**: **General & Skill Execution**
- **Description**: Get current mouse cursor (X, Y) coordinates on screen.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `cursor_move`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_cursor_move`
- **Category**: **General & Skill Execution**
- **Description**: Move the mouse cursor to specific screen coordinates.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `x` (integer, Required): 
  - `y` (integer, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `custom_command_add`
- **Implementation File**: `tools/custom_command_tools.py`
- **Function**: `tool_custom_command_add`
- **Category**: **General & Skill Execution**
- **Description**: Add or update a custom command. You can define triggers (including variable anchors like $QUERY), aliases, and a list of actions (type: speak, open_url, open_app, run_command, press_keys, hotkey).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `trigger` (string, Required): Trigger phrase, e.g., 'search google for $QUERY'
  - `aliases` (array, Optional): Optional list of alias triggers
  - `actions` (array, Required): Sequential actions to execute
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `custom_command_delete`
- **Implementation File**: `tools/custom_command_tools.py`
- **Function**: `tool_custom_command_delete`
- **Category**: **General & Skill Execution**
- **Description**: Delete a custom command using its trigger phrase.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `trigger` (string, Required): The exact trigger phrase of the command to delete
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `custom_command_list`
- **Implementation File**: `tools/custom_command_tools.py`
- **Function**: `tool_custom_command_list`
- **Category**: **General & Skill Execution**
- **Description**: List all user-configured custom voice and text commands.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `delete_calendar_event`
- **Implementation File**: `tools/calendar_tools.py`
- **Function**: `tool_delete_calendar_event`
- **Category**: **General & Skill Execution**
- **Description**: Delete a calendar event by ID.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `event_id` (integer, Required): Calendar event ID to delete
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `desktop_control`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_desktop_control`
- **Category**: **General & Skill Execution**
- **Description**: Wallpaper management or desktop organizing utilities.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): set_wallpaper, organize
  - `path` (string, Optional): 
  - `task` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `dev_agent`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_dev_agent`
- **Category**: **General & Skill Execution**
- **Description**: Build complete multi-file software projects autonomously.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `description` (string, Required): 
  - `language` (string, Optional): 
  - `project_name` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `display_resolution`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_display_resolution`
- **Category**: **Vision & Desktop Operator**
- **Description**: Query screen display dimensions (width, height).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `dns_enum`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_dns_enum`
- **Category**: **Security & Network Recon**
- **Description**: Enumerate DNS records for a domain (scope-checked).
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `domain` (string, Required): Target domain
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `document_creator`
- **Implementation File**: `tools/doc_tools.py`
- **Function**: `document_creator`
- **Category**: **General & Skill Execution**
- **Description**: Universal Executive Document Engine. Creates styled Word (.docx), PDF (.pdf), HTML (.html), and Markdown (.md) documents with Cover Pages, Styled Tables, Callouts, Code Blocks, and Auto-Launch.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (8)**:
  - `title` (string, Required): Title of the document
  - `subtitle` (string, Optional): Subtitle or tagline for the document
  - `author` (string, Optional): Author name (default: BR JARVIS AI)
  - `content` (string, Required): Main text content in structured Markdown (headings, bullets, tables, callouts)
  - `filename` (string, Optional): Target filename or relative path (e.g., workspace/Books/Startup_Book.docx)
  - `format` (string, Optional): Output format: docx | pdf | html | md (default: docx)
  - `cover_page` (boolean, Optional): Whether to include an executive cover page (default: true)
  - `auto_open` (boolean, Optional): Whether to auto-launch the generated file (default: true)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `edit_image`
- **Implementation File**: `tools/image_tools.py`
- **Function**: `tool_edit_image`
- **Category**: **General & Skill Execution**
- **Description**: Edit an existing image using AI. Supports inpainting with optional mask.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `image_path` (string, Required): Path to the source image to edit
  - `prompt` (string, Required): What to change in the image
  - `mask_path` (string, Optional): Optional path to mask image for inpainting
  - `provider` (string, Optional): Provider: 'openai' (default)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `email_assistant`
- **Implementation File**: `actions/email_assistant.py`
- **Function**: `tool_email_assistant`
- **Category**: **Communication & CRM**
- **Description**: Send emails via SMTP, check recent inbox messages via IMAP, or draft mail templates.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (5)**:
  - `action` (string, Required): send, check, draft
  - `to` (string, Optional): Recipient email address (required for action='send')
  - `subject` (string, Optional): Subject of the email (required for action='send'/'draft')
  - `body` (string, Optional): Body text of the email
  - `limit` (integer, Optional): Max emails to check (default 5)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `execute_system_automation`
- **Implementation File**: `tools/automation_tools.py`
- **Function**: `tool_execute_system_automation`
- **Category**: **Process & OS Execution**
- **Description**: Execute automated PowerShell or system shell command scripts with timeout and output capture.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `command` (string, Required): Shell command line or PowerShell snippet to execute
  - `timeout` (integer, Optional): Maximum execution time in seconds (default: 30)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `export_chat`
- **Implementation File**: `tools/export_tools.py`
- **Function**: `tool_export_chat`
- **Category**: **Security & Network Recon**
- **Description**: Export the current conversation/chat history to a file. Formats: pdf, md (Markdown), html, txt.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `format` (string, Required): Output file format: 'pdf', 'md', 'html', 'txt' (default: pdf)
  - `max_turns` (integer, Optional): Maximum conversation turns to export (default: 100)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `fast_file_search`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **Filesystem & Storage**
- **Description**: High-speed desktop file search by filename or text content. Args: 'action' ('name' or 'content'), 'query' (search keyword), 'search_path' (optional directory path), 'extension' (optional file extension).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (4)**:
  - `action` (string, Required): 
  - `query` (string, Required): Search keyword or filename
  - `search_path` (string, Optional): Root directory path
  - `extension` (string, Optional): File extension filter
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `fetch_page`
- **Implementation File**: `tools/web_tools.py`
- **Function**: `tool_fetch_page`
- **Category**: **General & Skill Execution**
- **Description**: Fetch and extract text content from a URL using a headless browser.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `url` (string, Required): URL to fetch
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `fetch_raw`
- **Implementation File**: `tools/web_tools.py`
- **Function**: `tool_fetch_raw`
- **Category**: **General & Skill Execution**
- **Description**: Fetch raw HTML/text content from a URL via HTTP GET.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `url` (string, Required): URL to fetch
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `file_controller`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_file_controller`
- **Category**: **Filesystem & Storage**
- **Description**: Perform file and directory management actions (read, write, delete, move, create_dir, list).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (5)**:
  - `action` (string, Required): read, write, delete, move, create_dir, list
  - `path` (string, Optional): Target file or directory path
  - `name` (string, Optional): File or directory name
  - `content` (string, Optional): Content for write operations
  - `destination` (string, Optional): Destination path for move operations
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `file_list`
- **Implementation File**: `tools/file_tools.py`
- **Function**: `tool_file_list`
- **Category**: **Filesystem & Storage**
- **Description**: List files in a workspace directory.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `path` (string, Optional): Relative directory path (default: root)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `file_read`
- **Implementation File**: `tools/file_tools.py`
- **Function**: `tool_file_read`
- **Category**: **Filesystem & Storage**
- **Description**: Read a file from the workspace.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `path` (string, Required): Relative path within the workspace
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `file_search_semantic`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **Filesystem & Storage**
- **Description**: Fast natural language semantic file search across workspace files. Args: 'query' (search term or file description).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `query` (string, Required): Natural language file description or keywords
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `file_write`
- **Implementation File**: `tools/file_tools.py`
- **Function**: `tool_file_write`
- **Category**: **Filesystem & Storage**
- **Description**: Write content to a file in the workspace.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `path` (string, Required): Relative path within the workspace
  - `content` (string, Required): Content to write
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `flight_finder`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_flight_finder`
- **Category**: **General & Skill Execution**
- **Description**: Search flights details between origin and destination on a specific date.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `origin` (string, Required): 
  - `destination` (string, Required): 
  - `date` (string, Required): Format: YYYY-MM-DD
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `focus_window`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_focus_window`
- **Category**: **Vision & Desktop Operator**
- **Description**: Bring a window to the foreground by title.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `title` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `game_updater`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_game_updater`
- **Category**: **General & Skill Execution**
- **Description**: Manage Steam/Epic games (updating, launching, checking status).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): launch, update, status
  - `platform` (string, Required): steam, epic
  - `game_name` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `generate_image`
- **Implementation File**: `tools/image_tools.py`
- **Function**: `tool_generate_image`
- **Category**: **General & Skill Execution**
- **Description**: Generate an AI image from a text description. Providers: gemini (Imagen), openai (DALL-E 3), stability (Stable Diffusion). Returns file paths of generated images.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `prompt` (string, Required): Detailed description of the image to generate
  - `provider` (string, Optional): Provider: 'auto', 'gemini', 'openai', 'stability' (default: auto)
  - `size` (string, Optional): Image size: '1024x1024', '1792x1024', '1024x1792' (default: 1024x1024)
  - `style` (string, Optional): Style: 'vivid' or 'natural' (default: vivid)
  - `negative_prompt` (string, Optional): What to avoid in the image
  - `num_images` (integer, Optional): Number of images (1-4, default: 1)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `generate_project_product_analysis`
- **Implementation File**: `tools/doc_tools.py`
- **Function**: `generate_project_product_analysis`
- **Category**: **General & Skill Execution**
- **Description**: Generate a complete Product Analysis Report for B.R. JARVIS as Word (.docx) and PDF (.pdf) documents and auto-open them.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `generate_report`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_generate_report`
- **Category**: **Security & Network Recon**
- **Description**: Generate a professional penetration test report in markdown.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `data` (object, Required): Report data dict
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `generate_video`
- **Implementation File**: `tools/video_tools.py`
- **Function**: `tool_generate_video`
- **Category**: **General & Skill Execution**
- **Description**: Generate an AI video from a text description. Providers: veo (Google Veo), kling (Kling AI). Returns file path of the generated video.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `prompt` (string, Required): Detailed description of the video to generate
  - `provider` (string, Optional): Provider: 'auto', 'veo', 'kling' (default: auto)
  - `duration` (integer, Optional): Duration in seconds (default: 5)
  - `resolution` (string, Optional): Resolution: '720p' or '1080p' (default: 1080p)
  - `aspect_ratio` (string, Optional): Aspect ratio: '16:9', '9:16', '1:1' (default: 16:9)
  - `image_path` (string, Optional): Optional reference image for image-to-video generation
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `generate_walkthrough`
- **Implementation File**: `tools/doc_tools.py`
- **Function**: `generate_walkthrough`
- **Category**: **General & Skill Execution**
- **Description**: Generate a rich GitHub-flavored Markdown Walkthrough document (walkthrough.md) documenting technical changes, verification results, and file links.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `title` (string, Required): Title of the walkthrough
  - `summary` (string, Optional): High-level summary of work accomplished
  - `changes` (string, Required): Detailed description or markdown list of changes made
  - `verification` (string, Optional): Verification steps and automated test results
  - `filename` (string, Optional): Target filename, default is walkthrough.md
  - `auto_open` (boolean, Optional): Whether to auto-open the generated walkthrough file
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_app_launch_history`
- **Implementation File**: `tools/app_tracker_tools.py`
- **Function**: `tool_get_app_launch_history`
- **Category**: **General & Skill Execution**
- **Description**: Retrieve the persistent log of application start events recorded on this machine. Args: 'limit' (integer), 'app_name' (optional filter).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (2)**:
  - `limit` (integer, Optional): Number of recent start events to return (default: 30)
  - `app_name` (string, Optional): Optional application name filter
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_app_usage_statistics`
- **Implementation File**: `tools/app_tracker_tools.py`
- **Function**: `tool_get_app_usage_statistics`
- **Category**: **General & Skill Execution**
- **Description**: Retrieve analytics on application starts, including total launches, most launched apps, and recent activity.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_gmail_auth_status`
- **Implementation File**: `tools/gmail_auth_tools.py`
- **Function**: `tool_get_gmail_auth_status`
- **Category**: **General & Skill Execution**
- **Description**: Check whether a Gmail account is currently logged in, showing active email address and authentication method.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_pending_channel_actions`
- **Implementation File**: `tools/proactive_listener_tools.py`
- **Function**: `get_pending_channel_actions_action`
- **Category**: **General & Skill Execution**
- **Description**: Retrieve all unhandled incoming Email and WhatsApp messages requiring user opinion or approval.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_system_diagnostics`
- **Implementation File**: `tools/process_tools.py`
- **Function**: `get_system_diagnostics`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Retrieve real-time system performance telemetry: CPU, RAM, Top 10 memory-hogging processes, disk usage, and active tasks.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `top_n` (integer, Optional): Number of top memory-consuming processes to report (default: 10)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `get_workspace_timeline`
- **Implementation File**: `tools/workspace_tools.py`
- **Function**: `get_workspace_timeline`
- **Category**: **General & Skill Execution**
- **Description**: Retrieve the chronological workspace action timeline stream (file creations, code generations, model calls).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `limit` (integer, Optional): Number of recent events to retrieve (default: 15)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `git_repo_mgr`
- **Implementation File**: `tools/git_repo_tool.py`
- **Function**: `git_repo_mgr`
- **Category**: **General & Skill Execution**
- **Description**: Inspect git repository status, view diffs/logs, switch branches, create branches, stage changes, create commits, and pull/push.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `action` (string, Required): Git operation to perform
  - `repo_dir` (string, Optional): Target repository directory path (default: current workspace)
  - `commit_msg` (string, Optional): Commit message for 'commit' action
  - `branch` (string, Optional): Branch name for 'checkout', 'create_branch', 'pull', or 'push'
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `github_create_issue`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `github_create_issue`
- **Category**: **General & Skill Execution**
- **Description**: Create a new issue on GitHub repository.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `repo` (string, Required): Repository in format 'owner/repo'
  - `title` (string, Required): Issue title
  - `body` (string, Optional): Issue description content
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `github_list_prs`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `github_list_prs`
- **Category**: **General & Skill Execution**
- **Description**: List open Pull Requests or Issues in a GitHub repository.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `repo` (string, Optional): Repository in format 'owner/repo' (default: 'bharthraj1412/BrJarvis')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_list_unread`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `gmail_list_unread`
- **Category**: **Filesystem & Storage**
- **Description**: List unread emails from Gmail inbox with subject, sender, and snippet.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `max_results` (integer, Optional): Maximum number of unread emails to retrieve (default: 5)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_login`
- **Implementation File**: `tools/gmail_auth_tools.py`
- **Function**: `tool_gmail_login`
- **Category**: **General & Skill Execution**
- **Description**: Log in to Gmail. Mode 'browser' opens Google Sign-In page in browser. Mode 'credentials' saves email and Google App Password for automated email access.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `mode` (string, Required): Login mode: 'browser' for interactive sign-in, or 'credentials' for App Password
  - `email` (string, Optional): Gmail email address (required for credentials mode)
  - `app_password` (string, Optional): 16-character Google App Password (required for credentials mode)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_logout`
- **Implementation File**: `tools/gmail_auth_tools.py`
- **Function**: `tool_gmail_logout`
- **Category**: **General & Skill Execution**
- **Description**: Sign out of Gmail and clear stored credentials and session tokens from local storage.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_reply`
- **Implementation File**: `tools/web_app_tools.py`
- **Function**: `gmail_reply`
- **Category**: **General & Skill Execution**
- **Description**: Search Gmail inbox for an email thread and send a reply message.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `query` (string, Required): Search term or sender name/subject to locate email
  - `reply_text` (string, Required): Reply text message body
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_send`
- **Implementation File**: `tools/web_app_tools.py`
- **Function**: `gmail_send`
- **Category**: **General & Skill Execution**
- **Description**: Compose and send an email via Gmail online in the browser.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `to` (string, Required): Recipient email address
  - `subject` (string, Required): Email subject line
  - `body` (string, Required): Email body content
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `gmail_send_email`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `gmail_send_email`
- **Category**: **Communication & CRM**
- **Description**: Draft or send an email via Gmail connector.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `to` (string, Required): Recipient email address
  - `subject` (string, Required): Email subject line
  - `body` (string, Required): Email body content
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `headers_audit`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_headers_audit`
- **Category**: **General & Skill Execution**
- **Description**: Audit HTTP security headers of a URL (scope-checked).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `url` (string, Required): Target URL
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `init_project_workspace`
- **Implementation File**: `tools/workspace_tools.py`
- **Function**: `init_project_workspace`
- **Category**: **General & Skill Execution**
- **Description**: Create a standardized self-contained Project Workspace (source, docs, architecture, api, tests, build) inside BR_WORKSPACE/Projects/.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `project_name` (string, Required): Name of the project workspace to create
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `keyboard_hotkey`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_keyboard_hotkey`
- **Category**: **General & Skill Execution**
- **Description**: Press a key combination (e.g., ctrl+c, alt+tab).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `keys` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `keyboard_key_down`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_keyboard_key_down`
- **Category**: **General & Skill Execution**
- **Description**: Press and hold a specific key down.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `key` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `keyboard_key_up`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_keyboard_key_up`
- **Category**: **General & Skill Execution**
- **Description**: Release a held key.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `key` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `keyboard_press`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_keyboard_press`
- **Category**: **General & Skill Execution**
- **Description**: Press a single key (enter, tab, escape, etc.).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `key` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `keyboard_type`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_keyboard_type`
- **Category**: **General & Skill Execution**
- **Description**: Type text at the current cursor position.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `text` (string, Required): 
  - `clear_first` (boolean, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `kill_process`
- **Implementation File**: `tools/process_tools.py`
- **Function**: `kill_process`
- **Category**: **Process & OS Execution**
- **Description**: Kill or terminate a running process by Process ID (PID) or process name.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `identifier` (string, Required): PID (e.g. '1234') or Process Name (e.g. 'notepad.exe')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_agent_types`
- **Implementation File**: `tools/agent_tools.py`
- **Function**: `tool_list_agent_types`
- **Category**: **General & Skill Execution**
- **Description**: List all available agent types (built-in and custom).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_agents`
- **Implementation File**: `tools/agent_tools.py`
- **Function**: `tool_list_agents`
- **Category**: **General & Skill Execution**
- **Description**: List all sub-agent tasks and their statuses.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_calendar_events`
- **Implementation File**: `tools/calendar_tools.py`
- **Function**: `tool_list_calendar_events`
- **Category**: **General & Skill Execution**
- **Description**: List upcoming calendar events and tasks. Args: 'days' (integer number of days to look ahead, default: 7).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `days` (integer, Optional): Number of days to retrieve (default: 7)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_generated_videos`
- **Implementation File**: `tools/video_tools.py`
- **Function**: `tool_list_generated_videos`
- **Category**: **General & Skill Execution**
- **Description**: List all previously generated AI videos.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_installed_applications`
- **Implementation File**: `tools/app_analyzer_tools.py`
- **Function**: `tool_list_installed_applications`
- **Category**: **General & Skill Execution**
- **Description**: Scan and list all installed applications on the system (Windows Registry/Start Menu, macOS Apps, Linux desktop files). Args: optional 'query' filter string.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `query` (string, Optional): Optional keyword filter to search app names
  - `limit` (integer, Optional): Maximum number of apps to return (default: 50)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_monitors`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_list_monitors`
- **Category**: **General & Skill Execution**
- **Description**: List all available monitors with resolution and position.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_running_applications`
- **Implementation File**: `tools/app_analyzer_tools.py`
- **Function**: `tool_list_running_applications`
- **Category**: **Process & OS Execution**
- **Description**: List all active running desktop applications and processes on the system with PID, Memory usage, CPU %, and Path.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `gui_only` (boolean, Optional): Whether to filter system background noise (default: true)
  - `top_n` (integer, Optional): Number of top running apps to display (default: 25)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `list_skills`
- **Implementation File**: `tools/skills_tools.py`
- **Function**: `tool_list_skills`
- **Category**: **General & Skill Execution**
- **Description**: List all available user-invocable skills.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `live_os_control`
- **Implementation File**: `tools/live_os_tools.py`
- **Function**: `tool_live_os_control`
- **Category**: **General & Skill Execution**
- **Description**: Launch autonomous Live OS Visual Control loop ('Antigravity Mode'). Performs real-time screen perception, planning, and mouse/keyboard action execution until goal is achieved.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `goal` (string, Required): Objective or task to accomplish on the computer desktop.
  - `max_steps` (integer, Optional): Maximum step limit (default 20).
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `live_screen_analyze`
- **Implementation File**: `tools/live_os_tools.py`
- **Function**: `tool_live_screen_analyze`
- **Category**: **Vision & Desktop Operator**
- **Description**: Analyze the current screen using vision AI and return a structured visual breakdown of open windows, interactive UI elements, and desktop state.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `longform_builder`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **General & Skill Execution**
- **Description**: Build comprehensive multi-volume books, technical manuals, research publications, and project toolkits automatically. Args: 'title' (book title), 'description' (topic focus), 'year' (publication year), 'folder_name' (optional output subfolder).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `title` (string, Required): Title of the book or guide
  - `description` (string, Required): Detailed topic focus
  - `year` (string, Optional): Target year (default: '2026')
  - `folder_name` (string, Optional): Output folder name inside ./workspace/
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `manage_email_contacts`
- **Implementation File**: `tools/smart_email_tools.py`
- **Function**: `tool_manage_email_contacts`
- **Category**: **Communication & CRM**
- **Description**: Add or list saved email contact address mappings. Args: 'action' ('add' or 'list'), 'name' (contact name), 'email_address' (email address).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): Action to perform
  - `name` (string, Optional): Contact display name
  - `email_address` (string, Optional): Contact email address
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `manage_telegram_contacts`
- **Implementation File**: `tools/telegram_tools.py`
- **Function**: `tool_manage_telegram_contacts`
- **Category**: **Communication & CRM**
- **Description**: Add a new Telegram contact mapping (name → chat_id or @username) or list all saved Telegram contacts. Use 'add' to save a new contact, 'list' to see all saved contacts. A chat_id can be discovered using the telegram_get_updates tool.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): Action to perform: 'add' or 'list'
  - `name` (string, Optional): Contact display name (e.g. 'Appa', 'John', 'Work Group')
  - `chat_id` (string, Optional): Telegram chat_id (numeric, e.g. '123456789') or @username (e.g. '@johnsmith'). Use telegram_get_updates to discover chat_ids.
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `manage_whatsapp_contacts`
- **Implementation File**: `tools/whatsapp_tools.py`
- **Function**: `tool_manage_whatsapp_contacts`
- **Category**: **Communication & CRM**
- **Description**: Add a new contact mapping or list saved contacts. Args: 'action' ('add' or 'list'), 'name' (contact name), 'phone_number' (phone number).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `action` (string, Required): Action to perform
  - `name` (string, Optional): Contact display name
  - `phone_number` (string, Optional): Phone number with country code
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `mcp_call_tool`
- **Implementation File**: `tools/mcp_connector.py`
- **Function**: `mcp_call_tool_action`
- **Category**: **General & Skill Execution**
- **Description**: Connect to an external Model Context Protocol (MCP) server and execute a tool call.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `server_url` (string, Required): MCP server base URL
  - `tool_name` (string, Required): Target tool name on MCP server
  - `args` (object, Optional): Tool parameters payload
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `memory_delete`
- **Implementation File**: `tools/memory_tools.py`
- **Function**: `tool_memory_delete`
- **Category**: **General & Skill Execution**
- **Description**: Delete a persistent memory entry by name.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `name` (string, Required): 
  - `scope` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `memory_list`
- **Implementation File**: `tools/memory_tools.py`
- **Function**: `tool_memory_list`
- **Category**: **General & Skill Execution**
- **Description**: List all persistent memory entries.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `scope` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `memory_save`
- **Implementation File**: `tools/memory_tools.py`
- **Function**: `tool_memory_save`
- **Category**: **General & Skill Execution**
- **Description**: Save a persistent memory entry.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (5)**:
  - `name` (string, Required): 
  - `type` (string, Required): 
  - `description` (string, Required): 
  - `content` (string, Required): 
  - `scope` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `memory_search`
- **Implementation File**: `tools/memory_tools.py`
- **Function**: `tool_memory_search`
- **Category**: **Web & Browser Automation**
- **Description**: Search persistent memories by keyword.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (2)**:
  - `query` (string, Required): 
  - `max_results` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `mouse_drag`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_mouse_drag`
- **Category**: **General & Skill Execution**
- **Description**: Click and drag from one point to another.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `x1` (integer, Required): 
  - `y1` (integer, Required): 
  - `x2` (integer, Required): 
  - `y2` (integer, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `mouse_scroll`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_mouse_scroll`
- **Category**: **General & Skill Execution**
- **Description**: Scroll the mouse wheel.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `direction` (string, Optional): 
  - `amount` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `ms365_control`
- **Implementation File**: `tools/web_app_tools.py`
- **Function**: `ms365_control`
- **Category**: **General & Skill Execution**
- **Description**: Launch and interact with Microsoft 365 / Office Online web apps (Word, Excel, PowerPoint, Outlook, Home).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `app` (string, Required): App name: 'word', 'excel', 'powerpoint', 'outlook', or 'home'
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `native_audio_meter`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_native_audio_meter`
- **Category**: **General & Skill Execution**
- **Description**: High-speed C-native RMS audio energy calculator for microphone and voice level monitoring.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `samples` (array, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `native_grid_transform`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_native_grid_transform`
- **Category**: **General & Skill Execution**
- **Description**: Transform target visual grid coordinates to screen pixel coordinates via C extension.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (5)**:
  - `gx` (integer, Required): 
  - `gy` (integer, Required): 
  - `grid_size` (integer, Optional): 
  - `sw` (integer, Required): 
  - `sh` (integer, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `native_hash_fast`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_native_hash_fast`
- **Category**: **General & Skill Execution**
- **Description**: High-speed C-native FNV-1a hashing for screen frame delta detection or content integrity.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `text` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `native_proc_telemetry`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_native_proc_telemetry`
- **Category**: **General & Skill Execution**
- **Description**: Low-overhead C-native process page count and RAM usage reader.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `pid` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `nmap_scan`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_nmap_scan`
- **Category**: **Security & Network Recon**
- **Description**: Run an nmap service scan on a host (scope-checked, requires nmap installed).
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `host` (string, Required): Target host
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `notion_create_page`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `notion_create_page`
- **Category**: **General & Skill Execution**
- **Description**: Create a new page in a Notion database or workspace root.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `title` (string, Required): Title of the new Notion page
  - `content` (string, Optional): Markdown body content of the page
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `notion_search_pages`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `notion_search_pages`
- **Category**: **Web & Browser Automation**
- **Description**: Search Notion workspace for pages, databases, or documentation notes.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `query` (string, Required): Search query for Notion workspace
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `open_app`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_open_app`
- **Category**: **General & Skill Execution**
- **Description**: Launch any application on the host machine.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `app_name` (string, Required): Name or path of the application to launch
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `open_workspace_file`
- **Implementation File**: `tools/workspace_tools.py`
- **Function**: `open_workspace_file`
- **Category**: **Filesystem & Storage**
- **Description**: Smart natural language file opener for BR_WORKSPACE/. Accepts query like 'open yesterday's API design' or 'open RouteX architecture'.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `query` (string, Required): Natural language query or file description
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `pdf_tool`
- **Implementation File**: `tools/pdf_tools.py`
- **Function**: `pdf_tool`
- **Category**: **General & Skill Execution**
- **Description**: Comprehensive PDF operations tool - merge, split, compress, convert (PDF<->Word/Excel/PPTX/JPG/HTML/Markdown), watermark, rotate, protect, unlock, OCR, redact, crop, compare, repair, page numbers, forms, summarize, translate, sign. Use 'action' to specify the operation. Always provide 'input_path' (or 'input_paths' for merge/jpg_to_pdf).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (18)**:
  - `action` (string, Required): The PDF operation to perform.
  - `input_path` (string, Optional): Path to input PDF or document file.
  - `input_paths` (array, Optional): List of input paths (required for merge and jpg_to_pdf actions).
  - `output_path` (string, Optional): Optional output file path. Auto-generated if not provided.
  - `output_dir` (string, Optional): Output directory for multi-file operations (split, pdf_to_jpg).
  - `pages` (string, Optional): Page selection: '1', '1,3,5', '2-5', or list of ints.
  - `password` (string, Optional): Password for protect/unlock operations.
  - `text` (string, Optional): Text for watermark, edit, or redact operations.
  - `angle` (integer, Optional): Rotation angle in degrees (for rotate action).
  - `dpi` (integer, Optional): DPI resolution for image rendering (default: 150).
  - `language` (string, Optional): Target language for translate action.
  - `page_order` (array, Optional): New page order (1-indexed) for organize action.
  - `delete_pages` (array, Optional): Pages to delete (1-indexed) for organize action.
  - `fields` (object, Optional): Field name -> value mapping for pdf_forms fill action.
  - `rect` (array, Optional): Crop rectangle [x0, y0, x1, y1] in points for crop action.
  - `html` (string, Optional): HTML content string for html_to_pdf action.
  - `patterns` (array, Optional): Text patterns to redact for redact action.
  - `path2` (string, Optional): Second PDF path for compare action.
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `port_scan`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_port_scan`
- **Category**: **Security & Network Recon**
- **Description**: Scan TCP ports on a host (scope-checked). Returns open/closed status.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `host` (string, Required): Target host IP or hostname
  - `ports` (array, Optional): List of port numbers (default: common ports)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `qa_assert_page_state`
- **Implementation File**: `tools/qa_testing_tool.py`
- **Function**: `qa_assert_page_state`
- **Category**: **General & Skill Execution**
- **Description**: Assert background page conditions (URL match, text presence, selector existence, no console errors).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `url` (string, Required): Target URL to open and evaluate
  - `url_contains` (string, Optional): Expected substring in final page URL
  - `text_visible` (string, Optional): Expected visible text on page
  - `selector_exists` (string, Optional): Expected CSS selector on page
  - `timeout_ms` (integer, Optional): Navigation timeout in ms (default 15000)
  - `fail_on_console_error` (boolean, Optional): Fail test if JS console errors detected (default false)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `qa_generate_report`
- **Implementation File**: `tools/qa_testing_tool.py`
- **Function**: `qa_generate_report`
- **Category**: **Security & Network Recon**
- **Description**: Generate a comprehensive Markdown QA Audit Report from test execution results.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `test_name` (string, Required): Title of the test suite or application
  - `results_json` (string, Required): JSON string or payload of test results
  - `report_filename` (string, Optional): Filename for markdown report (default qa_report.md)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `qa_run_browser_test`
- **Implementation File**: `tools/qa_testing_tool.py`
- **Function**: `qa_run_browser_test`
- **Category**: **Web & Browser Automation**
- **Description**: Run an autonomous background end-to-end browser test flow on a target URL or local dev server.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `url` (string, Required): Target website URL or local server (e.g. http://localhost:3000)
  - `steps` (array, Optional): List of test step objects e.g. [{'action': 'click', 'selector': '#login'}, {'action': 'type', 'selector': '#user', 'value': 'admin'}, {'action': 'assert_text', 'text': 'Dashboard'}]
  - `headless` (boolean, Optional): Run in background without opening window (default true)
  - `screenshot_name` (string, Optional): Filename for final test screenshot (default test_result.png)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_chat`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_chat`
- **Category**: **General & Skill Execution**
- **Description**: Chat with your personal document library. Ask questions and get AI-generated answers based on your ingested documents.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `question` (string, Required): Your question about the documents
  - `doc_filter` (string, Optional): Optional: filter to a specific document
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_delete`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_delete`
- **Category**: **General & Skill Execution**
- **Description**: Delete a document from the local RAG library by name.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `doc_name` (string, Required): Name of the document to delete
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_ingest`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_ingest`
- **Category**: **General & Skill Execution**
- **Description**: Ingest a document (PDF, DOCX, TXT, CSV, MD) into the local RAG library for later querying. Provide the file path.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `file_path` (string, Required): Path to the document file to ingest
  - `doc_name` (string, Optional): Optional custom name for the document
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_ingest_webpage`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_ingest_webpage`
- **Category**: **Web & Browser Automation**
- **Description**: Ingest a webpage into the local RAG library by fetching and indexing its content.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `url` (string, Required): URL of the webpage to ingest
  - `doc_name` (string, Optional): Optional custom name for the document
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_list`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_list`
- **Category**: **General & Skill Execution**
- **Description**: List all documents currently in the local RAG library.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `rag_query`
- **Implementation File**: `tools/rag_tools.py`
- **Function**: `tool_rag_query`
- **Category**: **General & Skill Execution**
- **Description**: Search the local document library for information relevant to a question. Returns the most relevant text chunks.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `question` (string, Required): The search query or question
  - `top_k` (integer, Optional): Number of results (default: 5)
  - `doc_filter` (string, Optional): Optional: filter to a specific document name
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `reminder`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **Communication & CRM**
- **Description**: Set or list smart reminders and desktop toast notifications. Args: 'action' ('add' or 'list'), 'text' (reminder message), 'time_str' (e.g. '9:00 AM', '14:30', 'tomorrow 9am'), 'delay_seconds' (optional integer).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `action` (string, Required): 
  - `text` (string, Optional): Reminder text
  - `time_str` (string, Optional): Target time (e.g. '9am', '14:30')
  - `delay_seconds` (integer, Optional): Delay in seconds
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `respond_channel_action`
- **Implementation File**: `tools/proactive_listener_tools.py`
- **Function**: `respond_channel_action_action`
- **Category**: **General & Skill Execution**
- **Description**: Execute user approval decision ('reply', 'add_to_calendar', or 'dismiss') for a pending message item.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (6)**:
  - `item_id` (string, Required): The unique message ID from pending actions list
  - `decision` (string, Required): 'reply', 'add_to_calendar', or 'dismiss'
  - `custom_reply` (string, Optional): Optional custom message text for reply
  - `event_title` (string, Optional): Optional custom title for calendar event
  - `event_date` (string, Optional): Optional date string for calendar event (e.g., 'tomorrow')
  - `event_time` (string, Optional): Optional time string for calendar event (e.g., '3:00 PM')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `run_automation_workflow`
- **Implementation File**: `tools/automation_tools.py`
- **Function**: `tool_run_automation_workflow`
- **Category**: **Process & OS Execution**
- **Description**: Execute a multi-step macro automation workflow script. Pass steps as a JSON list or array of action objects (e.g. launch_app, sleep, type_text, hotkey, shell).
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `steps` (array, Required): List of step dictionary objects. Example: [{'action': 'launch_app', 'app_name': 'notepad'}, {'action': 'sleep', 'seconds': 1}, {'action': 'type_text', 'text': 'Hello World'}]
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `run_code`
- **Implementation File**: `tools/code_tools.py`
- **Function**: `tool_run_code`
- **Category**: **Process & OS Execution**
- **Description**: Execute code in a sandboxed environment. Supports python, javascript, bash.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `code` (string, Required): The code to execute
  - `lang` (string, Optional): Language: python, javascript, bash (default: python)
  - `timeout` (integer, Optional): Timeout in seconds (default: 30)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `run_skill`
- **Implementation File**: `tools/skills_tools.py`
- **Function**: `tool_run_skill`
- **Category**: **Process & OS Execution**
- **Description**: Execute a named skill (reusable prompt template). Use list_skills to see available skills.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `name` (string, Required): 
  - `args` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `schedule_email`
- **Implementation File**: `tools/smart_email_tools.py`
- **Function**: `tool_schedule_email`
- **Category**: **Communication & CRM**
- **Description**: Schedule an email for future automated sending to any recipient.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `recipient` (string, Required): Recipient email address or contact name
  - `subject` (string, Required): Email subject line
  - `body` (string, Required): Email body content
  - `send_at` (string, Required): Future date/time string (e.g. '2026-08-01 09:00:00' or '14:30')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `schedule_telegram_message`
- **Implementation File**: `tools/telegram_tools.py`
- **Function**: `tool_schedule_telegram_message`
- **Category**: **Communication & CRM**
- **Description**: Schedule a Telegram message to be automatically sent to a contact at a specified future date/time. The message is queued and sent in the background even while JARVIS continues other work.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `recipient` (string, Required): Contact name, @username, or chat_id
  - `message` (string, Required): Message content to send
  - `send_at` (string, Required): Target date/time string. Formats: '2026-08-01 09:00', '2026-08-01 09:00:00', '14:30', '9:00 AM'
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `schedule_whatsapp_message`
- **Implementation File**: `tools/whatsapp_tools.py`
- **Function**: `tool_schedule_whatsapp_message`
- **Category**: **Communication & CRM**
- **Description**: Schedule a WhatsApp message to be automatically sent to a contact at a specified future date/time.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `recipient` (string, Required): Contact name or phone number
  - `message` (string, Required): Message content to send
  - `send_at` (string, Required): Target date/time string (e.g. '2026-08-01 09:00:00' or '14:30')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `scheduler`
- **Implementation File**: `actions/scheduler.py`
- **Function**: `tool_scheduler`
- **Category**: **General & Skill Execution**
- **Description**: Schedule automated goals to run at intervals or specific times.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `action` (string, Required): add, remove, list
  - `schedule` (string, Optional): Time interval, e.g. 'every 10 minutes', 'every day at 9:30am' (required for action='add')
  - `goal` (string, Optional): Goal to execute (required for action='add')
  - `task_id` (integer, Optional): Scheduler task ID to remove (required for action='remove')
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_click`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_screen_click`
- **Category**: **Process & OS Execution**
- **Description**: Find a UI element by description and click on it.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `description` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_describe`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_screen_describe`
- **Category**: **Vision & Desktop Operator**
- **Description**: Get a natural language description of what is on the screen.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_find`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_screen_find`
- **Category**: **Vision & Desktop Operator**
- **Description**: Use AI vision to find a UI element on screen by description. Returns coordinates.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `description` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_process`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_screen_process`
- **Category**: **Process & OS Execution**
- **Description**: Analyze screen or camera feed utilizing vision capabilities.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `text` (string, Optional): 
  - `angle` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_read`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_screen_read`
- **Category**: **Filesystem & Storage**
- **Description**: Read and OCR the entire screen via vision.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_share_start`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_screen_share_start`
- **Category**: **Vision & Desktop Operator**
- **Description**: Start real-time screen sharing over WebSocket.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `port` (integer, Optional): 
  - `monitor` (integer, Optional): 
  - `fps` (integer, Optional): 
  - `quality` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_share_status`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_screen_share_status`
- **Category**: **Vision & Desktop Operator**
- **Description**: Get the current screen sharing status.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `screen_share_stop`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_screen_share_stop`
- **Category**: **Vision & Desktop Operator**
- **Description**: Stop the active screen sharing session.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `search_applications`
- **Implementation File**: `tools/app_analyzer_tools.py`
- **Function**: `tool_search_applications`
- **Category**: **Web & Browser Automation**
- **Description**: Search both installed and currently running applications on the system by keyword.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `query` (string, Required): Application name or keyword to search for
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `search_calendar_events`
- **Implementation File**: `tools/calendar_tools.py`
- **Function**: `tool_search_calendar_events`
- **Category**: **Web & Browser Automation**
- **Description**: Search calendar events by title, description, or location keyword.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `query` (string, Required): Search keyword
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `semantic_file_search`
- **Implementation File**: `tools/file_search_semantic.py`
- **Function**: `file_search_semantic_action`
- **Category**: **Filesystem & Storage**
- **Description**: Search workspace files by natural language keywords, filename patterns, or extensions.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `query` (string, Required): Search query or file pattern
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `send_email`
- **Implementation File**: `tools/smart_email_tools.py`
- **Function**: `tool_send_email`
- **Category**: **Communication & CRM**
- **Description**: Compose and send an email to any recipient email address (e.g. 'alex@example.com') or contact name (e.g. 'Alex', 'Manager'). Args: 'recipient', 'subject', 'body', 'attachment_paths' (optional list of file paths).
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `recipient` (string, Required): Recipient email address or contact name
  - `subject` (string, Required): Email subject line
  - `body` (string, Required): Email body content
  - `attachment_paths` (array, Optional): Optional list of local file paths to attach
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `send_message`
- **Implementation File**: `tools/agent_tools.py`
- **Function**: `tool_send_message`
- **Category**: **Communication & CRM**
- **Description**: Send a follow-up message to a running background agent.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `to` (string, Required): 
  - `message` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `send_telegram`
- **Implementation File**: `tools/telegram_tools.py`
- **Function**: `tool_send_telegram`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Send a Telegram message to any contact, @username, or chat_id. NEVER use open_app or run_code to send Telegram messages; ALWAYS use send_telegram. Supports saved contact names (e.g. 'Appa', 'Mom', 'John'), @usernames (e.g. '@johnsmith'), numeric chat_ids, and group/channel IDs. Requires TELEGRAM_BOT_TOKEN in .env (get it from @BotFather). Falls back to Telegram desktop app automation if no bot token is configured.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `recipient` (string, Required): Contact name (e.g. 'Appa'), @username (e.g. '@johnsmith'), or numeric chat_id (e.g. '123456789')
  - `message` (string, Required): Message content to send (supports Markdown formatting)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `send_whatsapp`
- **Implementation File**: `tools/whatsapp_tools.py`
- **Function**: `tool_send_whatsapp`
- **Category**: **General & Skill Execution**
- **Description**: Send a WhatsApp message or greeting directly to any contact name (e.g. 'Appa', 'Mom', 'John') or phone number. NEVER use open_app or run_code to send WhatsApp messages; ALWAYS use send_whatsapp.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `recipient` (string, Required): Contact name or phone number with country code
  - `message` (string, Required): Message content to send
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `slack_send_message`
- **Implementation File**: `tools/app_connectors.py`
- **Function**: `slack_send_message`
- **Category**: **Communication & CRM**
- **Description**: Post a message to a Slack or Discord dev channel.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `channel` (string, Required): Channel name e.g. '#dev-announcements'
  - `message` (string, Required): Message text to post
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `smart_click`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_smart_click`
- **Category**: **Process & OS Execution**
- **Description**: Smartly click a UI element by its natural language description.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `description` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `spawn_agent`
- **Implementation File**: `tools/agent_tools.py`
- **Function**: `tool_spawn_agent`
- **Category**: **General & Skill Execution**
- **Description**: Spawn a sub-agent to handle a task autonomously. NOTE: available in CLI mode (start.py cli). Types: general-purpose, coder, reviewer, researcher, tester, editor, sysadmin, devops.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (4)**:
  - `prompt` (string, Required): 
  - `agent_type` (string, Optional): 
  - `name` (string, Optional): 
  - `wait` (boolean, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `start_multichannel_listener`
- **Implementation File**: `tools/proactive_listener_tools.py`
- **Function**: `start_multichannel_listener_action`
- **Category**: **General & Skill Execution**
- **Description**: Start the proactive background listener monitoring incoming Emails and WhatsApp messages.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `poll_interval` (integer, Optional): Polling interval in seconds (default: 30)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `stop_multichannel_listener`
- **Implementation File**: `tools/proactive_listener_tools.py`
- **Function**: `stop_multichannel_listener_action`
- **Category**: **General & Skill Execution**
- **Description**: Stop the proactive background listener.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `system_cleanup`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_system_cleanup`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Clean temporary cache files, old log files, and build artifacts to reclaim disk space.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `clean_temp` (boolean, Optional): 
  - `clean_pycache` (boolean, Optional): 
  - `clean_logs` (boolean, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `system_diagnostic`
- **Implementation File**: `tools/system_diagnostic_tool.py`
- **Function**: `system_diagnostic`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Inspect system health, CPU/RAM usage, top memory-hogging processes, disk space, and open network sockets.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `aspect` (string, Required): System telemetry aspect to query
  - `top_n` (integer, Optional): Number of top processes to return (default: 5)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `system_health`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Retrieve system health metrics including CPU load, RAM usage, storage, and battery state.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `system_monitor`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_system_monitor`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Get system health info: CPU, RAM, disk, network, top processes.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `action` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `system_optimizer`
- **Implementation File**: `tools/system_tools.py`
- **Function**: `tool_system_optimizer`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Run automated RAM, garbage collection, and temporary file cache optimization. Returns memory stats.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `action` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `take_screenshot`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_take_screenshot`
- **Category**: **Vision & Desktop Operator**
- **Description**: Capture a screenshot of the current screen.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `path` (string, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `telegram_bot_info`
- **Implementation File**: `tools/telegram_tools.py`
- **Function**: `tool_telegram_bot_info`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Check the status of the configured Telegram bot and get a shareable link for contacts to initiate messaging. Validates the TELEGRAM_BOT_TOKEN. Use this to verify the bot is working correctly.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (0)**:
  - None (Zero-parameter tool)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `telegram_get_updates`
- **Implementation File**: `tools/telegram_tools.py`
- **Function**: `tool_telegram_get_updates`
- **Category**: **System Diagnostics & Maintenance**
- **Description**: Fetch recent messages received by the Telegram bot to discover chat_ids of users who have interacted with it. Use this to find the numeric chat_id needed to add a contact or send a message. Users must first send any message (e.g. /start) to the bot on Telegram.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (1)**:
  - `limit` (integer, Optional): Number of recent updates to fetch (default: 10, max: 100)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `transcribe_batch`
- **Implementation File**: `tools/transcription_tools.py`
- **Function**: `tool_transcribe_batch`
- **Category**: **General & Skill Execution**
- **Description**: Transcribe multiple audio/video files in batch. Returns results for each file.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `file_paths` (array, Required): List of paths to audio/video files
  - `language` (string, Optional): Language code or 'auto' (default: auto)
  - `output_format` (string, Optional): Output format (default: txt)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `transcribe_file`
- **Implementation File**: `tools/transcription_tools.py`
- **Function**: `tool_transcribe_file`
- **Category**: **Filesystem & Storage**
- **Description**: Transcribe an audio or video file to text offline using local Whisper. Supports MP3, WAV, M4A, MP4, MKV, AVI, WEBM. Outputs TXT, SRT subtitles, VTT, or JSON.
- **Risk Level**: **MODERATE_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (3)**:
  - `file_path` (string, Required): Path to the audio or video file
  - `language` (string, Optional): Language code (e.g., 'en', 'hi') or 'auto' for detection (default: auto)
  - `output_format` (string, Optional): Output format: 'txt', 'srt', 'vtt', 'json' (default: txt)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `visual_click`
- **Implementation File**: `tools/live_os_tools.py`
- **Function**: `tool_visual_click`
- **Category**: **Process & OS Execution**
- **Description**: Use AI vision to locate a specific UI element by description on the screen and click it.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `description` (string, Required): Visual description of element (e.g., 'blue submit button', 'Chrome browser icon', 'search bar').
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `visual_drag`
- **Implementation File**: `tools/live_os_tools.py`
- **Function**: `tool_visual_drag`
- **Category**: **General & Skill Execution**
- **Description**: Click and drag from a source UI element to a target UI element identified by visual description.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `from_description` (string, Required): Visual description of source element.
  - `to_description` (string, Required): Visual description of target destination.
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `visual_type`
- **Implementation File**: `tools/live_os_tools.py`
- **Function**: `tool_visual_type`
- **Category**: **General & Skill Execution**
- **Description**: Use AI vision to locate an input field by description and type text into it.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `description` (string, Required): Visual description of input box or field.
  - `text` (string, Required): Text to type into the field.
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `wait_for_element`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_wait_for_element`
- **Category**: **General & Skill Execution**
- **Description**: Wait until a UI element appears on screen.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `description` (string, Required): 
  - `timeout` (integer, Optional): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `weather_report`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_weather_report`
- **Category**: **Security & Network Recon**
- **Description**: Get real-time weather information for a city.
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `city` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `web_extractor`
- **Implementation File**: `tools/web_extractor.py`
- **Function**: `web_extractor_action`
- **Category**: **Web & Browser Automation**
- **Description**: Extract clean text content, headers, and main article text from any web URL. Args: 'url' (webpage URL).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `url` (string, Required): Target webpage URL to fetch and extract
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `web_search`
- **Implementation File**: `tools/web_tools.py`
- **Function**: `tool_web_search`
- **Category**: **Web & Browser Automation**
- **Description**: Search the web using DuckDuckGo. Returns a list of results with titles, URLs, and snippets.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: Yes
- **Parallel Safe**: Yes
- **Input Parameters (2)**:
  - `query` (string, Required): The search query
  - `max_results` (integer, Optional): Max results to return (default 5)
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `whois_lookup`
- **Implementation File**: `tools/redteam_tools.py`
- **Function**: `tool_whois_lookup`
- **Category**: **Security & Network Recon**
- **Description**: Perform a WHOIS lookup on a domain (scope-checked).
- **Risk Level**: **HIGH_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `domain` (string, Required): Target domain
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `window_manager`
- **Implementation File**: `tools/registry.py`
- **Function**: `_lazy_register_tool.<locals>._lazy_wrapper`
- **Category**: **Vision & Desktop Operator**
- **Description**: Inspect visible desktop window titles and focus/switch applications. Args: 'action' ('list' or 'focus'), 'title' (optional application window title).
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `action` (string, Required): 
  - `title` (string, Optional): Title or partial title of window to focus
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `window_maximize`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_window_maximize`
- **Category**: **Vision & Desktop Operator**
- **Description**: Maximize a window by title or process name.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `title` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `window_minimize`
- **Implementation File**: `tools/pc_tools.py`
- **Function**: `tool_window_minimize`
- **Category**: **Vision & Desktop Operator**
- **Description**: Minimize a window by title or process name.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (1)**:
  - `title` (string, Required): 
- **Current Status**: **FUNCTIONALLY WORKING**

---

### Tool: `youtube_video`
- **Implementation File**: `tools/legacy_actions_tools.py`
- **Function**: `tool_youtube_video`
- **Category**: **General & Skill Execution**
- **Description**: Play or summarize a YouTube video.
- **Risk Level**: **LOW_RISK**
- **Required Permissions**: `TIER_0` / `TIER_1`
- **Timeout**: `30.0s` (Default)
- **Retry Policy**: Bounded Exponential Backoff (Max 2 retries on transient errors)
- **Idempotent**: No (State Mutation)
- **Parallel Safe**: No (Lock Required)
- **Input Parameters (2)**:
  - `action` (string, Required): play, summarize
  - `query` (string, Required): Search query or video URL
- **Current Status**: **FUNCTIONALLY WORKING**

---

