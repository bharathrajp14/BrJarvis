# 🧹 BR JARVIS — Technical Debt & Refactoring Audit

> **Document Status**: Production Architecture Specification  
> **Scope**: Codebase Debt Audits, Refactoring Targets & Maintenance Roadmap  
> **Version**: MK38.2.5 / v37.5.0  

---

## 1. Executive Debt Audit Overview

The BR JARVIS MK38 codebase (~185 Python files, 30+ packages) achieves a **100% test pass rate** across all 120 Pytest verification tests (`pytest tests/`). Full project analysis reveals key technical debt targets that are actively being refactored and optimized.

---

## 2. Identified Technical Debt & Refactoring Targets

### 1. `ui.py` Monolith File Breakdown (72KB / 2000+ Lines)
- **Issue**: The entire Tkinter desktop interface — HUD animations, chat log, settings panels, face canvas rendering, waveform visualizer, and Multi-Task dashboard — resides in a single 72KB file.
- **Refactoring Strategy**: Modularize `ui.py` into dedicated sub-packages under `ui/`:
  - `ui/tabs/chat_tab.py`: Chat stream & message rendering.
  - `ui/tabs/tasks_tab.py`: Glossy Multi-Task cards & progress bars.
  - `ui/tabs/settings_tab.py`: API keys & system settings dialogs.
  - `ui/widgets/canvas_hud.py`: Face canvas & waveform HUD visualizers.

### 2. Runtime Singleton Factory (`core/bootstrap.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Implemented double-checked locking mechanism (`threading.Lock`) in `build_assistant_runtime()`. Voice GUI, CLI, and Web Server now share a unified runtime instance, eliminating split working memory and duplicate backend connection pools.

### 3. Permission System Enforcement (`permissions.py`, `tools/registry.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Added `CONFIRM_DESTRUCTIVE` mode to `PermissionMode` enum and wired pre-execution permission traps into `execute_tool()`.

### 4. Web Server CORS & Request Thread Serialization (`server.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Bound server host to `127.0.0.1` by default, restricted CORS to explicit localhost whitelist, and added `_CHAT_LOCK` thread serialization to API endpoints.

### 5. Stream Safety Guards & Duplicate Tool Call Shield (`orchestrator/core.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Integrated `StepPlanner` budgeting, 4-call duplicate tool call detection/interception, and 4KB output truncation in streaming mode.

### 6. Input Sanitization & URL Scheme Protection (`core/intent_engine.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Replaced shell execution `os.system()` with `subprocess.Popen()` and enforced URL scheme whitelisting (blocking `javascript:`, `file:`, `data:`, `vbscript:` schemes).

### 7. Centralized API Key Loading (`config/__init__.py`) [RESOLVED]
- **Status**: ✅ **RESOLVED in v38.2.5**
- **Fix**: Centralized Gemini API key loading into `config.get_gemini_api_key()` across backends, vector store, and live OS control.

