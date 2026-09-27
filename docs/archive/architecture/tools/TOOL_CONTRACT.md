# BR JARVIS — Canonical Tool Contract Specification

**Document Version:** MK40.2 / MK41 Canonical Rebuild  
**Classification:** Technical Contract & Specification  
**Status:** Authoritative  

---

## 1. Tool Lifecycle Specification

Every capability execution in BR JARVIS must strictly adhere to the 12-stage execution lifecycle:

```text
1. RESOLVE          → Translate requested tool name/version to registered ToolDefinition.
2. VALIDATE         → Strictly validate arguments against JSON Schema (reject unknown properties).
3. NORMALIZE        → Deterministically sanitize paths, URLs, booleans, enums, timeouts.
4. AUTHORIZE        → Evaluate 6-Tuple Policy (User, Device, Application, Resource, Action, Risk).
5. APPROVAL CHECK   → Interlock high-risk / confirmation-mandated operations.
6. IDEMPOTENCY      → Deduplicate repeated side-effect mutations; evaluate read-only cache.
7. EXECUTION        → Sandboxed invocation under strict per-tool timeouts.
8. OBSERVATION      → Extract structured physical delta (subject, old_state, new_state, evidence).
9. VERIFICATION     → Perform deterministic verification check (file on disk, window active, process running).
10. CONTRACT        → Construct canonical ToolResult with explicit status enum and proof.
11. LEDGER / STATE  → Write immutable entry to ExecutionLedger & TaskStateManager WAL.
12. ADMISSION       → Emit EventBus notifications; conditionally admit observations to memory.
```

---

## 2. ToolDefinition Contract

Every registered tool must explicitly declare:

```python
@dataclass
class ToolDefinition:
    tool_id: str                      # e.g., "filesystem.write"
    name: str                         # primary invocation name, e.g., "file_write"
    version: str = "1.0.0"
    description: str = ""
    category: ToolCategory = ToolCategory.GENERAL
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Security & Governance
    risk_level: RiskLevel = RiskLevel.LOW
    permission_required: str = "PUBLIC_READ"
    approval_required: bool = False
    
    # Execution Properties
    read_only: bool = False
    idempotent: bool = True
    retryable: bool = True
    parallel_safe: bool = True
    side_effect_level: SideEffectLevel = SideEffectLevel.READ_ONLY
    
    # Limits & Timing
    timeout_sec: float = 30.0
    max_retries: int = 2
    supports_async: bool = False
    
    # Strategies & Policies
    verification_strategy: VerificationStrategy = VerificationStrategy.NONE
    cache_policy: CachePolicy = CachePolicy.NO_CACHE
    resource_reads: List[str] = field(default_factory=list)
    resource_writes: List[str] = field(default_factory=list)
```

---

## 3. ToolResult Contract

All tool executions must yield a canonical `ToolResult`:

```python
@dataclass
class ToolResult:
    tool_name: str
    status: ToolExecutionStatus
    task_id: str = ""
    step_id: str = ""
    invocation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    data: Any = None
    evidence: str = ""
    verified: bool = False
    error_code: Optional[str] = None
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_ms: float = 0.0
    observation: Optional[Observation] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
```

---

## 4. Status Vocabulary

```python
class ToolExecutionStatus(str, Enum):
    SUCCESS             = "SUCCESS"             # Action executed and physically verified
    PARTIAL             = "PARTIAL"             # Action partially executed
    FAILED              = "FAILED"              # Unrecoverable error during execution
    TIMEOUT             = "TIMEOUT"             # Execution exceeded timeout budget
    BLOCKED             = "BLOCKED"             # Security policy blocked execution
    DENIED              = "DENIED"              # Explicit policy denial
    REQUIRES_APPROVAL   = "REQUIRES_APPROVAL"   # Paused pending human confirmation
    NOT_FOUND           = "NOT_FOUND"           # Tool does not exist in registry
    NOT_AVAILABLE       = "NOT_AVAILABLE"       # Tool missing host dependencies
    UNSUPPORTED         = "UNSUPPORTED"         # Tool unsupported on current OS platform
    CANCELLED           = "CANCELLED"           # Cancelled by user or watchdog
    RETRYABLE_FAILURE   = "RETRYABLE_FAILURE"   # Transitory network or resource conflict
    VERIFICATION_FAILED = "VERIFICATION_FAILED" # Action ran but physical state mismatch
    STATE_MISMATCH      = "STATE_MISMATCH"      # Pre-condition check failed
```

---

## 5. Standardized Observation Model

```python
@dataclass
class Observation:
    subject: str                  # e.g., "file:///d:/BRJARVIS/workspace/report.docx"
    property: str                 # e.g., "size_bytes", "window_title", "volume_level"
    old_state: Optional[Any] = None
    new_state: Optional[Any] = None
    evidence: str = ""            # Verifiable proof string
    confidence: float = 1.0       # Confidence in observation [0.0 - 1.0]
    source: str = "tool_runtime"
    timestamp: float = field(default_factory=time.time)
```

---

## 6. Canonical Error Model

```python
class ToolErrorCode(str, Enum):
    INVALID_ARGUMENT       = "INVALID_ARGUMENT"
    SCHEMA_VALIDATION_ERR  = "SCHEMA_VALIDATION_ERR"
    TOOL_NOT_FOUND         = "TOOL_NOT_FOUND"
    DEPENDENCY_MISSING     = "DEPENDENCY_MISSING"
    PERMISSION_DENIED      = "PERMISSION_DENIED"
    POLICY_DENIED          = "POLICY_DENIED"
    APPROVAL_REQUIRED      = "APPROVAL_REQUIRED"
    TIMEOUT_EXCEEDED       = "TIMEOUT_EXCEEDED"
    EXECUTION_EXCEPTION    = "EXECUTION_EXCEPTION"
    VERIFICATION_FAILED    = "VERIFICATION_FAILED"
    PATH_TRAVERSAL_BLOCKED = "PATH_TRAVERSAL_BLOCKED"
    RESOURCE_CONFLICT      = "RESOURCE_CONFLICT"
    RATE_LIMITED           = "RATE_LIMITED"
    CANCELLED              = "CANCELLED"
```
