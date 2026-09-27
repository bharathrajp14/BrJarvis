# BR JARVIS — Master Remediation Prompt
**For: Antigravity, Gemini 3.5/3.6 Flash (High)**
**Source: cross-referenced audit of all 21 docs in `br_archetecture/` (including `fullproject.md`, `README.md`, `ROADMAP.md`, `PROJECT_VISION.md`)**

---

## HOW TO USE THIS

Paste this whole file into a new Antigravity task against the `BrJarvis` repo. Run it in **Review-driven** or **Agent-assisted** mode, not Autopilot — Phase 1 touches the privacy-routing and self-upgrade-deployment logic, and you want to see each diff before it lands. Phase 0 is mandatory and gates everything after it: do not let the agent skip to "fixing" something it hasn't first confirmed is actually broken. If it runs out of steam partway through, it's fine to stop after a phase and resume in a new session — each phase is self-contained.

---

## ROLE

You are working directly in the `BrJarvis` repository (`d:\BRJARVIS\Br-Jarvis`). The `br_archetecture/` docs describing this codebase contain multiple internal contradictions — some are stale docs, some may be doc claims that were never actually implemented. Your job in this pass is not to trust the docs' "✅ Production" / "100%" labels. Your job is to check the actual source, fix what's actually broken, and correct any doc that doesn't match reality — in that order.

---

## PHASE 0 — GROUND TRUTH AUDIT (mandatory, do this before any fix below)

Run each of these and paste the raw output. Do not summarize, do not round up, do not say "looks good" — paste the command and its exact result.

