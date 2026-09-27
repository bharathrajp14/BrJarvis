# BR JARVIS — SYSTEM CONTRACT & DATA BOUNDARY MATRIX

## 1. Subsystem Data Contracts

| Subsystem | Input Contract | Output Contract | Status Enums | Handled Exceptions | Physical Verification Hook | Resource Ownership |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Core Bootstrapper** | Environment vars, CLI flags | `ApplicationRuntime` instance | `INITIALIZING`, `RUNNING`, `STOPPED` | `ConfigurationError` | `Runtime.get_status()` | Runtime Process |
| **Model Gateway** | `ModelRequest` (messages, tools, profile) | `ModelResponse` (text, tool_calls, usage) | `OK`, `RATE_LIMITED`, `CIRCUIT_OPEN` | `ProviderTimeout`, `ProviderRateLimit` | Gateway response envelope check | Gateway Session Pool |
| **Smart Router** | `TaskProfile` (complexity, modalities) | `ModelSelection` (model_id, provider, score) | `ROUTED`, `FALLBACK`, `EXHAUSTED` | `ModelNotFoundError` | Health service status query | Router Engine |
| **Tool Runtime** | `tool_name: str, args: dict` | `ToolResult` (status, data, evidence) | `SUCCESS`, `PARTIAL`, `FAILED`, `DENIED`, `TIMEOUT` | `ToolError`, `ToolTimeout`, `SecurityPolicyError` | `agent/verifier.py :: verify_action` | Process Supervisor |
| **Policy Engine** | 6-Tuple: `(User, Device, App, Res, Act, Risk)` | `PolicyDecision(allowed: bool, reason: str)` | `ALLOWED`, `DENIED`, `REQUIRES_CONFIRMATION` | `SecurityPolicyError` | Denylist lookup & rule evaluation | Policy Engine |
| **Action Verifier** | `tool_name, args, result` | `VerificationResult(verified: bool, details: str)` | `VERIFIED`, `UNVERIFIED`, `FAILED` | `VerificationError` | Physical disk/process/DOM query | Verifier Engine |
| **Artifact Manager** | Content, filename, MIME type | `ArtifactRecord(sandbox_path, host_path, sha256)` | `CREATED`, `EXPORTED`, `OPENED`, `VERIFIED` | `ArtifactError` | `verify_artifact_exported` | Workspace Manager |
| **Canonical DB** | SQL query, parameters, table | SQLite Row / Dict / ID | `COMMITTED`, `ROLLED_BACK`, `BUSY` | `MemoryError`, `sqlite3.OperationalError` | Row count / FTS query check | SQLite Lock Manager |
| **Voice Assistant** | Audio frames (16kHz PCM) | Synthesized speech / Text event | `LISTENING`, `THINKING`, `SPEAKING`, `MUTED` | `STTError`, `TTSError` | VAD probability & sound meter | Audio Stream Handler |
| **Vision Engine** | Monitor index, capture request | `ScreenAnalysisReport(ocr, graph, nodes)` | `CAPTURED`, `UNCHANGED`, `ANALYZED` | `VisionError` | Frame hash comparison | DXGI GPU Capture Bridge |
