# BR JARVIS MK40.2 — Canonical Test Contracts

## 1. Tool & ToolResult Contract
Every tool registered in `ToolRegistry` and executed through `ToolRuntimeEngine` must adhere to:

```python
class ToolExecutionStatus(str, Enum):
    SUCCESS           = "SUCCESS"
    PARTIAL           = "PARTIAL"
    FAILED            = "FAILED"
    TIMEOUT           = "TIMEOUT"
    BLOCKED           = "BLOCKED"
    NOT_AVAILABLE     = "NOT_AVAILABLE"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    DENIED            = "DENIED"

@dataclass
class ToolResult:
    tool_name: str
    task_id: str
    step_id: str
    status: ToolExecutionStatus
    data: Any
    error_code: Optional[str] = None
    message: str = ""
    evidence: str = ""
    execution_ms: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## 2. Model Router & Gateway Failure Contract
Explicit classification of all AI backend failures without collapsing to generic errors:

| Failure Type | HTTP Code | Trigger Condition | Router Handling |
|---|---|---|---|
| `NOT_CONFIGURED` | N/A | Missing API key in `.env` / config | Exclude from routing pool |
| `AUTH_FAILED` | 401 / 403 | Invalid credentials or forbidden | Quarantine provider & trip circuit breaker |
| `UNAVAILABLE` | 404 / 503 | Model name not found or host down | Fallback to next provider candidate |
| `RATE_LIMITED` | 429 | Rate limit hit | Exponential backoff retry or fallback |
| `QUOTA_EXHAUSTED` | 402 / 429 | Credit quota depleted | Immediate failover to alternative provider |
| `TIMEOUT` | 408 / 504 | Read / connect timeout > 30s | Fallback with timeout annotation |
| `INVALID_MODEL` | N/A | Manual model pinning to invalid ID | Reject request with valid catalog hints |
| `NETWORK_ERROR` | ConnectionRefused | DNS / socket failure | Offline local fallback (Ollama) if available |

## 3. Career OS CRM State Machine Contract
State machine strictly governs application lifecycle:
$$\text{DISCOVERED} \to \text{SAVED} \to \text{APPLIED} \to \text{INTERVIEWING} \to \text{OFFERED} \to \text{ACCEPTED} / \text{REJECTED}$$

- Illegal backward jumps (e.g. `OFFERED` $\to$ `SAVED`) are blocked.
- Duplicate applications for identical `(company, job_id)` are rejected.
- Submission verification requires physical evidence (API receipt or verified confirmation URL).
