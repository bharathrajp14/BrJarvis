# BR JARVIS — OPERATIONAL TROUBLESHOOTING GUIDE

## 1. Common Operational Scenarios & Diagnostic Solutions

| Symptom / Error | Root Cause | Immediate Diagnostic & Fix |
| :--- | :--- | :--- |
| `ERR_FILE_NOT_FOUND` in Browser | Browser attempted to open unexported virtual sandbox path. | Run `tools.export_tools.tool_artifact_export()` or use `agent.artifacts.ensure_host_artifact()`. |
| `All backends failed` | Cloud provider quota reached (HTTP 429) or API key invalid. | Verify `.env` keys; check local proxy server (`http://localhost:8045/v1`); enable fallback provider. |
| `sqlite3.OperationalError: database is locked` | Concurrent threads writing without mutex. | Use `memory.sqlite_lock.get_sqlite_lock()` to serialize database writes in WAL mode. |
| Mouse clicks landing off-target | Non-100% display scaling on Windows monitor. | Ensure `computer.operator.ComputerOperator` applies DPI scaling factor via `GetDpiForWindow`. |
| Mic VAD triggers while assistant speaks | Speaker audio looping into microphone. | Ensure software acoustic echo suppression is active in `voice.assistant.VoiceAssistant`. |
