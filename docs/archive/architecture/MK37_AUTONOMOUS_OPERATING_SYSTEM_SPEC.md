# BR JARVIS MK37 — Autonomous Operating System & Universal Device Control Specification

## 1. Executive Summary

**BR JARVIS MK37** is an autonomous, multimodal, local-first multi-device operating system. It transforms the AI assistant from executing individual tool commands into an intelligent agent that owns entire workflows end-to-end:
`Goal → Planning → Research → Execution → Observe → Verification → Recovery → Completion`.

The system unifies the user's PC, desktop applications, web browser, connected cloud services, and authorized Android mobile devices into a single, cohesive control plane with strict security boundaries, approval checkpoints, and verifiable execution states.

---

## 2. System Architecture & Control Plane

```text
                                  USER GOAL / VOICE / PROMPT
                                               │
                                               ▼
                              INTENT & TASK CLASSIFIER
                        (Simple Command vs. Multi-Step vs. Autonomous)
                                               │
                                               ▼
                              CROSS-DEVICE TASK PLANNER
                             (agent/cross_device_planner.py)
                                               │
                                               ▼
                            PERSISTENT TASK STATE MACHINE (SQLite WAL)
                              (agent/task_state.py & task_dag.py)
                                               │
                                               ▼
                                 UNIVERSAL CAPABILITY ROUTER
                               (connectors/capabilities.py)
                                               │
                 ┌─────────────────────────────┼─────────────────────────────┐
                 ▼                             ▼                             ▼
        PC / DESKTOP CONTROLLER     STRAWBERRY BROWSER AGENT       ANDROID MOBILE GATEWAY
        (computer/operator.py)      (tools/browser_agent_v2.py)     (mobile/device_controller.py)
                 │                             │                             │
                 ▼                             ▼                             ▼
         PyAutoGUI / Live OS          Playwright / DOM / Tree       Accessibility / Projection
                 │                             │                             │
                 └─────────────────────────────┼─────────────────────────────┘
                                               │
                                               ▼
                                  POST-ACTION STEP VERIFIER
                                               │
                                 ┌─────────────┴─────────────┐
                           [Success]                     [Failure]
                                 │                           │
                                 ▼                           ▼
                           STATE CHECKPOINT           RECOVERY ENGINE
                                 │                 (Retry / Replan / Pause)
                                 ▼
                         TASK REPORT & COMPLETION
```

---

## 3. Subsystem Specifications

### 3.1 Autonomous Agent 2.0 (`agent/`)
- **Task Lifecycle**: Every task possesses a persistent `TaskState` record stored in `workspace/tasks/agent_tasks.db` with states `PENDING`, `RUNNING`, `PAUSED`, `WAITING_APPROVAL`, `COMPLETED`, `FAILED`, `CANCELLED`.
- **State Checkpointing**: Checkpoints are created after every single executed action step to permit zero-data-loss rollback, resumption, and task replay.
- **Recovery Engine**: Standardized failure classification (`AUTH_REQUIRED`, `PERMISSION_DENIED`, `ELEMENT_NOT_FOUND`, `DEVICE_OFFLINE`, `NETWORK_FAILURE`, `APP_NOT_INSTALLED`, `APP_CRASHED`, `TASK_TIMEOUT`, `USER_APPROVAL_REQUIRED`, `CAPTCHA_REQUIRED`, `UNSUPPORTED_ACTION`, `UNKNOWN_FAILURE`).
- **Loop & Stuck Guard**: Detects consecutive duplicate tool signatures and halts unbounded ReAct loops with exponential backoff.

### 3.2 Strawberry-Class Browser Agent (`tools/browser_agent_v2.py`)
- **Hybrid Observation**: Extracts clean semantic DOM summaries, accessibility role trees, and interactive element maps (assigning stable numeric IDs instead of fragile pixel coordinates).
- **Structured Actions**: `click`, `type`, `navigate`, `scroll`, `select`, `upload`, `extract`, `handle_dialog`.
- **Bot/CAPTCHA Policy**: Automatically detects Cloudflare / reCAPTCHA / hCaptcha challenges and pauses with `WAITING_FOR_USER_AUTHENTICATION` instead of attempting security bypass.

