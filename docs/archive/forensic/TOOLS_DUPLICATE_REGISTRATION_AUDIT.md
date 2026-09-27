# BR JARVIS — TOOLS DUPLICATE REGISTRATION AUDIT

## 1. Audit Summary
- **Registration Architecture**: Single source of truth in `tools/registry.py` with `@register_tool` decorator.
- **Root Cause of Log Warning**: `tools/registry.py` defined redundant `_lazy_register_tool` calls on initial module import for tools that were already implemented as first-class native tools in `tools/*.py`.
- **Resolution Applied**:
  1. Removed redundant `_lazy_register_tool` calls in `tools/registry.py` for all 5 natively implemented tools (`system_optimizer`, `web_extractor`, `system_health`, `window_manager`, `file_search_semantic`).
  2. Enhanced `register_tool` in `tools/registry.py` to seamlessly upgrade lazy wrappers to native handlers at `DEBUG` level and avoid schema duplications.

---

## 2. Duplicate Registration Audit Ledger

| Tool Name | Registration Mechanism 1 | Registration Mechanism 2 | Primary Caller | Canonical Source File | Duplicate Status | Fix Applied |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `system_optimizer` | `_lazy_register_tool` in `tools/registry.py` | `@register_tool` in `tools/system_tools.py` | Intent Engine / Tool Runtime | `tools/system_tools.py` | **ELIMINATED** | Removed lazy stub in `registry.py`; canonical decorator in `system_tools.py` retained. |
| `web_extractor` | `_lazy_register_tool` in `tools/registry.py` | `@register_tool` in `tools/web_extractor.py` | Research Workflows | `tools/web_extractor.py` | **ELIMINATED** | Removed lazy stub in `registry.py`; canonical decorator in `web_extractor.py` retained. |
| `system_health` | `_lazy_register_tool` in `tools/registry.py` | `@register_tool` in `tools/system_health.py` | Diagnostic Workflows | `tools/system_health.py` | **ELIMINATED** | Removed lazy stub in `registry.py`; canonical decorator in `system_health.py` retained. |
| `window_manager` | `_lazy_register_tool` in `tools/registry.py` | `@register_tool` in `tools/window_manager.py` | Desktop UI Automation | `tools/window_manager.py` | **ELIMINATED** | Removed lazy stub in `registry.py`; canonical decorator in `window_manager.py` retained. |
| `file_search_semantic` | `_lazy_register_tool` in `tools/registry.py` | `@register_tool` in `tools/file_search_semantic.py`| File Search Workflows | `tools/file_search_semantic.py`| **ELIMINATED**| Removed lazy stub in `registry.py`; canonical decorator in `file_search_semantic.py` retained. |
