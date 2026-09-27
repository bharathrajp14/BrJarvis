# 🧩 Context Engine Architectural Specification

> **Module**: `context/` & `orchestrator._resolve_context_references()`  
> **Version**: MK37.31.0  
> **Primary Purpose**: Context window assembly, dynamic token budgeting, sliding window compression, prompt pruning, and anaphoric pronoun reference resolution.

---

## 1. Overview & Key Capabilities

The **Context Engine** handles context lifecycle management for BR JARVIS. It ensures that the LLM receives optimal, relevant background context while preventing token overflow and minimizing payload costs.

### Key Capabilities in v37.31.0
1. **Context-Aware Pronoun & Reference Resolver (`orchestrator._resolve_context_references()`)**:
   - Automatically resolves anaphoric pronouns and target browser commands (e.g. `"open it in brave"`, `"show this in chrome"`).
   - Scans recent working memory history for target URLs, browser windows, or file paths and replaces explicit/implicit references before dispatching to the executor.
2. **8-Priority Scope Hierarchy**:
   - Structured context assembly prioritizing System Instruction > Safety Policies > Direct Goal > Working Memory > RAG Context > Environment Telemetry.
3. **Dynamic Token Budgeting**:
   - Real-time token usage estimation (`context/token_counter.py`) leveraging `tiktoken` or fast character estimation heuristics.
4. **Sliding Window & Payload Compression (`context/compressor.py`)**:
   - Strips redundant system output logs, truncates massive tool responses beyond 800 lines, and preserves critical reasoning traces.

---

## 2. Context Assembly Pipeline

```
Raw User Prompt / Spoken Input
            │
            ▼
[ VoicePromptRefiner (voice/prompt_refiner.py) ]
            │ (Strips vocal fillers: um, uh, like)
            ▼
[ Context Reference Resolver (orchestrator._resolve_context_references) ]
            │ (Resolves "open it", "search that" against Working Memory)
            ▼
[ Context Builder (context/builder.py) ]
            │ (Assembles System Prompt + Policies + Priority Scopes + Memory)
            ▼
[ Token Compressor (context/compressor.py) ]
            │ (Strips redundant output logs & enforces token ceilings)
            ▼
   Optimized LLM Prompt Payload
```

---

## 3. Scope Priorities & Budget Caps

| Scope Tier | Content Description | Priority Level | Token Cap |
|---|---|---|---|
| Tier 1 | System Identity & Core Instructions | Critical (P0) | 1,500 tokens |
| Tier 2 | Guardian Safety Policies & Path Bounds | High (P1) | 800 tokens |
| Tier 3 | Active User Goal & Plan Graph | High (P1) | 1,000 tokens |
| Tier 4 | Working Memory (Recent Turns) | Medium (P2) | 4,000 tokens |
| Tier 5 | Vector RAG & Retrieved Lessons | Medium (P2) | 2,000 tokens |
| Tier 6 | OS Telemetry & Active Window Context | Low (P3) | 500 tokens |
| Tier 7 | Available Tools & Schema Specs | High (P1) | 3,000 tokens |
