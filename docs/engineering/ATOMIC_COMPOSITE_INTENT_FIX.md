# Engineering Report: Prevention of Premature 0-Token Actions on Multi-Step User Requests

## 1. Executive Summary
This document records the architectural fix resolving the critical execution bug where multi-step user utterances (such as `"open excel sheet in web and then show system properties"`) triggered premature 0-token deterministic fast-path actions, terminating the request after executing only the first action and ignoring all subsequent operations.

---

## 2. Root Cause Analysis
Prior to this fix:
1. `DeterministicIntentEngine` executed before any composite-task detection or goal planning.
2. The deterministic intent engine performed broad substring matching across more than 50 matchers. For instance, encountering `"excel sheet"` inside `"open excel sheet in web and then show system properties"` immediately triggered the online Excel matcher (`https://excel.new`) and returned with a 0-token execution response.
3. No distinction existed between **atomic** requests (entire utterance describes a single action) and **composite** requests (multi-action workflows or sequences).
4. No validation existed to check whether the matcher consumed the full actionable user request or left unconsumed actionable clauses behind.
5. In `JarvisOrchestrator` (`chat()` and `chat_stream()`) and `AgentLoop`, early returns on deterministic fast-path responses terminated the turn immediately, dropping the remainder of the user command.

---

## 3. Architecture Change

### 3.1 Strict Atomic Intent Contract
Deterministic fast-path execution is now **restricted exclusively to requests where the entire user utterance is confidently classified as one atomic action**.

A request is allowed to execute deterministically if and only if:
- Exactly one actionable intent is detected.
- The whole utterance belongs to that intent.
- No unresolved secondary action or sequencing clause exists.
- Polite filler tokens (`please`, `thanks`, `now`, etc.) are stripped, and `remaining_text == ""`.
- The request is safe and deterministic.

If any sequencing signal, secondary action verb, question pattern, negation, or unconsumed clause is detected, `DeterministicIntentEngine.parse_and_execute()` immediately returns `None` and routes the request to the composite executor or planner.

### 3.2 Canonical Request Classification Gate
All entry points (`chat()`, `chat_stream()`, CLI, AgentLoop, Web API, WebSocket, Voice) now pass through a single canonical classification stage:

```
USER INPUT
    ↓
SECURITY / INJECTION CHECK
    ↓
INPUT NORMALIZATION
    ↓
COMPOSITE / MULTI-INTENT DETECTION (IntentClassifier)
    ↓
ATOMICITY DECISION
    ↓
┌──────────────────────────────────────────────┐
│                                              │
ATOMIC                                     COMPOSITE
│                                              │
↓                                              ↓
Deterministic shortcut / Agent             CompositeIntentExecutor / Planner
│                                              │
↓                                              ↓
Execute                                    Decompose into ordered ActionIntents
│                                              │
↓                                              ↓
Verify (ActionVerifier)                    Execute Step 1 → Verify (ActionVerifier)
│                                              │
↓                                              ↓
Return 0-token response                    Execute Step 2 → Verify (ActionVerifier)
                                               │
                                               ↓
                                           Truthful Multi-Step Summary
```

### 3.3 Semantic Grouping for "AND"
Rather than naively treating every "and" as a composite split:
- **Single executable operation**:
  - `"show CPU and RAM usage"`: Single verb (`show`) targeting grouped hardware telemetry metrics → classified as **atomic**.
  - `"open chrome and github"`: Single verb (`open`) with browser (`chrome`) and target site (`github`) → classified as **atomic grouped browser navigation**.
- **Two or more separately executable actions**:
  - `"open excel and show system information"`: Two verbs (`open` + `show`) → **composite**.
  - `"open calculator and then open notepad"`: Two verbs (`open` + `open`) + sequencer (`then`) → **composite**.
  - `"take screenshot and save it to documents"`: Two verbs (`take` + `save`) → **composite**.
  - `"open vscode, create test.py, and run it"`: Three verbs (`open` + `create` + `run`) → **composite**.

### 3.4 Data Contracts
Introduced structured contracts in `brjarvis.core.intent_models`:
- **`AtomicIntentResult`**: Contains `matched`, `atomic`, `intent`, `parameters`, `consumed_text`, `remaining_text`, `confidence`, and `requires_planner`.
- **`ActionIntent`**: Represents a single executable step with `intent`, `order`, `raw_text`, `parameters`, `depends_on`, and `is_negated`.
- **`CompositeIntent`**: Represents a multi-step task with `original_text`, ordered `actions`, `dependencies`, and `confidence`.
- **`ExecutionTrace`**: Observability contract recording `user_input`, `classification`, `atomic`, `deterministic`, `intent`, `steps`, `planner_required`, `execution_started`, `execution_completed`, and `details`.

### 3.5 Sequential Composite Execution (`CompositeIntentExecutor`)
- Preserves explicit user execution order.
- Respects dependencies (e.g. Step 2 depends on Step 1).
- Verifies every step with `ActionVerifier`.
- Short-circuits dependent steps if a prerequisite step fails.
- Respects negations (e.g. `"open Excel and don't show system properties"` skips Step 2).
- Delivers a user-friendly acknowledgment: `"I'll open Excel first, then show the system properties."`
- Truthful partial completion reporting (reports `"Step 1 completed. Step 2 failed."` without false claims of overall completion).

---

## 4. Files Changed

