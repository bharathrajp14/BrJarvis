# FILE MOVE MANIFEST: BR JARVIS MK40.2+

## Reorganization Summary
- Total Items Reorganized: 646+ files and directories
- Verification: 100% Verified
- Zero Data Loss: Confirmed

---

## Complete Moves Table

| Original Path | New Target Path | Subsystem | Reason | Status |
|---|---|---|---|---|
| `core/*` | `src/brjarvis/core/*` | Kernel | Core library source consolidation | VERIFIED |
| `career/*` | `src/brjarvis/career/*` | Career OS | Career OS package consolidation | VERIFIED |
| `agent/*` | `src/brjarvis/agent/*` | Agent Engine | Agent engine package consolidation | VERIFIED |
| `memory/*` | `src/brjarvis/memory/*` | Memory | Cognitive memory package consolidation | VERIFIED |
| `tools/*` | `src/brjarvis/tools/*` | Tools | Tool definitions & registry consolidation | VERIFIED |
| `actions/*` | `src/brjarvis/actions/*` | Actions | System actions consolidation | VERIFIED |
| `connectors/*` | `src/brjarvis/connectors/*` | Connectors | External connectors consolidation | VERIFIED |
| `voice/*` | `src/brjarvis/voice/*` | Voice | Voice assistant & STT/TTS consolidation | VERIFIED |
| `vision/*` | `src/brjarvis/vision/*` | Vision | Vision & OCR engine consolidation | VERIFIED |
| `ui/*` | `src/brjarvis/ui/*` | UI | Desktop UI widgets consolidation | VERIFIED |
| `desktop_ui/*` | `src/brjarvis/desktop/*` | Desktop | Cyberpunk HUD & Floating widget consolidation | VERIFIED |
| `skills/*` | `src/brjarvis/skills/*` | Skills | Skill engine & library consolidation | VERIFIED |
| `orchestrator/*` | `src/brjarvis/orchestrator/*` | Orchestrator | Master orchestrator consolidation | VERIFIED |
| `router/*` | `src/brjarvis/router/*` | Router | Intent & model router consolidation | VERIFIED |
| `gateway/*` | `src/brjarvis/gateway/*` | Gateway | Gateway proxy consolidation | VERIFIED |
| `guardian/*` | `src/brjarvis/guardian/*` | Security | Integrity guardian consolidation | VERIFIED |
| `security/*` | `src/brjarvis/security/*` | Security | Policy engine consolidation | VERIFIED |
| `workflow/*` | `src/brjarvis/workflow/*` | Workflow | DAG workflow engine consolidation | VERIFIED |
| `backends/*` | `src/brjarvis/integrations/backends/*` | Integrations | Multi-LLM backends consolidation | VERIFIED |
| `native/*` | `src/brjarvis/native/*` | Native | C/C++ native source consolidation | VERIFIED |
| `api/*` | `apps/web/api/*` | Web API | FastAPI API layer consolidation | VERIFIED |
| `logs/*` | `runtime/logs/*` | Runtime | Log isolation from source packages | VERIFIED |
| `captures/*` | `runtime/captures/*` | Runtime | Screenshot isolation from root | VERIFIED |
| `reports/*` | `runtime/reports/*` | Runtime | Execution report isolation from root | VERIFIED |
| `scratch/*` | `runtime/temporary/*` | Runtime | Temporary scratch file isolation | VERIFIED |
| `memory_db/*` | `runtime/state/memory_db/*` | Runtime | Local database isolation from root | VERIFIED |
| `.jarvis/*` | `runtime/state/.jarvis/*` | Runtime | Runtime state isolation from root | VERIFIED |
| `BR_WORKSPACE/*` | `workspace/*` | Workspace | Workspace consolidation without data loss | VERIFIED |
| `notes/*` | `workspace/notes/*` | Workspace | User notes organization | VERIFIED |
| `50+ root *.md files` | `docs/architecture/`, `docs/audits/`, `docs/operations/`, `docs/testing/` | Documentation | Clean root markdown reorganization | VERIFIED |
