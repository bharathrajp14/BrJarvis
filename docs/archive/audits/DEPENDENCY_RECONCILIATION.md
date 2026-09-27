# DEPENDENCY RECONCILIATION AUDIT REPORT

**Audit Objective:** Cross-reconcile `pyproject.toml`, `requirements.txt`, setup scripts, and actual imports across the repository.

## 1. Discrepancy Matrix

| Package | In `pyproject.toml` | In `requirements.txt` | Imported in Code | Required Runtime Extra | Action Taken |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `python-pptx` | ❌ Missing | ✅ `>=1.0.0` | `actions/file_processor.py` | `documents` | Added to `pyproject.toml[documents]` |
| `onnxruntime` | ❌ Missing | ✅ `>=1.17.0` | `voice/stt.py`, `voice/stt_engine.py` | `voice` | Added to `pyproject.toml[voice]` |
| `selenium` | ❌ Missing | ✅ `>=4.20.0` | `actions/browser_control.py` | `web` | Added to `pyproject.toml[web]` |
| `ddgs` | ❌ Missing | ✅ `>=6.0.0` | `connectors/web_search.py` | `web` | Added to `pyproject.toml[web]` |
| `keyboard` | ❌ Missing | ✅ `>=0.13.5` | `actions/hotkeys.py` | `windows` | Added to `pyproject.toml[windows]` |
| `mss` | ❌ Missing | ✅ `>=10.0.0` | `actions/screen_share.py` | `windows`, `automation` | Added to `pyproject.toml[automation]` |
| `google-genai` | ✅ Core | ✅ `>=1.0.0` | `backends/gemini.py` | Core | Synchronized |
| `PySide6` | ✅ `automation` | ✅ `>=6.6.0` | `desktop_ui/*`, `float_widget.py` | `automation` | Synchronized |
| `chromadb` | ✅ `memory` | ✅ `>=0.5.0` | `memory/vector_memory.py` | `memory` | Synchronized |
| `python-docx` | ✅ `documents`| ✅ `>=1.1.0` | `tools/doc_tools.py` | `documents` | Synchronized |
| `openpyxl` | ✅ `documents`| ✅ `>=3.1.0` | `tools/excel_tools.py` | `documents` | Synchronized |
| `fpdf2` | ✅ `documents`| ✅ `>=2.7.0` | `tools/pdf_tools.py` | `documents` | Synchronized |

## 2. Canonical Dependency Policy
- `pyproject.toml` is the single source of truth for package definitions and extras.
- `requirements.txt` mirrors `pyproject.toml` for simple `pip install -r requirements.txt` environments.
- All extras are bundled in `brjarvis[all]`.