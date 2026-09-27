# 05 — CORE SUBSYSTEM FORENSIC RECORD

## 1. Overview & Architectural Role
The `core/` subsystem provides the foundational runtime primitives: dependency injection container, lifecycle state machine, structured logging, configuration schemas, cross-platform process supervision, and deterministic heuristic intent routing.

---

## 2. File-by-File Forensic Audit

### `core/bootstrap.py` (93 lines)
- **Role**: Modern runtime bootstrapper.
- **Classes**: `AssistantRuntime`
- **Functions**: `build_assistant_runtime()`, `reset_assistant_runtime()`
- **Responsibilities**: Instantiates `Container`, registers singleton services (`Orchestrator`, `SmartRouter`, `UnifiedMemory`), starts lifecycle.
- **Disposition**: **KEEP + IMPROVE** (Canonical initialization path).

### `core/bootstrapper.py` (94 lines)
- **Role**: Duplicate legacy bootstrapper.
- **Classes**: `CoreBootstrapper`
- **Flaw**: Duplicate implementation of `bootstrap.py` with slight differences in error handling.
- **Disposition**: **CONSOLIDATE** into `core/bootstrap.py`.

### `core/runtime.py` (192 lines)
- **Role**: Application runtime manager.
- **Classes**: `ApplicationRuntime`
- **State Owned**: Runtime state enum (`STARTING`, `RUNNING`, `PAUSED`, `STOPPING`, `STOPPED`), DI container pointer, background task pool.
- **Disposition**: **KEEP**.

### `core/lifecycle.py` (122 lines)
- **Role**: Lifecycle management, graceful shutdown signals, hook registration.
- **Classes**: `SystemState`, `LifecycleManager`
- **Signals**: Intercepts `SIGINT`, `SIGTERM`, Windows console control events.
- **Disposition**: **KEEP**.

### `core/di.py` (129 lines)
- **Role**: Lightweight, deterministic Dependency Injection container.
- **Classes**: `Container`
- **Features**: Singleton registration, factory registration, thread-safe instance cache.
- **Disposition**: **KEEP**.

### `core/config.py` (135 lines)
- **Role**: Global configuration dataclasses and YAML/JSON/.env parser.
- **Classes**: `AssistantConfig`, `ModelConfig`, `VoiceConfig`, `UIConfig`, `SecurityConfig`.
- **Validation**: Strict environment variable parsing with type casting.
- **Disposition**: **KEEP**.

### `core/intent_engine.py` (1,811 lines)
- **Role**: Deterministic, zero-token fast-path regex and heuristic intent parser.
- **Classes**: `DeterministicIntentEngine`
- **Methods**: 65 intent pattern matchers (media control, app launching, file open, system volume, calculator, timer, weather).
- **Flaws**:
  - 1,811 lines containing huge hardcoded application dictionaries for Windows.
  - Directly imports procedural functions from `actions/`.
- **Disposition**: **REFACTOR** (Extract app registry and rule tables into structured JSON/YAML config).

### `core/logging.py` (155 lines)
- **Role**: Structured JSON & colored console loggers.
- **Classes**: `JSONFormatter`, `ColoredConsoleFormatter`
- **Features**: Automatic secret masking for API keys, UUID session tagging.
- **Disposition**: **KEEP**.

### `core/process.py` (81 lines)
- **Role**: Process supervisor for background tasks.
- **Classes**: `TaskStatus`, `ProcessSupervisor`
- **Disposition**: **KEEP**.

### `core/native_bridge.py` (213 lines)
- **Role**: C++/Rust native accelerator bridge via `ctypes` / C-extension.
- **Functions**: Memory search vector dot-product, audio RMS calculation, Windows window hook.
- **Fallback**: 100% pure Python fallback if native binary not compiled.
- **Disposition**: **KEEP**.

### `core/workspace_engine.py` (178 lines)
- **Role**: Cognitive workspace & directory boundary manager.
- **Classes**: `CognitiveWorkspaceEngine`
- **Sandboxing**: Confines AI file modifications to `workspace/` and `BR_WORKSPACE/`.
- **Disposition**: **KEEP**.

### `core/errors.py` (119 lines) & `core/error_middleware.py` (53 lines)
- **Role**: Strongly-typed exception taxonomy (`JarvisError`, `SecurityViolationError`, `ModelTimeoutError`, `ToolExecutionError`).
- **Disposition**: **KEEP**.

### `core/sanitizer.py` (4 lines)
- **Role**: Obsolete 4-line stub.
- **Disposition**: **DELETE** (Merged into `security/sanitizer.py`).
