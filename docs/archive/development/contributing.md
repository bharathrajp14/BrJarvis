# BR JARVIS — DEVELOPER CONTRIBUTING GUIDELINES

## 1. Core Architectural Rules
1. **Single Source of Truth**: New capabilities must register through `tools/registry.py` via `@register_tool`.
2. **Explicit Contracts**: Functions must declare typed arguments and return typed DTOs or `ToolResult`.
3. **No Unverified Success**: State-mutating tools must provide post-condition verification in `agent/verifier.py`.
4. **Clean Dependencies**: Subsystems depend downward; platform-specific code is isolated in platform adapters.
