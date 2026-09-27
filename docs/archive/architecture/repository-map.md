# BR JARVIS — MASTER REPOSITORY & SUBSYSTEM MAP

## 1. Executive Subsystem Topology
BR JARVIS is organized into cohesive, single-responsibility layers:

```text
                                  ┌─────────────────────────────┐
                                  │      Desktop HUD & Web UI    │
                                  └──────────────┬──────────────┘
                                                 │ (HTTP / WebSocket / Events)
                                  ┌──────────────▼──────────────┐
                                  │  API Server (/api/v1/...)   │
                                  └──────────────┬──────────────┘
                                                 │
                                  ┌──────────────▼──────────────┐
                                  │ ApplicationRuntime / Core DI │
                                  └──────────────┬──────────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            │                                    │                                    │
┌───────────▼───────────┐            ┌───────────▼───────────┐            ┌───────────▼───────────┐
│     Voice Engine      │            │  Cognitive & Planner  │            │     Vision Engine     │
│ (Silero VAD / Whisper)│            │ (SmartRouter/Gateway) │            │  (DXGI Capture / OCR) │
└───────────┬───────────┘            └───────────┬───────────┘            └───────────┬───────────┘
            │                                    │                                    │
            └────────────────────────────────────┼────────────────────────────────────┘
                                                 │
                                  ┌──────────────▼──────────────┐
                                  │   6-Tuple Policy & Paths    │
                                  └──────────────┬──────────────┘
                                                 │
                                  ┌──────────────▼──────────────┐
                                  │    Universal Tool Runtime   │
                                  └──────────────┬──────────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            │                                    │                                    │
┌───────────▼───────────┐            ┌───────────▼───────────┐            ┌───────────▼───────────┐
│   Host OS & Desktop   │            │   Artifacts Sandbox   │            │   Browser Automation  │
│ (Win32 / SendInput)   │            │ (SHA-256 Host Export) │            │ (Playwright / CDP)    │
└───────────────────────┘            └───────────────────────┘            └───────────────────────┘
```

---

## 2. Directory & Domain Breakdown

| Directory Path | Architectural Responsibility | Canonical Entrypoint | Key Contracts / Classes |
| :--- | :--- | :--- | :--- |
| `core/` | Application lifecycle, DI container, bootstrap, errors. | `core/runtime.py` | `ApplicationRuntime`, `CoreBootstrapper`, `JarvisError` |
| `gateway/` | OpenAI-compatible LLM gateway, key rotation, circuit breaker. | `gateway/model_gateway.py` | `ModelGatewayClient`, `ModelResponse` |
| `router/` | Multi-provider intelligent routing, fallback chains, latency tiers. | `router/core.py`, `router/smart_router.py` | `SmartRouter`, `TaskProfile`, `ModelDecision` |
| `agent/` | Task state machine, DAG decomposition, artifact lifecycle, verifier. | `agent/task_state.py`, `agent/verifier.py` | `TaskState`, `ActionVerifier`, `ArtifactManager` |
| `tools/` | Universal tool registry and execution runtime engine. | `tools/registry.py`, `tools/tool_runtime.py` | `ToolRuntimeEngine`, `ToolResult`, `ArgumentNormalizer` |
| `security/` | 6-Tuple deterministic policy engine and path confinement. | `security/policy_engine.py` | `SecurityPolicyEngine`, `PathSecurityPolicy` |
| `memory/` | Unified SQLite WAL database, vector embeddings, thread-safe locking.| `memory/canonical_db.py`, `memory/sqlite_lock.py`| `CanonicalDatabaseManager`, `AsyncSqliteLock` |
| `voice/` | Hands-free duplex voice pipeline with instant barge-in interrupt. | `voice/assistant.py` | `VoiceAssistant`, `SileroVAD`, `TTSQueue` |
| `vision/` | DXGI GPU screen capture, OCR, accessibility, perception router. | `vision/engine.py` | `VisionEngine`, `PerceptionRouter` |
| `computer/` | Win32 desktop automation, mouse/keyboard operator, DPI scaling. | `computer/operator.py` | `ComputerOperator`, `ActionResult` |
| `api/` | FastAPI application layer, `/api/v1/` routes, WebSockets, health. | `api/server.py` | `FastAPI`, `WebSocketManager` |
| `ui/` | Cyberpunk HUD, system tray, desktop overlays. | `ui/main_window.py` | `JARVISMainWindow`, Qt Signal Bridge |
