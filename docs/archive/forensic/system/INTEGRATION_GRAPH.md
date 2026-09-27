# BR JARVIS — INTEGRATION BOUNDARY TOPOLOGY & HEALTH GRAPH

## 1. System Integration Boundary Status
- 🟢 **GREEN**: Verified and robust contract.
- 🟡 **YELLOW**: Functional, but requires stricter post-condition verification or DPI/token tuning.
- 🔴 **RED**: Broken invariant or opaque failure path.

```mermaid
graph TD
    User([User Voice / Text / Screen]) -->|🟢 Audio / Text| Normalizer[Input Normalizer & Shield]
    Normalizer -->|🟢 Clean Text| IntentEngine[Deterministic Intent Engine]
    
    IntentEngine -->|🟢 Fast-Path| Policy[6-Tuple Policy Engine]
    IntentEngine -->|🟢 Complex Task| Router[Smart Model Router]
    
    Router -->|🟢 Selected Model| Gateway[Unified Model Gateway]
    Gateway -->|🟡 Cloud / Local API| Adapters[LLM Backends: Gemini/Claude/Ollama]
    
    Adapters -->|🟢 Tool Proposal| Policy
    Policy -->|🟢 Tier & Denylist Check| PathPolicy[Path Security Policy]
    PathPolicy -->|🟢 Authorized Args| ToolRuntime[Universal Tool Runtime]
    
    ToolRuntime -->|🟡 OS / Subprocess / Network| ExternalWorld[Physical OS / Filesystem / Web]
    ExternalWorld -->|🟡 Raw State Result| ActionVerifier[Physical Action Verifier]
    
    ActionVerifier -->|🟢 Verified Observation| OrchestratorContext[Orchestrator Cognitive Loop]
    OrchestratorContext -->|🟢 Epistemic Update| MemoryStore[(Canonical SQLite DB & Vectors)]
    OrchestratorContext -->|🟢 Final Response| TTSQueue[Priority Audio Synthesis & UI]
    
    ToolRuntime -->|🟢 Sandbox Output| ArtifactExport[Artifact Manager SHA256 Export]
    ArtifactExport -->|🟡 Host Path| HostBrowser[Live Browser / Playwright]
    HostBrowser -->|🟡 Page DOM / Screenshot| ActionVerifier
```

---

## 2. Boundary Health Ledger

| Boundary Pair | Health Status | Verification Status | Primary Invariant Enforced |
| :--- | :---: | :---: | :--- |
| `Voice -> Intent Engine` | 🟢 **GREEN** | **VERIFIED** | Wake word & filler removal produce normalized clean text. |
| `Intent Engine -> Fast-Path` | 🟢 **GREEN** | **VERIFIED** | Zero-token instant app launching & audio controls. |
| `Intent Engine -> Smart Router` | 🟢 **GREEN** | **VERIFIED** | Multi-factor routing based on task complexity and latency class. |
| `Smart Router -> Model Gateway` | 🟢 **GREEN** | **VERIFIED** | Circuit breaker, rate-limit backoff, and multi-key rotation. |
| `Model Gateway -> Backends` | 🟡 **YELLOW** | **PARTIALLY VERIFIED** | Requires active cloud keys or local proxy; structured fallback on 429. |
| `LLM Proposal -> Policy Engine`| 🟢 **GREEN** | **VERIFIED** | Deterministic 6-tuple evaluation before any side effect. |
| `Policy Engine -> Path Policy` | 🟢 **GREEN** | **VERIFIED** | Canonical path resolution blocks junction and traversal attacks. |
| `Tool Runtime -> External OS` | 🟡 **YELLOW** | **PARTIALLY VERIFIED** | Subprocess tokens and shell commands executed with explicit timeout. |
| `External OS -> Action Verifier`| 🟡 **YELLOW** | **PARTIALLY VERIFIED** | Verifies physical file existence and process state before `success=True`. |
| `Artifacts -> Host Browser` | 🟢 **GREEN** | **VERIFIED** | Strict `sandbox_path != host_path` with SHA256 export prevents `ERR_FILE_NOT_FOUND`. |
| `Vision Capture -> Coordinate Mapper` | 🟡 **YELLOW** | **PARTIALLY VERIFIED** | DPI scale matrix required for non-100% Windows desktop scaling. |
| `Memory Write -> Canonical DB` | 🟢 **GREEN** | **VERIFIED** | SQLite WAL mode with `sqlite_lock.py` prevents database locked errors. |