### 3.3 Learnable Skills System (`skills/skill_engine.py`)
- **Declarative Workflows**: Saved as versioned JSON schemas in `workspace/skills/` with typed inputs, sequential steps, parameter interpolation (`{input_var}`), and post-execution verification criteria.
- **Trajectory Learning**: Automatically analyzes successful execution traces and prompts the user to save them as permanent reusable skills.

### 3.4 Persistent Background Routine Engine (`actions/routine_engine.py`)
- **9 Trigger Types**: Time / Cron schedule, application events, incoming emails, calendar conflicts, Slack messages, filesystem changes, webhooks, device events, and direct user requests.
- **Background Daemon**: Continuously evaluates scheduled routines and triggers execution safely in the background across restarts.

### 3.5 Universal Capability Registry (`connectors/capabilities.py`)
- Standardizes all application integrations under the `ApplicationCapability` model:
  - **Communication**: Gmail, Outlook, Slack, WhatsApp, Teams, Discord.
  - **Productivity**: Google Calendar, Notion, Google Drive, Microsoft 365, Docs, Sheets.
  - **Engineering**: GitHub, GitLab, Jira, Linear, CI/CD.
  - **Research**: Strawberry Browser, Search, YouTube, RSS.
  - **Local**: Filesystem, Terminal, Desktop Apps, Diagnostics.
  - **MCP**: Model Context Protocol servers.

### 3.6 Mobile Master Control Subsystem (`mobile/`)
- **Transport**: Mutual TLS / Secure WebSocket (`/mobile/ws`) with SHA256 auth tokens and PIN pairing.
- **Accessibility Service**: Real-time view hierarchy traversal and semantic element interaction.
- **Screen Understanding**: Combines accessibility node bounds, text, content descriptions, and OCR.
- **Strict Lock-State Rules**: If the phone is locked, JARVIS halts automation and transitions to `WAITING_FOR_USER_AUTHENTICATION`. It never fakes unlocking or bypasses OEM security.
- **Mock Android Environment**: `mobile/mock_android.py` provides 100% testable Android emulation for automated CI/CD verification.

### 3.7 Security, Permissions & Audit Engine (`permissions.py`, `security/`, `history/`)
- **Permission Modes**: `ALLOW_ALL`, `CONFIRM_DESTRUCTIVE`, `CONFIRM_ALL`, `DENY_ALL`.
- **Action Decisions**: `ALLOW`, `DENY`, `CONFIRM`, `ALLOW_FOR_SESSION`, `ALLOW_FOR_DEVICE`, `ALLOW_FOR_APPLICATION`.
- **Credential Vault**: Stores API keys and device secrets by opaque reference IDs (`credential_ref`) to prevent exposing raw credentials to LLM prompt contexts.
- **Structured Audit Engine**: Records every high-risk action in `workspace/audit/audit_events.db` with task ID, device ID, risk level, and user approval outcome.

---

## 4. Setup & Pairing Instructions

### 4.1 Pairing an Android Phone
1. Launch JARVIS Server (`python server.py`).
2. Request a pairing token:
   ```bash
   POST http://localhost:8000/api/agent/devices/pair-token
   ```
3. Open the **JARVIS Companion App** on Android.
4. Enter the 6-digit PIN or scan the QR code.
5. The device connects over `/mobile/ws` and registers as `TRUSTED`.

### 4.2 Running Cross-Device Tasks
Example voice or text command:
> *"Find my resume on my PC and send it to Rahul on WhatsApp."*
1. JARVIS locates `resume.pdf` on the PC filesystem.
2. Formats document attachment for the paired Android phone.
3. Opens WhatsApp and prepares the message.
4. **Approval Gate Triggers**: Displays an approval prompt with file and contact details.
5. Upon user approval, sends message and records structured audit event.
