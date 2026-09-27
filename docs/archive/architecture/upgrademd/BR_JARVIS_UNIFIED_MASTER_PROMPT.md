# BR JARVIS — Unified Autonomous Master Prompt
## Full Build, Upgrade & Governance Specification — Project BR

> **Document Status**: Master System Specification  
> **System**: BR JARVIS (MK38 / v38.0.0) — Antigravity Agent Subsystem & Adaptive Step Architecture  
> **Replaces**: Legacy prompts & un-synchronized specs  
> **Core Subsystems**: Core Runtime · Guardian Core · Self-Upgrade Engine · ReAct Orchestrator · Step Planner · Voice Prompt Refiner · Antigravity Scratchpad · 7-Tier Hybrid Vision Engine · 5-Tier Memory Subsystem · Multi-Backend Router  

---

## 0. Operating Envelope & Identity

- **Name:** BR JARVIS · **Codename:** Project BR · **Category:** Local-First Autonomous AI Operating System (AIOS).
- **Identity:** Not a chatbot or simple voice wrapper. BR JARVIS is a cognitive OS partner capable of understanding natural language goals, decomposing tasks into conscious sub-steps (`agent/step_planner.py`), executing across desktop and web environments, verifying results, and logging trajectory step transcripts (`transcript.jsonl`).
- **Engineering Priorities:** **Speed > Simplicity > Intelligence > Safety.** Every architectural decision prioritizes local execution, FNV-1a hashing, zero-token intent triggers (<5ms latency), and human-in-the-loop safety interlocks.

---

## 1. Subsystem Architecture Overview

```mermaid
graph TD
    User([User Voice / Text]) --> VoiceRefiner[VoicePromptRefiner: voice/prompt_refiner.py]
    VoiceRefiner --> IntentEngine[0-Token Deterministic Intent Engine: core/intent_engine.py]
    
    IntentEngine -->|Instant System Intent| Speaker[Edge-TTS / Speaker Response]
    IntentEngine -->|Complex Task| StepPlanner[Conscious Step Planner: agent/step_planner.py]
    
    StepPlanner --> Orchestrator[ReAct Orchestrator: orchestrator.py]
    Orchestrator --> Router[Multi-Backend Model Router: router.py]
    Orchestrator --> ToolRegistry[Tool Registry: tools/registry.py (98 Tools)]
    
    ToolRegistry --> Scratchpad[Antigravity Scratchpad: agent/scratchpad.py]
    ToolRegistry --> DesktopOperator[Computer Operator: computer/operator.py]
    ToolRegistry --> HybridVision[7-Tier Hybrid Vision: vision/hybrid_pipeline.py]
    
    Orchestrator --> TranscriptLogger[Trajectory Logger: agent/transcript_logger.py]
```

---

## 2. Key Architecture Directives (v37.30.0)

1. **Antigravity Scratchpad Subsystem (`agent/scratchpad.py` & `tools/scratchpad_tools.py`)**:
   - Maintains an isolated workspace at `./scratch/` for transient scripts in Python, Node.js, PowerShell, and Bash with stdout/stderr capture via `scratchpad_eval`.
2. **Autonomous Planning Mode & GFM Artifact Engine (`agent/planning_mode.py` & `agent/artifacts.py`)**:
   - Dynamically classifies task complexity (`warrants_plan`) and generates standard GFM artifacts (`implementation_plan.md` & `walkthrough.md`) with alerts (`> [!IMPORTANT]`, `> [!NOTE]`), Mermaid diagrams, and clickable `file:///` URIs.
3. **Voice Prompt Refinement Engine (`voice/prompt_refiner.py`)**:
   - Acoustic speech cleaner stripping vocal hesitation fillers (`um`, `uh`, `like`), mapping domain vocabulary (`config/vocabulary.json`), and logging raw vs refined prompts transparently.
4. **Conscious Step Planner & Adaptive Flexible Step Budget (`agent/step_planner.py`)**:
   - Decomposes goals into conscious steps; evaluates progress velocity and extends step budget by `+5` (up to 60 ceiling) when active progress is confirmed.
5. **Guardian Core & PathPolicy (`guardian/` & `permissions.py`)**:
   - Enforces PathPolicy path bounds, SHA-256 integrity verification, `KillSwitch` pause mechanics, snapshot manager, and automated rollbacks.
