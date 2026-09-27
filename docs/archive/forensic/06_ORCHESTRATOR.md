# 06 — ORCHESTRATOR & COGNITIVE LOOP FORENSIC RECORD

## 1. Overview & Architecture
The `orchestrator/` subsystem represents the central reasoning and task execution engine of BR JARVIS. It coordinates context assembly, model invocation, tool calling loops, speculative execution, and dynamic self-healing error recovery.

---

## 2. File-by-File Forensic Analysis

### `orchestrator/core.py` (960 lines)
- **Role**: Canonical Orchestrator Engine (`JarvisOrchestrator`).
- **Core Loop**:
  ```python
  async def process_query(self, user_prompt: str, context: Optional[Dict] = None) -> AsyncGenerator[str, None]:
  ```
- **Lifecycle & Control Flow**:
  1. **Turn Initialization**: Generates a `trace_id` and records user prompt into `events/bus.py` and `history/session_store.py`.
  2. **Context Enrichment**: Ingests recent turns from `memory/working.py`, performs vector recall via `memory/unified_memory.py`, and checks active tasks in `agent/task_state.py`.
  3. **Intent Interception**: Calls `core/intent_engine.py` to evaluate zero-token deterministic rules. If matched, returns immediately.
  4. **Model Selection & Dispatch**: Queries `router/core.py` (or `gateway/model_gateway.py`) to select the optimal model tier.
  5. **Streaming / Tool Invocation Loop**:
     - Consumes LLM token chunks.
     - Detects `<tool_call>` JSON payloads or native function calling frames.
     - Validates tool parameters against schema and passes to `security/policy_engine.py`.
     - Executes tool in `agent/executor.py` and feeds observation back into model context.
     - Maximum re-entrant tool loop limit: `MAX_TOOL_ITERATIONS = 10`.
  6. **Turn Finalization**: Dispatches TTS audio stream to `voice/tts_queue.py` and triggers memory consolidation.
- **Flaws & Risks**:
  - Contains duplicate model calling branches: one branch uses direct `backends/`, another branch routes through `gateway/model_gateway.py`.
  - Manual regex parsing of tool calls coexists with native Gemini/Claude tool-calling JSON schemas.
- **Disposition**: **KEEP + IMPROVE** (Central brain coordinator).

### `orchestrator/speculative.py` (18 lines)
- **Role**: Stub for speculative execution.
- **Disposition**: **CONSOLIDATE** into `reasoning/speculative.py`.
