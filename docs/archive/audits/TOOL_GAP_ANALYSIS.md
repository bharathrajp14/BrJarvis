# BR JARVIS — Tool Gap Analysis & Capability Matrix

## 1. Tool Category & Health Status Matrix

| Tool Category | Primary Tool | Fallback Tool(s) | Health State | Permission Level | Idempotent | Parallel Safe |
|:---|:---|:---|:---|:---|:---|:---|
| **Web Research** | `web_search` | `fetch_page`, `browser_control` | `READY` | Read-Only | Yes | Yes |
| **Repo Analysis** | `file_read` | `git_repo_mgr`, `code_helper` | `READY` | Read-Only | Yes | Yes |
| **Office Documents** | `document_creator` | `create_word_document`, `create_pdf_document` | `READY` | Write (Workspace) | Yes | No (Exclusive) |
| **Browser Control** | `browser_control` | `open_app`, `browser_open_url` | `READY` | OS Mutation | No | No (Exclusive) |
| **System Diagnostics** | `system_diagnostic` | `system_monitor`, `computer_settings` | `READY` | Read-Only | Yes | Yes |
| **Code Execution** | `code_helper` | `dev_agent`, `scratchpad_eval` | `READY` | Sandboxed Write | No | Exclusive |
| **Communication** | `send_message` | `smart_email_sender`, `email_assistant` | `READY` | High Risk / Confirm | No | No (Exclusive) |
| **Memory Operations** | `memory_save` | `memory_tools`, `persistent_store` | `READY` | Database Write | Yes | Yes (WAL) |

---

## 2. Identified Orchestration Gaps & Solutions

### Gap 1: Tool Health Awareness
- **Prior Problem**: The agent would repeatedly attempt calling tools that were missing API keys or unconfigured dependencies.
- **Solution**: `ToolHealthManager` maintains live health states (`READY`, `DEGRADED`, `DISABLED`, `BLOCKED`, `UNAVAILABLE`) and automatically routes around broken tools.

### Gap 2: Heterogeneous Output Formats
- **Prior Problem**: Tools returned unstandardized strings, JSON dicts, tuples, or stderr dumps.
- **Solution**: Standardized `ToolResult` and `StepResultStore` serialize outputs into canonical dictionaries with explicit `data`, `evidence`, and `status` fields.

### Gap 3: Multi-Parameter Input Dependency
- **Prior Problem**: Complex downstream tools requiring multiple upstream arguments (e.g. DOCX creator requiring text from Web Search + local AST from Repo Scan + system hardware metrics) lacked an aggregation layer.
- **Solution**: `ToolInputMapper` aggregates multiple independent upstream step outputs dynamically at wave dispatch.

### Gap 4: Resource Collisions in Parallel Execution
- **Prior Problem**: Two tools concurrently writing to the same document or workspace folder caused file locking errors on Windows.
- **Solution**: Reader-Writer lock mechanisms in `ExecutionGraph` ensure exclusive execution for mutating steps sharing `resource_keys`.
