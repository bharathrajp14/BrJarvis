# BR JARVIS — TOOL CONTRACT AUDIT & SCHEMA MATRIX

## 1. Schema vs Implementation Contract Audit
Compares the JSON schema presented to LLMs against actual Python parameter acceptance and return value structures.

| Tool Name | Declared Input Schema | Actual Python Signature | Declared Output | Actual Return Structure | Mismatch / Gap | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `schedule_reminder` | `message: str, delay_seconds: int` | `args: dict` | `str (confirmation)` | `str` | None (Matches) | NONE |
| `manage_reminders` | `action: str, reminder_id?: str` | `args: dict` | `str / JSON` | `str / JSON` | None (Matches) | NONE |
| `system_cleanup` | `target: str` | `args: dict` | `str` | `str (freed MB)` | None (Matches) | NONE |
| `system_optimizer` | `level: str` | `args: dict` | `str` | `str (optimizations)` | None (Matches) | NONE |
| `pdf_tool` | `action: str, file_path: str` | `args: dict` | `str / JSON` | `str` | None (Matches) | NONE |
| `run_sandboxed_process` | `command: str, timeout: int` | `args: dict` | `JSON (stdout, stderr)` | `JSON string` | None (Matches) | NONE |
| `web_extractor` | `url: str, selector?: str` | `args: dict` | `str (content)` | `str` | None (Matches) | NONE |
| `semantic_file_search` | `query: str, path?: str` | `args: dict` | `JSON (matches)` | `str (formatted list)` | Structured -> String conversion | LOW |
