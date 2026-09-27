# TASK CONTEXT ISOLATION AUDIT — BR JARVIS MK40.2

## 1. The Context Contamination Vulnerability

In previous versions of the system, composite prompts suffered from static template leakage. For example:
- A user requested: *"Perform workspace organization, catalog temporary files, and generate a summary report."*
- `stage_decomposer.py` used hardcoded fallbacks that titled the report: `"OpenClaw vs BR JARVIS Comparison"` and inserted comparative text comparing OpenClaw gateways to BR JARVIS memory.

### Root Causes:
1. Hardcoded string assignments in `_synthesize_comparison()`.
2. Hardcoded fallback branch `doc_title = "OpenClaw vs BR JARVIS Comparison" if "openclaw" in low else "JARVIS System and Architecture Audit"`.
3. Lack of dynamic prompt parameter extraction.

---

## 2. Dynamic Context Isolation Architecture

In MK40.2:
1. **Dynamic Intent Extraction**: Prompts are classified into domain buckets:
   - Workspace Organization & File Audit
   - Professional Resume Revamp
   - Comparative Research & Analysis
   - System Diagnostics & Architecture Audit
2. **Dynamic Topic Extraction**: Titles, filenames, research queries, and document sections are synthesized dynamically from `user_prompt`.
3. **Session & Task State Partitioning**: Every task is keyed by a unique `task_id` (`task_<uuid>`) and state is persisted independently in SQLite WAL tables without shared global mutable state.
