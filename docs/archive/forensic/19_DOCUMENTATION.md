# 19 — DOCUMENTATION & HISTORICAL RECORD FORENSIC AUDIT

## 1. Documentation Inventory (47 markdown specifications)
The repository contains extensive documentation spanning multiple architectural iterations (MK37, MK38, MK40).

---

## 2. Historical Version Stratification
- **MK37 Era** (`br_architecture/MK37_AUTONOMOUS_OPERATING_SYSTEM_SPEC.md`): Initial autonomous agent vision with separate specialized subagents.
- **MK38 Era** (`BR_JARVIS_FULL_PROJECT_ANALYSIS.md`, `DEVELOPER_WALKTHROUGH.md`, `UI_UX_DESIGN.md`): Monolithic architecture with PySide6 GUI, procedural `actions/`, and direct Gemini API calling.
- **MK40 Era** (`docs/MK40_MIGRATION.md`, `docs/MODERNIZATION_LEDGER.md`): Modern modular architecture introducing `core/bootstrap.py`, `gateway/model_gateway.py`, `workflow/task_dag.py`, and `security/policy_engine.py`.
- **Artifacts Suite** (`ARTIFACT_01_REPOSITORY_AUDIT.md` to `ARTIFACT_05_SECURITY_THREAT_MODEL.md`): Production gap analysis documents.

---

## 3. Documentation Drift & Obsolescence
1. **Startup Instructions**: Legacy README mentions running `python main.py` or `python start.py --gui`, while the canonical modern CLI is `python brjarvis.py` or `python ui_mark.py`.
2. **Backend Config Keys**: Documentation claims support for 20 models, but only 7 provider adapters are actively implemented in `backends/`.
