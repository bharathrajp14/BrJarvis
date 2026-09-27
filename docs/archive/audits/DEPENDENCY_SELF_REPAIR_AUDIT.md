# DEPENDENCY SELF-REPAIR AUDIT — BR JARVIS MK40.2

## 1. Automated Import-to-Package Mapping

In Python, module import names often differ from their PyPI package distribution names:
- `import docx` $\rightarrow$ `pip install python-docx`
- `import fitz` $\rightarrow$ `pip install pymupdf`
- `import PIL` $\rightarrow$ `pip install pillow`
- `import yaml` $\rightarrow$ `pip install pyyaml`
- `import bs4` $\rightarrow$ `pip install beautifulsoup4`
- `import sklearn` $\rightarrow$ `pip install scikit-learn`
- `import cv2` $\rightarrow$ `pip install opencv-python`

`DependencyResolver` maintains bidirectional mapping tables and AST static analysis tools to identify missing modules before script execution begins.

---

## 2. Governed Self-Repair Policies

Automated dependency installation is governed by explicit security policies:
1. **`AUTO_REPAIR_SAFE`**: Safe, non-invasive packages in `SAFE_PACKAGES_ALLOWLIST` are automatically installed into the target `.venv` without user prompts.
2. **`ASK_BEFORE_REPAIR`**: Prompts the user or creates an `ApprovalRequest` before running `pip install` for non-standard packages.
3. **`NO_AUTO_REPAIR`**: Strict fail-closed mode for production environments.
