# BR JARVIS — FINAL TOOL ARCHITECTURE

## 1. Unified Execution Flow

```text
USER INTENT (Web UI / CLI / Voice)
    │
    ▼
ORCHESTRATOR / REACT LOOP
    │
    ├── Tool Selection & Intent-Based Dynamic Pruning (`tools/registry.py`)
    │
    ├── Permission Validation & Security Policy Check (`permissions.py`)
    │
    ├── Prompt Injection Security Audit (`guardian/prompt_injection_shield.py`)
    │
    ├── Centralized Execution Engine (`tools/tool_runtime.py` / `tools/registry.py`)
    │       │
    │       ├── Real Execution (OS / Filesystem / APIs / Subprocesses)
    │       │
    │       └── Telemetry Events (`events/bus.py`)
    │
    ▼
AUTONOMOUS ACTION VERIFIER (`agent/verifier.py`)
    │
    ├── FileVerifier (Existence, Non-Zero Bytes, Structure Parsing)
    ├── ApplicationVerifier (Win32 Window Detection, Process PID)
    ├── BrowserVerifier (Host Path, DOM Content)
    ├── ArtifactVerifier (SHA-256 Checksum, Path Resolution)
    └── GitVerifier / CommandVerifier (Exit Codes, Output)
    │
    ▼
RESULT NORMALIZATION & CONTEXT INJECTION (`ToolResult` / `VerificationResult`)
    │
    ▼
PERSISTENT OPERATIONAL MEMORY (`memory/unified_memory.py`)
    │
    ▼
USER EVIDENCE SUMMARY (Real Turn Outputs, No Hallucinated Claims)
```

## 2. Tool Scoping & Security Classifications
- `READ_ONLY / LOW`: File reads, web searches, status checks, diagnostics. Auto-allowed.
- `WRITE / MEDIUM`: File writes, document creation, calendar events, reminder scheduling. Monitored with logging.
- `DESTRUCTIVE / HIGH`: Code evaluation, command execution, process termination, system configuration changes. Requires confirmation in strict policy modes.

## 3. Resilience & Failover Architecture
- Thread-safe registry lock (`_REGISTRY_LOCK`).
- Fail-closed security permission engine.
- Timeout protection (60s async bridge timeout).
- Operational memory logging for all successes and failures.