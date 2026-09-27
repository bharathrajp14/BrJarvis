# BR JARVIS — ROOT CAUSE DEPENDENCY & PROPAGATION GRAPH

## 1. The Core Failure Propagation Pipeline
```mermaid
graph TD
    %% Root Cause 1: Missing Physical Post-Condition Verification
    RC_Verif[RC-02: Missing Physical Post-Condition Verification] -->|Propagates to| State_Jump[Illegal State Jump: EXECUTED -> COMPLETED]
    State_Jump -->|Generates| False_Success[False Success Synthesis to User]
    
    %% Root Cause 2: Sandbox Path Conflation
    RC_Sandbox[RC-01: Sandbox Path Conflation without Host Export] -->|Passes Virtual Path to| Browser_Nav[Browser Navigation / File Open]
    Browser_Nav -->|Triggers| Err_NotFound[ERR_FILE_NOT_FOUND in Chrome/Edge]
    
    %% Root Cause 3: DPI Coordinate Misalignment
    RC_DPI[RC-03: DPI Coordinate Misalignment] -->|Sends Physical Pixels to| Win32_Input[Win32 SendInput Logical Canvas]
    Win32_Input -->|Results in| Offset_Click[Missed UI Button Clicks]
    
    %% Root Cause 4: Provider Failover Absence
    RC_Router[RC-04: Provider Failover Absence on 429] -->|Raises Exception to| Orch_Halt[Orchestrator Collapse: All Backends Failed]
    
    %% Root Cause 5: Compound Intent Dropping
    RC_Intent[RC-05: Single-Clause Regex Intent Matching] -->|Drops Subsequent Clauses| Partial_Exec[Partial Execution of User Goal]
    
    %% Root Cause 6: Unlocked Database Writes
    RC_DB[RC-06: Unsynchronized SQLite Transactions] -->|Triggers| DB_Lock[sqlite3.OperationalError: database locked]
    
    %% Root Cause 7: Self-Echo Feedback
    RC_Echo[RC-07: Acoustic Self-Echo in Voice Loop] -->|Feeds TTS Output to| Mic_VAD[Microphone VAD Loopback]
    Mic_VAD -->|Causes| Self_Interruption[Assistant Interrupts Itself]
```

---

## 2. Highest-Leverage Root Cause Node
The single node whose resolution eliminates the highest volume of user-facing failure symptoms is:
**`RC-02: Mandatory Physical Post-Condition Verification & Execution Truth`**

Fixing `RC-02` guarantees that regardless of tool failures, timeout anomalies, or sub-agent errors, **false-positive success responses are mathematically impossible**.
