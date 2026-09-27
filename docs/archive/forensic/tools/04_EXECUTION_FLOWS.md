# BR JARVIS — TOOL EXECUTION FLOWS & RUNTIME TRACING

## 1. End-to-End Execution Trace
Tracing the canonical execution path for representative tools:

```text
[1. MODEL TOOL CALL PROPOSAL]
   LLM emits structured JSON tool call: {"tool": "write_file", "args": {"path": "workspace/app.py", "content": "..."}}
     ↓
[2. REGISTRY RESOLUTION]
   tools/registry.py :: execute_tool(tool_name, args)
     ├─ Resolves handler function in TOOL_REGISTRY
     └─ Extracts tool metadata (risk_level, permission_tier, timeout)
     ↓
[3. SECURITY POLICY EVALUATION]
   security/policy_engine.py :: evaluate(User, Device, App, Resource, Action, Risk)
     ├─ security/path_policy.py :: canonicalize(path) & verify not in CRITICAL_DENYLIST
     └─ [APPROVED] -> Proceed to execution
     └─ [DENIED] -> Raise SecurityPolicyError -> Re-plan
     ↓
[4. EXECUTION RUNTIME]
   tools/tool_runtime.py :: execute_with_timeout(handler, args, timeout=30.0s)
     ├─ Subprocess / Native OS / Filesystem Mutation
     └─ Captures stdout, stderr, and exit codes
     ↓
[5. PHYSICAL POST-CONDITION VERIFICATION]
   agent/verifier.py :: verify_action(tool_name, args, result)
     ├─ ActionVerifier.verify_file_created(path) -> Checks physical disk existence & size
     └─ Returns VerificationResult(verified=True/False)
     ↓
[6. OBSERVATION & RESULT SYNTHESIS]
   Orchestrator context updated with verified tool observation -> Model generates response
```
