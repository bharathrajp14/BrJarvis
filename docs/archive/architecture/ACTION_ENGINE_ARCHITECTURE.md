# ACTION ENGINE ARCHITECTURE: BR JARVIS Autonomous Operating Agent

**Architecture Version:** MK40.2 Universal Execution Architecture  
**Author:** BR JARVIS Systems Architecture Group  
**Status:** Approved & Implemented  

---

## 1. Architectural Philosophy

BR JARVIS is fundamentally an **action-oriented autonomous operating system agent**, not a chatbot. It adheres to the primary execution axiom:

> **"JARVIS must stop describing actions and start actually performing, verifying, and completing actions. A claim of success is forbidden unless the operation actually happened and was independently verified."**

---

## 2. Complete End-to-End Execution Pipeline

```
                     USER REQUEST (Voice / CLI / Web)
                                  │
                                  ▼
                     INTENT & TASK CLASSIFICATION
                                  │
                                  ▼
                     HIERARCHICAL MEMORY RECALL
                   (L0–L6: Facts, Preferences, Trajectories)
                                  │
                                  ▼
                     DYNAMIC EXECUTION PLANNING
                   (StageDecomposer / AgentExecutor)
                                  │
                                  ▼
                     UNIVERSAL TOOL ROUTING
                   (Central Registry with Auto-Discovery)
                                  │
                                  ▼
                     DETERMINISTIC PERMISSION CHECK
                   (6-Tuple Security Engine: Fail-Closed)
                                  │
                                  ▼
                     REAL-WORLD OPERATION EXECUTION
                   (OS / Filesystem / Web / Applications)
                                  │
                                  ▼
                     MULTI-LAYERED ACTION VERIFIER
                   (FileVerifier, ApplicationVerifier, BrowserVerifier)
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
            [SUCCESS_VERIFIED]        [FAILURE / PARTIAL]
                     │                         │
                     ▼                         ▼
            ARTIFACT REGISTRATION       RECOVERY ENGINE
             (SHA-256 + Host Path)     (Bounded Replan / Retry)
                     │                         │
                     └────────────┬────────────┘
                                  ▼
                     OPERATIONAL MEMORY UPDATE
                   (L6 Experience Replay Learning)
                                  │
                                  ▼
                     EVIDENCE-BACKED RESPONSE
```

---

## 3. Generalized ActionVerifier Architecture

The verification layer enforces zero hallucinated success states through dedicated strategy verifiers:

```
                          ActionVerifier
                                │
        ┌──────────────┬────────┼──────────────┬──────────────┐
        ▼              ▼        ▼              ▼              ▼
   FileVerifier   AppVerifier  BrowserVerifier ArtifactVerifier GitVerifier
        │              │        │              │              │
   - Exists       - Process    - Valid URL     - Exported     - Clean Tree
   - Non-zero     - PID Active - DOM Render    - SHA-256 Hash - Commit Valid
   - Parse DOCX   - Win32 GUI  - No ERR_FILE   - Readable     - Branch Valid
   - Parse PDF      Window
   - Parse XLSX
```

### Verification Result Contract

Every verification check produces a standardized `VerificationResult`:

```python
@dataclass
class VerificationResult:
    verified: bool
    status: VerificationStatus  # SUCCESS_VERIFIED, SUCCESS_UNVERIFIED, PARTIAL_SUCCESS, FAILED, BLOCKED
    evidence: str               # Human-readable evidence (e.g. "DOCX parsed (12 paragraphs, 3 tables)")
    details: str                # Diagnostic description
    error: Optional[str]        # Error code (e.g. FILE_NOT_FOUND, ERR_FILE_NOT_FOUND, PARSE_ERROR)
    metadata: Dict[str, Any]    # Raw metrics (size_bytes, pid, paragraphs, tables, hash)
```

---

## 4. Normalized Tool Execution Contract

Tools return structured records normalized across all callers (ReAct loop, StageExecutionEngine, and AgentExecutor):

```json
{
  "status": "SUCCESS_VERIFIED",
  "tool": "create_word_document",
  "message": "Created Executive Document (DOCX): 'workspace/Documents/Comparison.docx'",
  "artifact": {
    "path": "D:\\BRJARVIS\\Br-Jarvis\\workspace\\Documents\\Comparison.docx",
    "format": "docx",
    "size_bytes": 48290,
    "sha256": "3a8b...1f9c"
  },
  "verification": {
    "verified": true,
    "method": "ActionVerifier.verify_file_parsed",
    "evidence": "DOCX parsed successfully (18 paragraphs, 2 tables, 14,200 chars)"
  },
  "error": null
}
```

---

## 5. Artifact Lifecycle Management

To prevent sandbox escape, path traversal, or unverified deliveries, all generated user deliverables follow a strictly verified 5-stage lifecycle:

```
[1. CREATE]  ──▶  [2. VALIDATE]  ──▶  [3. REGISTER]  ──▶  [4. LAUNCH]  ──▶  [5. VERIFY OPEN]
 In Sandbox         FileVerifier        ArtifactManager     open_app          Win32 Window /
 or Workspace       Structure & Size    SHA-256 + Host Path Native Viewer     Process PID
```

---

## 6. L6 Operational Trajectory Learning

When a task completes or fails:
1. The execution trajectory (goal, tool sequence, verification result, error) is recorded in `UnifiedMemory.record_operational_lesson()`.
2. Future tasks retrieve past successes to reuse effective patterns, and retrieve past pitfalls to avoid repeating failed approaches.
3. Secrets, API keys, and sensitive tokens are automatically redacted before storage.

---

## 7. Multi-Interface Consistency

The same Action Engine powers all interfaces:
- **Voice HUD (`voice/assistant.py`):** Speaks clean evidence summaries and partial states truthfully.
- **Web UI (`web/app.js`):** Displays real-time timeline steps, tool outputs, and verified artifact links.
- **CLI (`brjarvis.py` / `start.py`):** Outputs formatted step progress with pass/fail indicators.
