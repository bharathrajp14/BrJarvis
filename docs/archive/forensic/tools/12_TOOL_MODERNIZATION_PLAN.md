# BR JARVIS — TOOL SUBSYSTEM MODERNIZATION PLAN

## 1. Principles of Modernization
1. **Preserve Working Implementations**: Functionally working tools remain intact.
2. **Standardize Schemas**: Ensure all parameters have explicit JSON types and descriptions.
3. **Enforce Post-Condition Verification**: Pair every mutating tool with an explicit verification routine in `agent/verifier.py`.
4. **Structured Error Normalization**: Return `ToolResult` envelopes with error classifications.
