# 08 — TOOLS & ACTIONS SUBSYSTEM FORENSIC RECORD

## 1. Overview & Forensic Separation
The codebase contains **121 tool and action modules** split across `tools/` (63 files) and `actions/` (58 files).
- `tools/`: Declarative, schema-driven tools designed for AI model tool-calling.
- `actions/`: Legacy procedural automation scripts containing direct GUI, OS, and scraping routines.

---

## 2. Major Tool Subsystems & Capabilities

### A. Advanced Document & PDF Processing (`tools/pdf_tools.py`, 1,257 lines)
- Implements complete PDF inspection, OCR text extraction, table parsing (via `pdfplumber` / `pypdf`), form filling, PDF merging, splitting, and metadata redaction.
- **Disposition**: **KEEP**.

### B. Live OS & Desktop Control (`tools/live_os_tools.py`, `actions/desktop.py`, `actions/computer_control.py`)
- Screen capture with grid overlays for spatial coordinate prompting.
- PyAutoGUI and Win32 API mouse clicking, drag-and-drop, keystroke injection.
- Window management (`tools/window_manager.py`): Focus, minimize, maximize, move windows via `win32gui`.
- **Security Check**: Enforces safety bounding box and confirmation on destructive hotkeys (`Alt+F4`, `Ctrl+W`).
- **Disposition**: **CONSOLIDATE** into `computer/operator.py` and `tools/live_os_tools.py`.

### C. Web & Browser Automation (`actions/browser_control.py`, 1,079 lines; `tools/web_tools.py`)
- Dual-mode browser automation:
  - Mode 1: Playwright / Selenium headless browser automation.
  - Mode 2: Chrome DevTools Protocol (CDP) connecting to user's active Chrome browser session on port 9222.
- **Disposition**: **CONSOLIDATE** into `tools/browser_tools.py`.

### D. Messaging & Social Automation (`actions/telegram_automation.py`, `actions/whatsapp_automation.py`, `actions/smart_email_sender.py`)
- Automated scheduling, draft creation, and contact lookup.
- Uses encrypted contact database in `memory/contact_manager.py`.
- **Disposition**: **REFACTOR** into `connectors/`.

---

## 3. Duplicate Tool Cleanup Matrix
| Duplicate Group | File A | File B | File C | Unified Target |
| :--- | :--- | :--- | :--- | :--- |
| **Reminders** | `actions/reminder.py` | `actions/reminders.py` | `tools/reminder_tools.py` | `tools/reminder_tools.py` |
| **Web Search** | `actions/web_search.py`| `tools/web_tools.py` | `connectors/web_search.py` | `connectors/web_search.py` |
| **Email** | `actions/email_assistant.py` | `actions/smart_email_sender.py` | `tools/smart_email_tools.py` | `connectors/email.py` |
| **System Clean**| `actions/system_cleanup.py` | `actions/system_optimizer.py` | `tools/system_tools.py` | `tools/system_tools.py` |
| **Browser** | `actions/browser_control.py` | `tools/browser_tools.py` | `actions/web_app_controller.py` | `tools/browser_tools.py` |
