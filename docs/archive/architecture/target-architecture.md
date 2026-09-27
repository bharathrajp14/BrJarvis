# BR JARVIS — TARGET PRODUCTION ARCHITECTURE SPECIFICATION

## 1. Single Responsibility Invariants
1. **Single Application Lifecycle**: `core/bootstrap.py` and `core/runtime.py` exclusively manage process startup, dependency injection, and clean shutdown.
2. **Single Tool Registry**: `tools/registry.py` is the sole authority for all 185 capability schemas and handler callables.
3. **Single Model Gateway**: `gateway/model_gateway.py` standardizes all LLM completions into `ModelResponse` envelopes with circuit-breaker protection.
4. **Single Execution Engine**: `tools/tool_runtime.py` handles timeouts, argument normalization, and error classification.
5. **Mandatory Post-Condition Verification**: `agent/verifier.py` validates physical state before any task status is marked `COMPLETED`.
6. **Isolated Sandbox Artifacts**: User-facing artifacts are exported via `agent/artifacts.py` (`sandbox_path != host_path`) before host browser consumption.
