# BR JARVIS MK40.2 — Failure Injection & Chaos Engineering

## 1. Failure Modes & Chaos Test Coverage

| Failure Mode | Injection Technique | System Reaction | Acceptance Criteria |
|---|---|---|---|
| **Model Timeout** | Simulated 35s latency in model gateway adapter | Fallback to secondary model candidate | No unhandled exception; user receives response from fallback model within timeout budget |
| **Quota Depletion** | HTTP 429 quota exhausted mock | Provider marked circuit-broken for 5m | Instant routing to alternate provider; zero user-facing crash |
| **Corrupt Artifact** | Zero-byte or truncated file header written to disk | `FileVerifier` / `DocumentVerifier` | Verification fails; `TaskCompletionGate` rejects task completion |
| **Hostile Injection** | Prompt injection containing `rm -rf`, `format C:`, or token leak | `PromptInjectionShield` & `PolicyEngine` | Request blocked; security event logged; zero execution |
| **Path Traversal** | Argument containing `../../../../windows/system32` | `SafePathValidator` in sandbox | `PermissionError` raised; scope violation reported |
| **Process Crash** | Subprocess terminating with non-zero exit code | `SandboxedProcessRunner` | Captured stderr; diagnostic diagnosis; auto-repair triggered if dependency missing |
| **Database Lock** | Simulated SQLite busy state under heavy concurrency | `SQLiteWALPool` with retry exponential backoff | Automatic retry succeeds without data loss or corruption |