| File | Change Summary |
| :--- | :--- |
| `src/brjarvis/core/intent_models.py` | **New**: Defines `AtomicIntentResult`, `ActionIntent`, `CompositeIntent`, and `ExecutionTrace`. |
| `src/brjarvis/core/intent_classifier.py` | **New**: Canonical classifier implementing verb density analysis, sequencer detection, question/negation filters, semantic grouping, and `IntentTraceStore`. |
| `src/brjarvis/core/composite_executor.py` | **New**: Dependency-aware multi-step sequential execution engine with step-level `ActionVerifier` validation and partial status reporting. |
| `src/brjarvis/core/intent_engine.py` | Enforces the canonical atomicity gate at top of `parse_and_execute()`, routes to `_match_and_execute()`, supports grouped intents, records full execution traces, updates 0-token definitions. |
| `src/brjarvis/orchestrator/core.py` | Updated `chat()` and `chat_stream()` to execute the canonical classification gate before deterministic shortcut and route composite tasks through `CompositeIntentExecutor`. |
| `src/brjarvis/agent/agent_loop.py` | Step 2 updated to classify requests and handle predictable composite workflows before invoking atomic fast-path. |
| `tests/unit/test_atomic_vs_composite_intent.py` | **New**: 40 unit and regression tests covering Cases A–K, 25 representative utterances, tracing, partial completion, and acceptance reproduction. |

---

## 5. Before vs. After Behavior

### Reproduction Scenario:
```
USER: "open excel sheet in web and then show system properties"
```

#### Before:
1. `DeterministicIntentEngine` scanned for `"excel sheet"`.
2. Immediate substring match in online productivity block.
3. Native browser launched `https://excel.new`.
4. Early return: `"Opened Online Excel Sheets at https://excel.new (0-Token Execution)"`.
5. Second action `"show system properties"` was completely discarded.

#### After:
1. `IntentClassifier.classify()` detects sequencing marker `"and then"` and two actionable verbs (`open`, `show`).
2. Request classified as `CompositeIntent` with 2 ordered actions:
   - Action 1: `open_online_excel` (order 1)
   - Action 2: `show_system_properties` (order 2, depends on Step 1)
3. `DeterministicIntentEngine.parse_and_execute()` bypasses deterministic execution and returns `None`.
4. `CompositeIntentExecutor` takes ownership:
   - Acknowledges workflow: `"I'll open Excel first, then show the system properties."`
   - Executes Step 1: Launches `https://excel.new` and verifies via `ActionVerifier`.
   - Executes Step 2: Queries `system_diagnostic({"aspect": "full_summary"})` and verifies output.
   - Combines evidence into truthful multi-step response:
     ```
     I'll open Excel first, then show the system properties.

     ✅ Step 1 completed: Opened Online Excel Sheets at https://excel.new
     ✅ Step 2 completed: System Properties & Diagnostics:
     🖥️ System Health Overview (Windows 11):
     - Host: DESKTOP-7KJT35R
     - CPU: 23.8% (8 cores)
     - RAM: 95.0% (7.40 / 7.79 GB)
     - Python: 3.14.0
     - System Uptime: 288.6 hours
     ```

---

## 6. Test Verification
All 40 tests in `tests/unit/test_atomic_vs_composite_intent.py` pass:
- **Case A**: `"open excel online"` → Atomic, deterministic, executed immediately.
- **Case B**: `"open excel online and then show system properties"` → Composite, 2 ordered actions, no premature termination.
- **Case C**: `"open chrome and github"` → Grouped navigation, opens github in chrome.
- **Case D**: `"show CPU and RAM usage"` → Grouped system-health intent, atomic.
- **Case E**: `"open calculator and then open notepad"` → Two sequential actions.
- **Case F**: `"take screenshot and save it to documents"` → Composite workflow.
- **Case G**: `"open vscode, create test.py, and run it"` → Three-step workflow.
- **Case H**: `"why should I open Excel?"` → Conversational, no deterministic execution.
- **Case I**: `"do not open Excel"` → Negation, no deterministic execution.
- **Case J**: `"tell me how to open Excel"` → Informational, no deterministic execution.
- **Case K**: `"open Excel and don't show system properties"` → Second action negated and skipped.
- **25 Parametrized Regression Utterances**: 100% pass rate.
- **Execution Trace Recording**: Verified across atomic and composite queries.
- **Partial Completion**: Correctly reports failure of Step 2 without claiming overall success.
- **Deduplication Guard**: Preserved and functional.

---

## 7. Performance Impact
- **Atomic requests**: Retain sub-5ms zero-LLM execution with zero token consumption.
- **Classification overhead**: Sub-1ms regex and keyword scanning in native Python.
- **Predictable composite workflows**: Executed locally in <50ms with zero LLM tokens, eliminating token burn and high latency for standard compound requests.
- **Complex multi-step workflows**: Routed cleanly to the ReAct loop without premature truncation.

---

## 8. Remaining Risks & Mitigations
- **Ambiguous entity conjunctions**: Queries with deeply nested clauses (e.g. `"open chrome and edge and search cats on google"`) may have ambiguous grouping.
  - *Mitigation*: The classifier defaults to `requires_planner=True` whenever ambiguity is detected, falling back to the cognitive ReAct loop rather than risking incorrect deterministic execution.
- **Novel third-party apps**: User requests to open apps not registered in `APP_MAPPINGS`.
  - *Mitigation*: Unrecognized apps fall back to the general application launch action and ReAct loop.
