# BR JARVIS — COMPREHENSIVE SECURITY & POLICY MODEL

## 1. Defense-in-Depth Security Layers
1. **Input Shield**: `guardian/prompt_injection_shield.py` screens all incoming user and web text for jailbreak and injection patterns.
2. **Deterministic 6-Tuple Policy**: `security/policy_engine.py` validates `(User, Device, App, Resource, Action, Risk)` before side-effect execution.
3. **Canonical Path Security**: `security/path_policy.py` canonicalizes file paths, blocks directory traversal (`../`), and guards critical system folders and secrets (`.env`, `.git`, `id_rsa`).
4. **Process Confinement**: `tools/sandbox_process.py` executes commands with restricted tokens, timeouts, and process-tree termination.
5. **Safe Artifact Export**: `agent/artifacts.py` computes SHA-256 hashes and guarantees isolation between sandbox environments and host directories.
