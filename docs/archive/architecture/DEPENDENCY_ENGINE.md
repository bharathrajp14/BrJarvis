# DEPENDENCY ENGINE — BR JARVIS MK40.2

## 1. Universal Dependency Engine Design

The **Universal Dependency Engine** (`core/execution/dependency_resolver.py`) replaces implicit or naive package assumptions with deterministic import intelligence.

### Key Capabilities:
1. **Dynamic AST Code Parsing**: Extracts all top-level `import` and `from ... import` symbols from Python code snippets, filtering out standard library modules (`os`, `sys`, `json`, `pathlib`, etc.).
2. **Machine-Readable Import-to-Distribution Mapping**: Resolves disparities between Python module names and PyPI package distribution names:
   - `fitz` → `PyMuPDF`
   - `docx` → `python-docx`
   - `cv2` → `opencv-python`
   - `PIL` → `pillow`
   - `sklearn` → `scikit-learn`
   - `yaml` → `PyYAML`
   - `bs4` → `beautifulsoup4`
   - `dotenv` → `python-dotenv`
   - `pypdf` → `pypdf`
   - `openpyxl` → `openpyxl`
   - `playwright` → `playwright`
   - `fpdf` → `fpdf2`
   - `pptx` → `python-pptx`
3. **Dynamic Introspection**: Leverages `importlib.metadata.packages_distributions()` to discover custom or local site-packages distributions.
4. **Target Environment Verification**: Verifies module importability directly against the target virtual environment (`resolved_python -c "import <mod>"`), preventing host-vs-sandbox skew.

---

## 2. Dependency Error Diagnostic Matrix

When execution fails with dependency issues, the engine diagnoses the exact condition:

| Raw Error Signal | Diagnostic Classification | Suggested Action |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'pypdf'` | `MISSING_DEPENDENCY` | Target Python `-m pip install pypdf` |
| `ModuleNotFoundError: No module named 'fitz'` | `MISSING_DEPENDENCY` | Target Python `-m pip install PyMuPDF` |
| `ModuleNotFoundError: No module named 'docx'` | `MISSING_DEPENDENCY` | Target Python `-m pip install python-docx` |
| `ImportError: cannot import name ...` | `DEPENDENCY_VERSION_MISMATCH` | Reinstall or upgrade package |
| `Executable doesn't exist at .../chromium` | `MISSING_SYSTEM_DEPENDENCY` | Target Python `-m playwright install chromium` |
| `FileNotFoundError: git not found` | `MISSING_SYSTEM_EXECUTABLE` | Report host system prerequisite |

---

## 3. Dependency Preflight Check

Before running any script or executing any multi-stage task, `CapabilityChecker` performs preflight checks:
* Code execution preflight checks all imports extracted via AST.
* If any dependencies are missing in the resolved virtual environment, the system auto-repairs them under `AUTO_REPAIR_SAFE` policy or provides clear instructions before running.
