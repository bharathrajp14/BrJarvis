# 12 — BROWSER AUTOMATION & ARTIFACTS FORENSIC RECORD

## 1. Overview & Dual-Mode Architecture
BR JARVIS supports both automated headless browser execution and live session control:
1. **Isolated Headless Automation** (`tools/browser_tools.py`): Playwright-based sandbox browser profile for automated search, form filling, and scraping.
2. **Interactive Live Browser Attach** (`actions/browser_control.py`, 1,079 lines): Attaches to user's running Chrome/Edge browser via Chrome DevTools Protocol (CDP port 9222).

---

## 2. Forensic Findings & Artifact Management

### A. Artifact Export & Cognitive Workspace (`agent/artifacts.py`, 613 lines)
- Manages output artifacts (reports, generated charts, code repos, exported documents).
- Confines AI file modifications to `workspace/` and `BR_WORKSPACE/AI_Output/`.
- Computes SHA256 integrity hashes for all exported artifacts.
- Automatically generates user-facing markdown previews.
- **Disposition**: **KEEP + IMPROVE**.

### B. Browser Profile Isolation Risk (`workspace/browser_user_data/`, 540+ files)
- Discovered that Chromium browser cache, cookies, local storage, and first-party sets were being stored directly in the `workspace/browser_user_data` git-tracked folder.
- *Finding*: Browser profile files are runtime cache files and must be excluded via `.gitignore` to prevent repository bloat and potential cookie leakage.
- **Disposition**: **ADD TO .gitignore & CLEANUP**.
