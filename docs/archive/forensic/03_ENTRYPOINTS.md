# 03 — ENTRYPOINT FORENSIC AUDIT

## 1. Inventory of All System Entrypoints
The repository contains 12 distinct entrypoints spanning CLI, GUI, Background Daemons, Web APIs, and Setup Utilities.

| Entrypoint File | Invocation Command | Target Subsystem | Runtime Initialized | Global State Created |
| :--- | :--- | :--- | :--- | :--- |
| `main.py` | `python main.py` | `start.py::main()` | `ApplicationRuntime` | `Container`, `LifecycleManager` |
| `start.py` | `python start.py [mode]` | Multi-mode launcher | Full Desktop/Voice/CLI | UI event loop, Voice thread, EventBus |
| `brjarvis.py` | `python brjarvis.py ask/voice/cli/web/doctor` | Unified CLI router | Dynamic per subcmd | CLI session / Subprocess spawns |
| `server.py` | `python server.py [--port 8000]` | FastAPI API Gateway | Modular FastAPI App | PID file, Server state, SQLite DB |
| `ui_mark.py` | `python ui_mark.py` | PySide6 Desktop GUI | `JarvisUI`, `BRVoiceAssistant` | Qt App, GPU monitor thread, HUD |
| `float_widget.py`| `python float_widget.py` | Cyberpunk Floating HUD| PySide6 Floating Widget| Frameless window, Drag tracker |
| `ui.py` | `from ui import JarvisUI` | Root shim for `ui/app.py` | None (Import Shim) | None |
| `dashboard/server.py`| `python -m dashboard.server` | Standalone Web Dashboard| Python `http.server` / JWT | Static file server, Port 8080 |
| `screen_server/ws_server.py`| `python -m screen_server.ws_server`| WebRTC Screen Server | Asyncio WebSockets | Screen capture loop, WS clients |
| `setup_native.py`| `python setup_native.py` | C++ Extension Build | MSVC / GCC Compiler | `.pyd` / `.so` native binaries |
| `scripts/smoke_startup.py`| `python scripts/smoke_startup.py` | Cold Boot Smoke Tester| Mocked Subsystems | Smoke test report |
| `scripts/test_toughest_tasks.py`| `python scripts/test_toughest_tasks.py`| Comprehensive E2E Test| Live/Mock Runtime | Full task evaluation logs |

---

## 2. Deep Forensic Analysis of Canonical Entrypoints

### A. `start.py` (47,713 bytes, 1,068 lines)
- **Role**: Historically the primary monolithic bootstrapper for BR JARVIS MK38.
- **Arguments Supported**: `--cli`, `--voice`, `--headless`, `--debug`, `--port`, `--model`, `--offline`.
- **Initialization Sequence**:
  1. Configures environment encoding and platform-specific DPI scaling.
  2. Bootstraps `core/config.py` and `security/credentials.py`.
  3. Initializes `guardian/core.py` (loads SHA256 code integrity hashes from `.guardian_hashes.json`).
  4. Starts `events/bus.py` and registers memory consolidation hooks.
  5. Spins up `voice/assistant.py` in a background daemon thread if voice is enabled.
  6. Launches PySide6 `ui/main_window.py` or enters CLI REPL in `core/cli.py`.
- **Critical Flaw**: Contains fallback code that manually re-instantiates deprecated subsystems if modern DI container fails.

### B. `brjarvis.py` (128 lines)
- **Role**: Clean, lightweight developer CLI tool.
- **Subcommands**:
  - `ask "<prompt>"`: Zero-UI instant query to `orchestrator/core.py`.
  - `voice`: Launches `ui_mark.py` voice assistant loop.
  - `cli`: Starts interactive terminal REPL.
  - `web`: Spawns `server.py` in background via subprocess.
  - `floating`: Spawns `float_widget.py`.
  - `status` / `doctor`: Inspects API keys, microphone device, GPU availability, and database connectivity.
- **Disposition**: **KEEP + IMPROVE** (Canonical CLI tool).

### C. `server.py` (125 lines)
- **Role**: Production ASGI server entrypoint mounting `api/` routes.
- **Startup Protection**: Contains automatic Python 3.14 alpha rerouting logic to Python 3.12/3.13 on Windows to prevent C-extension crashes.
- **PID Management**: Writes `.jarvis/server.pid` with cleanup on exit.
- **Disposition**: **KEEP + IMPROVE** (Canonical Web & API Server).

### D. `ui_mark.py` (348 lines)
- **Role**: Voice UI orchestrator uniting `ui/app.py` and `voice/assistant.py`.
- **Disposition**: **KEEP + IMPROVE** (Canonical GUI launcher).
