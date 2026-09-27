# BR JARVIS — FINAL CANONICAL TOOLS ARCHITECTURE

## 1. Single Responsibility Invariants
1. **Single Tool Registry**: `tools/registry.py` is the authoritative source for all 81 tool schemas and callable handlers.
2. **Single Tool Runtime Engine**: `tools/tool_runtime.py` handles execution timeouts, thread pools, async event loops, and exception normalization.
3. **Mandatory 6-Tuple Policy**: Every tool execution must receive authorization from `security/policy_engine.py` before execution.
4. **Mandatory Physical Verification**: Every state-mutating tool must pass post-condition verification in `agent/verifier.py` before `success=True` is reported to the cognitive model.
