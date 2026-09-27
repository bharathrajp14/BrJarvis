# VERIFICATION ARCHITECTURE — BR JARVIS MK40.2

## 1. Layered Verification Pipeline

Physical verification is divided into distinct, non-fungible verification layers:

```text
[EXECUTION OUTPUT]
       │
       ▼
[Layer 1: Output Contract Validator] ─── Validates stdout/stderr against 12+ error regexes
       │
       ▼
[Layer 2: Physical File Verifier]    ─── Asserts Path.exists(), Path.stat().st_size > 0, SHA-256
       │
       ▼
[Layer 3: Structural Doc Verifier]   ─── Parses PDF header/EOF, DOCX XML structure, JSON schema
       │
       ▼
[Layer 4: Sandbox Security Verifier] ─── Asserts zero path escape into internal sandbox jails
       │
       ▼
[Layer 5: Application / GUI Verifier]─── EnumWindows active title match, process table inspection
       │
       ▼
[Layer 6: Task Completion Gate]     ─── Evaluates C1..Cn criteria matrix, authoritatively sets status
```

---

## 2. Distinction Between Artifact Verification & Open Verification

A core failure mode in earlier versions was treating artifact production as proof of presentation:
- **`ARTIFACT_VERIFIED`**: Deliverable exists on disk, has non-zero size, and parsed without structural errors.
- **`OPEN_VERIFIED`**: An active desktop window whose title matches the file or viewer process is detected on the host OS display.

**Invariant**: `ARTIFACT_VERIFIED` does NOT imply `OPEN_VERIFIED`.
If an artifact is verified on disk but the host window is not detected, the task is marked `PARTIAL_SUCCESS` with evidence:
`"Document verified at 'workspace/Documents/Report.pdf' (5,325 bytes), but viewer window was not confirmed on screen."`