1. **Real test counts.** Run `python -m pytest tests/ -v`, `python test_deep_audit.py`, and `python scripts/smoke_startup.py` (referenced in CHANGELOG's 37.4.0 entry) separately. `ROADMAP.md` claims 58 = 42 (deep audit) + 11 (integration) + 5 (smoke); `full_repository_audit.md` presents pytest-58 and deep-audit-42 as two independent totals; `fullproject.md`'s own banner says "42/42 Deep Audit + Integration Tests" as if integration is folded into the 42. Determine which relationship is actually true.
2. **DeepSeek backend.** Run `ls backends/` and `grep -rn "DeepSeek\|deepseek\|AgentProfile.DEEPSEEK" router.py backends/`. `fullproject.md` claims a 7th backend at `backends/deepseek.py` is "✅ Production." `MODEL_ROUTER.md` and `PROJECT_STRUCTURE.md` both list exactly 6 backends and never mention DeepSeek, and `ROUTING_RULES` in `MODEL_ROUTER.md` never references an `AgentProfile.DEEPSEEK`. Does the file exist and is it wired into the router or not?
3. **Real tool/action/skill counts.** Run `ls tools/*.py | wc -l`, `grep -rn "@register_tool" tools/ | wc -l`, `ls actions/*.py | wc -l` (confirm this directory even exists — `PROJECT_STRUCTURE.md` never lists it despite `fullproject.md`, `CHANGELOG.md`, and `ARCHITECTURE.md` all referencing `actions/live_os_control.py`), and whatever `skills/loader.py` reports as its discovered-skill count at runtime.
4. **`ui.py` framework.** Run `grep -n "^import\|^from" ui.py | grep -iE "tkinter|pyside|pyqt"`. `TECHNICAL_DEBT.md` calls it a "69 KB PySide interface"; `fullproject.md` calls it "Tkinter desktop UI (71KB, 1554 lines)." These are different toolkits — confirm which one is real.
5. **Context token budget.** Run `grep -n "max_tokens" context/engine.py context/token_manager.py`. `CONTEXT_ENGINE.md`'s own code sample initializes `ContextEngine(max_tokens=8192)`, but the same doc states real compression only triggers past 128,000–1,000,000 tokens, and `ARCHITECTURE.md` states Working Memory holds a 120K-token window. Confirm whether 8192 is just a stale illustrative default or an actual hardcoded ceiling that's silently over-compressing every request.
6. **Blast-radius tiers.** Run `grep -n "LOW\|MEDIUM\|HIGH\|CRITICAL" evolution/classifier.py`. `PROJECT_STRUCTURE.md` and `ARCHITECTURE.md` say 4 tiers (adds CRITICAL); `fullproject.md`'s own subsystem table says 3 (LOW/MEDIUM/HIGH only).
7. **RedTeam module.** Run `find . -iname "*redteam*"`. `SECURITY.md` lists `redteam/` as a covered module path with its own pipeline stage; nothing in `PROJECT_STRUCTURE.md`'s full tree shows this directory, and the only real reference anywhere is `tools/redteam_tools.py`.

Report all seven results before proceeding to Phase 1.

---

## PHASE 1 — CRITICAL (safety, privacy, approval-gate correctness)

### 1. `local_private` routing falls back to a cloud backend — breaks the project's own privacy guarantee
- **File**: `router.py`, `ROUTING_RULES["local_private"]`
- **Problem**: Currently `[AgentProfile.OLLAMA, AgentProfile.GEMINI]`. `PROJECT_VISION.md` states as a core principle: *"Local-First & Privacy-Focused: Prioritizes local AI models... whenever possible."* A task explicitly classified `local_private` is, by definition, meant to never leave the device. If Ollama is down, silently rerouting to Gemini breaks that promise with zero warning to the user.
- **Fix**: Remove any cloud backend from the `local_private` fallback chain. On Ollama failure, fail closed — return an explicit error ("local model unavailable; task not sent to cloud because it was marked private") rather than silently rerouting. Audit `gpu_inference`'s `[AgentProfile.NVIDIA, AgentProfile.GEMINI]` too: confirm whether the NVIDIA NIM endpoint is self-hosted or a cloud microservice, and if it's meant to stay local, apply the same fail-closed rule.

### 2. Self-upgrade `AutoDeployer` has no confirmed human-approval gate before deploying
- **Files**: `evolution/deployer.py`, `evolution/classifier.py`, `guardian/autonomy_policy.yaml`, `guardian/core.py`
- **Problem**: `PROJECT_VISION.md` principle #4: *"Destructive OS operations... **production deployments**... automatically require explicit user approval via safety interlocks before execution."* Every doc describing the self-upgrade pipeline shows `SandboxRunner` passing → `AutoDeployer` deploying, with no document anywhere stating that a HIGH or CRITICAL blast-radius change is blocked pending human confirmation. The only human-in-the-loop gate documented in detail anywhere is for `computer/operator.py`'s destructive OS actions — a completely different subsystem.
- **Fix**: Read `guardian/autonomy_policy.yaml` and confirm it actually defines per-tier approval requirements. Confirm `evolution/deployer.py` reads and enforces that policy immediately before deploy (not just before sandboxing). If it doesn't, add a hard block: anything classified above LOW pauses for explicit user confirmation before `deployer.py` writes to the live codebase. Separately, confirm `guardian/core.py`'s SHA-256 integrity baseline is updated atomically as part of a legitimate deploy — otherwise real self-upgrades either falsely trip the integrity check, or the baseline-update path is itself an unguarded write that defeats the point of the check.

### 3. RedTeam / prompt-injection defense is referenced as an active gate but isn't a real module
- **Files**: expected `redteam/` (per `SECURITY.md`'s own header), actual likely just `tools/redteam_tools.py`
- **Problem**: `SECURITY.md` lists `redteam/` as a covered module path and its own pipeline diagram shows "RedTeam Prompt Injection Audit → Injection Detected → Quarantine Execution & Raise SecurityAlert" as a live gate. `PROJECT_STRUCTURE.md`'s full directory tree has no `redteam/` package. The only real mention anywhere is one line in `PLUGIN_SYSTEM.md` describing `tools/redteam_tools.py` as "security auditing, prompt injection testing" — a tool file, not a verified gate in the execution path. This matters concretely: `vision/ocr_engine.py` reads arbitrary on-screen text and `vision/dom_bridge.py` reads arbitrary web page DOM content, both feeding into the same context that drives `computer/operator.py`'s clicks and keystrokes. That's a real indirect-prompt-injection surface for a computer-use agent, and nothing verified in the docs currently inspects that content before it can influence a tool call.
- **Fix**: Either implement the injection check as a real, tested gate inside `tools/tool_runtime.py` — specifically in the path that handles OCR- or DOM-derived text before it can trigger a tool call — and correct `SECURITY.md` to describe it accurately where it actually lives; or, if `redteam/` genuinely exists in the real repo and Phase 0.7 just missed it, add it properly to `PROJECT_STRUCTURE.md` with the same evidence standard as everything else claiming ✅ Production (a real test, one example of a caught injection).

---

## PHASE 2 — HIGH (functional correctness, reliability, architecture clarity)

### 4. GPT backend identity is unresolved — gpt-4o and gpt-oss-120b are different providers
- **File**: `backends/openai_compat.py`, `router.py`
- **Problem**: `MODEL_ROUTER.md` states the default is `gpt-4o` / `gpt-4o-mini` (OpenAI's hosted proprietary API). `fullproject.md`'s own router table says `gpt-oss-120b-medium` (OpenAI's open-weight model — different host, different auth, different rate limits entirely). `ARCHITECTURE.md` hedges with "GPT-4o / OSS 120B." These aren't cosmetic — a wrong assumption here silently breaks the "code" and "analysis" routing categories, which both list GPT as a candidate.
- **Fix**: Check `backends/openai_compat.py`'s actual default `model=` value and target endpoint. Make every doc state the same one.

### 5. DeepSeek backend — wire it in properly or remove every reference
- Once Phase 0.2 resolves whether `backends/deepseek.py` exists: if yes, add `AgentProfile.DEEPSEEK` to `ROUTING_RULES` where it's meant to sit (fullproject.md suggests "Reasoning" tasks) with a real fallback candidate, and add it to `MODEL_ROUTER.md`'s backend table. If no, strip it from `ARCHITECTURE.md`'s and `fullproject.md`'s diagrams so the "7 backends" claim doesn't keep circulating.

### 6. `search` and `vision` routing have no real fallback — single point of failure
- **File**: `router.py`, `ROUTING_RULES`
- **Problem**: Every routing category has 2–3 candidate backends except `"search": [AgentProfile.GEMINI]` and `"vision": [AgentProfile.GEMINI]`. The documented self-healing failover falls back to Gemini on any backend failure — but if Gemini is the one that failed, a search or vision request has nowhere left to go.
- **Fix**: Add a genuine second candidate for both categories (e.g., GPT or Claude for vision if either backend supports image input; Claude for search-adjacent reasoning if no second search-capable backend exists).

### 7. Cross-platform claim doesn't match the implementation — clarify what CI actually exercises
- **Problem**: `COMPUTER_OPERATOR.md` states OS control spans "Windows, Linux, and macOS." Every low-level implementation detail documented anywhere is Windows-only: `Win32Bridge` window handles, `voice/tts.py`'s "Win32 MCI low-latency audio," `native/fnv1a.dll` (a Windows-only extension, no `.so`/`.dylib` mentioned), and every file path in `PROJECT_STRUCTURE.md` using a `d:/BRJARVIS/...` Windows drive letter. `ROADMAP.md` and `fullproject.md` both claim a GitHub Actions matrix across Ubuntu/Windows/macOS.
- **Fix**: Check what the Linux/macOS legs of `.github/workflows/ci.yml` actually run. If they only do import-level smoke tests and skip the OS-automation code paths (`computer/`, `voice/tts.py`, `core/native_bridge.py`), that's fine — but then correct `COMPUTER_OPERATOR.md` to say "Windows-primary, with Linux/macOS import compatibility" rather than implying full parity. If genuine cross-platform automation is wanted, that means adding real conditional code paths (X11/`xdotool` or Wayland for Linux, Quartz/AppleScript or `pyobjc` for macOS, a `.so`/`.dylib` build of the native bridge) — flag this as a real scoping decision for Bharath rather than guessing at it.

### 8. `actions/` and `tools/` overlap with no documented relationship
- **Problem**: `fullproject.md` lists `computer_control`, `computer_settings`, `browser_control`, `file_controller`, and `web_search` as entries in **both** Subsystem 6 (Tool Registry) and Subsystem 9 (Actions Layer, 34 files). `PROJECT_STRUCTURE.md` doesn't document `actions/` at all.
- **Fix**: Confirm whether `tools/` are thin registry wrappers that call into `actions/` implementations (fine, just undocumented), or whether these are two independently-maintained implementations that have drifted (a real bug risk — diff the two for behavioral differences). Document the real relationship in `PROJECT_STRUCTURE.md`, and if they've diverged, consolidate rather than leaving both live.

### 9. Context engine default token budget likely doesn't scale to the real model context windows
- Once Phase 0.5 confirms the real default in `context/engine.py`: if it's genuinely hardcoded near 8192, fix it to scale with the active backend's real context window (128K for Claude/GPT-class, 1M+ for Gemini) rather than a flat low constant that would force unnecessary compression on every request.

### 10. `ui.py` framework — fix whichever doc is wrong, and redo the refactor plan if needed
- Once Phase 0.4 confirms Tkinter vs. PySide: correct the wrong doc. If `TECHNICAL_DEBT.md`'s "modularize into `ui/components/`" recommendation was written assuming the wrong framework, redo it for the real one — Tkinter and PySide have fundamentally different component/widget patterns.

---

## PHASE 3 — MEDIUM (documentation integrity)

### 11. Lesson Store's priority number is almost certainly wrong in two docs
- `FEATURE_MATRIX.md` and `full_repository_audit.md` both state Lesson Store injects at "Priority 6." `CONTEXT_ENGINE.md`'s own scope table is unambiguous: Priority 6 = Clipboard, Priority 5 = Memory. `fullproject.md`'s own Memory Engine table separately confirms Lessons is Memory **Tier 5**. This is very likely a plain typo that should read "Priority 5" in both places — confirm against `context/builder.py`'s actual priority tag and fix both docs to match.

### 12. CHANGELOG.md has an 18-version gap with zero logged entries
- Jumps from v37.6.0 (2026-07-22) straight to v37.25.0 (2026-07-23) — nothing logged for versions 37.7 through 37.24, despite the single 37.25.0 entry summarizing it as covering "Round 24" and "Round 25" of work. Either backfill from real commit history (`git log --oneline`) or stop bumping the minor version per internal "round" without a matching entry — right now the changelog can't function as an audit trail.

### 13. Test-suite accounting doesn't reconcile across docs
- Resolved by Phase 0.1 — once you have the real relationship between the 42/11/5/58 figures, make `ROADMAP.md`, `full_repository_audit.md`, and `fullproject.md`'s Section 7 table all state it the same way.

### 14. Blast-radius tier count — fix whichever doc Phase 0.6 shows is wrong
- 3 tiers (fullproject.md) vs. 4 tiers with CRITICAL (PROJECT_STRUCTURE.md, ARCHITECTURE.md).

### 15. Tool/action/skill counts — replace five different figures with one real one
- Currently in circulation: 93 (`PROJECT_STRUCTURE.md`), 34 (`ARCHITECTURE.md`), "90+" (`PLUGIN_SYSTEM.md`, `FEATURE_MATRIX.md`), 29 (`TECHNICAL_DEBT.md`), "34 tool modules + 21 more actions" (`fullproject.md`). Once Phase 0.3 gives real numbers, state them the same way everywhere — e.g., "31 tool module files exposing 94 registered `@register_tool` functions across `tools/` and `actions/`." Do the same for the unverified "71 Loaded Skills" claim in `PROJECT_STRUCTURE.md`.

### 16. `README.md` points to a file that wasn't included in this audit
- Its "Essential Reading Order" lists `upgrademd/BR_JARVIS_UNIFIED_MASTER_PROMPT.md` as required reading #2, immediately after `fullproject.md`. If this file exists in the real repo, read it before treating this remediation pass as complete — it may already define autonomy/approval policy that resolves Critical #2 above.

### 17. `ROADMAP.md` never tracked four subsystems it now claims are "✅ Production"
- Guardian Core, Self-Upgrade Engine, Multi-Agent, and Reflection/Lesson Store appear in `FEATURE_MATRIX.md` and `full_repository_audit.md` as complete and tested, but none of `ROADMAP.md`'s six phases mention them. Once Phase 0 establishes what's actually real, either add the missing phases retroactively or pull the ✅ Production badge for whichever of the four don't check out.

---

## REPORTING PROTOCOL

- Nothing gets marked done without: the diff, the exact command used to verify it, and the real output pasted in full — not paraphrased, not rounded to "100%."
- "This was already correct" is not exempt from the above — prove it the same way you'd prove a fix.
- Update `CHANGELOG.md` per actual merged change, with a real commit hash, not per "round."
- If a fix genuinely can't be verified without something outside this repo (e.g., a live API key), say so explicitly instead of marking it done.

## HARD CONSTRAINTS

- Don't break any test that Phase 0 confirmed was genuinely passing.
- Don't rename a public method, class, or config key without grepping for and updating every call site.
- If Phase 0.8 (`actions/` vs `tools/`) finds real behavioral divergence, stop and flag it for Bharath rather than guessing which implementation is "correct."
- Work on a feature branch. Given Guardian's integrity baseline is tied to deploy state, don't push straight to `main`.
