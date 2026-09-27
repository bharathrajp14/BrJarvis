# BR JARVIS — Master Remediation Prompt v2
**For: Antigravity, Gemini 3.5/3.6 Flash (High)**
**Source: direct audit of the live `BrJarvis` repo at commit `cf02ed2` (cloned from `github.com/bharthraj1412/BrJarvis`) — code and test runs, not just docs.**

---

## WHY THIS VERSION EXISTS

Your previous master prompt (`br_archetecture/upgrademd/BR_JARVIS_Master_Fix_Prompt.md`) was already run. Git history shows it landed as commit `d337956` ("Master Remediation Pass") followed by `cf02ed2` ("Voice Upgrades"). That pass **looks** complete on skim — the right function names and doc edits are in the right places. But I cloned the repo, ran the actual test suites, and traced every changed code path, and found that two of the six "fixed" items are **silently non-functional**, and the documentation-reconciliation item was not actually completed. This prompt is not a rerun of the old one — Phase 0 below is already-verified ground truth, not a checklist to redo blindly. Paste this into a new Antigravity task in **Review-driven** mode. Phase 1 is the priority: it fixes things that currently look safe/correct but are not.

---

## ROLE

You are working in the `BrJarvis` repository. Do not trust a prior commit message's claim that something was fixed — including this codebase's own recent "Master Remediation Pass" commit. Verify the actual runtime behavior of any code you touch (does the function that's imported actually exist? is the "dynamic" thing actually called anywhere?) before marking anything done.

---

## PHASE 0 — VERIFIED GROUND TRUTH (already established — re-run only to confirm on your machine)

1. **RedTeam gate is dead code.** `tools/tool_runtime.py` line ~80 does `from tools.redteam_tools import audit_prompt_security`. That name does not exist anywhere in the repo (`grep -rn "def audit_prompt_security" .` returns nothing). Direct repro:
   ```
   python -c "from tools.redteam_tools import audit_prompt_security"
   → ImportError: cannot import name 'audit_prompt_security' from 'tools.redteam_tools'
   ```
   The call site wraps this in `except Exception: pass`, so every tool call silently skips the injection check. **The security gate the last pass claimed to add has never once run.**

2. **"Dynamic" token budget is dead code.** `context/types.py` defines `TokenBudget.from_profile(profile_str)` (Gemini→1,000,000 / Claude·GPT·DeepSeek→128,000 / Ollama·NVIDIA·Mistral→32,000). `grep -rn "from_profile" --include="*.py" .` shows exactly one hit: the definition itself. `ContextEngine` (`context/engine.py`) is constructed once as a global singleton with the static default `TokenBudget()` (128,000 flat) and never calls `from_profile`. **Every backend, including Gemini, is capped at 128K — the per-backend scaling claimed in the commit message doesn't happen.**

3. **Blast-radius tier doc still wrong.** `evolution/classifier.py`'s real `RiskLevel` enum has exactly 3 members: `LOW`, `MEDIUM`, `HIGH` (confirmed, no `CRITICAL`). `br_archetecture/architecture/PROJECT_STRUCTURE.md` line 13 still reads: `classifier.py # Blast-radius ChangeClassifier (LOW, MEDIUM, HIGH, CRITICAL)`. The "complete documentation alignment" commit missed this file.

4. **Test-count reconciliation is still wrong — with different real numbers than anyone has documented.** Actual measurements, this session:
   - `python -m pytest tests/ --collect-only -q` → **58 tests collected** (this already includes everything under `tests/integration/`).
   - `python -m pytest tests/integration --collect-only -q` → **18 tests** (not "11" — `ROADMAP.md`'s claimed integration count is wrong).
   - `grep -c "^def t_" test_deep_audit.py` → **42** (this part of `fullproject.md`'s "42/42" claim is correct) — but it is a **fully separate, non-pytest script**, not folded into the pytest 58 as `fullproject.md`'s banner ("42/42 Deep Audit + Integration Tests Passing") implies.
   - `grep -c "def check_" scripts/smoke_startup.py` → **10** (not "5").
   - Real relationship: **58 (pytest, unit+integration) + 42 (standalone deep-audit script) + 10 (standalone smoke script) = 110 independent checks across three non-overlapping suites.** `ROADMAP.md`'s formula "58 = 42 + 11 + 5" is wrong on every term and wrong about which suites are additive.

5. **CHANGELOG gap still unresolved.** `grep -n "^## \[" br_archetecture/CHANGELOG.md` still jumps straight from `[37.6.0] — 2026-07-22` to `[37.25.0] — 2026-07-23`. Versions 37.7–37.24 are still unlogged.

6. **Real pytest run (this session, Linux container): 56 passed, 2 failed.** Both failures are environment artifacts, not product bugs — traced below, not just asserted:
   - `tests/test_guardian.py::test_path_policy_tiers` hardcodes `d:/BRJARVIS/Br-Jarvis/main.py` and expects `PathTier.TIER_0_WORKSPACE`. `PathPolicy.get_tier()` (`permissions.py`) computes the workspace root as `Path(".").resolve()` at runtime — it will only equal that literal string on the original author's own machine/checkout path. This test has no portability; it will fail in any CI runner or any other clone location, including yours if your working directory differs even slightly.
   - `tests/test_vision_engine.py::test_screen_analyst_capture` fails only when there's no real display and no `mss` package (both true in this sandbox). `ScreenAnalyst.capture_frame()` falls back to empty bytes when both `mss` and `PIL.ImageGrab` fail, giving `frame_hash = 0`, and `is_frame_unchanged()` deliberately treats hash `0` as "capture failed" rather than "unchanged" (`if frame_hash != 0 and ...`). This will pass on your real Windows desktop with `mss` installed; it will always fail headless.

7. **GPT backend identity — now mostly resolved, one small loose end.** `config/models.py` sets the real default to `"gpt": "gpt-oss-120b-medium"`, served via `openai_base_url: http://localhost:8045/v1` (a **local proxy**, not OpenAI's hosted cloud endpoint). `fullproject.md`'s table and `MODEL_ROUTER.md`'s table both correctly say `gpt-oss-120b-medium`. Only `ARCHITECTURE.md`'s diagram label ("GPT-4o / OSS 120B") is still an ambiguous either/or — low priority, cosmetic.

8. **Cross-platform CI claim — confirmed still just import/unit-level.** `.github/workflows/ci.yml`'s `test` job runs the identical `pytest tests/` on `ubuntu-latest`, `windows-latest`, and `macos-latest` — no OS-conditional exercising of `computer/`, `voice/tts.py`, or `core/native_bridge.py`'s actual automation paths. Related: `core/native_bridge.py` correctly branches on `platform.system()` for `jarvis_native.dll` / `libjarvis_native.dylib` / `libjarvis_native.so`, but the repo only has `native/libjarvis_native.so` committed (a Linux build artifact) — `setup_native.py` does compile the right one per-platform at install time, so this isn't a functional bug, just an untracked build artifact worth `.gitignore`-ing so a stale `.so` can't shadow a fresh local build.

Everything above is established. Do not re-litigate it — fix it (Phase 1–2) or confirm-and-fix on your own machine where noted (Phase 3).

---

## PHASE 1 — CRITICAL (the two "fixes" that don't actually run)

### 1. Implement the RedTeam prompt-injection check for real
- **Files**: `tools/redteam_tools.py` (add the function), `tools/tool_runtime.py` (already calls it correctly — leave that call site alone)
- **Problem**: see Phase 0.1. `computer/operator.py`'s clicks/keystrokes are driven partly by `vision/ocr_engine.py` (arbitrary on-screen text) and `vision/dom_bridge.py` (arbitrary DOM content) — both are real indirect prompt-injection surfaces for a computer-use agent, and right now literally nothing screens that content before it can influence a tool call.
- **Fix**: Add `def audit_prompt_security(args: dict) -> str` to `tools/redteam_tools.py`. Input is `{"content": <str>}`. It should pattern-match common injection markers in the content (instruction-override phrases like "ignore previous/all instructions", "disregard the system prompt", fake role markers like `"system:"` or `"### New Instructions"` appearing inside untrusted data, suspicious embedded unicode/zero-width characters used to hide text, and unusually long base64-looking blobs). Return a string containing the literal substring `"INJECTION DETECTED"` plus a short reason when a pattern matches; otherwise return `"CLEAN"` (or similar). Register it as a normal importable function (add `@register_tool` too if you want it independently callable, but the plain function is the minimum `tool_runtime.py` needs).
- **Required proof of fix**: a real unit test in `tests/` that (a) feeds a benign string and asserts no injection is flagged, and (b) feeds a string containing an actual override phrase and asserts `"INJECTION DETECTED"` is returned. Then re-run `python -m pytest tests/ -v` and paste the real pass count — don't just say "added."

### 2. Wire the dynamic token budget to the actual active backend
- **Files**: `context/engine.py`, `context/types.py` (already has `from_profile` — don't rewrite it, call it)
- **Problem**: see Phase 0.2. Gemini's 1M-token window is never used; every backend is stuck at a flat 128K.
- **Fix**: `ContextEngine` needs to know which backend profile is about to serve the request when it builds context — either accept a `profile` argument in `create_builder()` / `assemble_system_context()` and call `TokenBudget.from_profile(profile)` instead of falling back to `self.default_budget`, or have the router pass its currently-selected `AgentProfile` in at call time. Whichever you pick, the acceptance test is concrete: call the context assembly path once with a Gemini profile and once with an Ollama profile, and prove (via `budget.max_tokens` or an equivalent introspectable value) that the two calls actually produce different budgets. A test that only checks `from_profile()` in isolation is not sufficient — it already passes today and the bug is that nothing calls it.

---

## PHASE 2 — HIGH (documentation truth, now with real numbers to state)

### 3. Blast-radius tiers — fix `PROJECT_STRUCTURE.md` line 13
- Change `(LOW, MEDIUM, HIGH, CRITICAL)` to `(LOW, MEDIUM, HIGH)` to match `evolution/classifier.py`'s real `RiskLevel` enum. Grep the rest of `br_archetecture/` for any other stray `CRITICAL` blast-radius mentions before closing this out — Phase 0.3 only checked the one file that still had it, not the whole tree.

### 4. Test-count docs — replace every version of this claim with the real, reconciled numbers from Phase 0.4
- State it identically in `ROADMAP.md`, `full_repository_audit.md`, and `fullproject.md`'s Section 7 table: **58 pytest tests (unit + the 18 in `tests/integration/`) + 42 standalone checks in `test_deep_audit.py` + 10 standalone checks in `scripts/smoke_startup.py` = 110 total, run via three separate commands, not one unified suite.** Don't invent a new single "110" marketing number either — the honest framing is "three suites, three commands, here are the three real counts."

### 5. CHANGELOG gap — backfill or stop bumping ungrouped
- Either reconstruct entries for 37.7.0–37.24.0 from `git log --oneline` (there is real commit history to backfill from — you don't have to guess), or collapse the versioning scheme so a version bump always corresponds to a logged entry going forward. Right now the file cannot function as an audit trail for that range.

### 6. Fix the two non-portable/environment-fragile tests found in Phase 0.6
- `tests/test_guardian.py::test_path_policy_tiers`: stop hardcoding `d:/BRJARVIS/Br-Jarvis/main.py`. Use a path built from the actual resolved workspace root at test time (e.g. `str(Path(".").resolve() / "main.py")`) so the test is machine-independent, and add a second case using a path that's clearly outside the workspace root (e.g. a temp directory) to confirm it correctly falls through to `TIER_1_USER_PROFILE`.
- `tests/test_vision_engine.py::test_screen_analyst_capture`: guard the "second identical capture returns True" assertion behind an actual successful capture (`assume raw_bytes` is non-empty, or `pytest.skip` when no display/mss is available) so CI runners without a display don't get a false failure signal that masks real regressions.

---

## PHASE 3 — AUDIT NEEDED (real code, uncertain-but-plausible bugs — confirm on your actual Windows dev machine, don't guess)

### 7. SAPI5 fallback speaker — confirm cross-thread COM safety
- **File**: `voice/tts.py`
- The new `_init_fallback_speaker()` creates the SAPI5 COM object (`win32com.client.Dispatch("SAPI.SpVoice")`) inside `NeuralTTS.__init__` — i.e., on whichever thread constructs `NeuralTTS`. `_speak_sapi5()` later calls `pythoncom.CoInitialize()` on whatever thread actually invokes `.Speak()`, which may be a different thread (there are `threading.Thread(...)` call sites elsewhere in `tts.py` and `tts_queue.py`).
- **What to check**: instantiate `NeuralTTS` on the main thread, then trigger a `.Speak()` call from the actual worker thread your app uses in production, and confirm there's no `RPC_E_WRONG_THREAD` / disconnected-proxy COM error. `ISpVoice` typically supports standard OLE Automation marshaling so this often works fine in practice — but "often works" isn't the same as verified, and this is exactly the kind of thing that only shows up intermittently on end-user machines. If it does fail cross-thread, either construct `self._sapi_speaker` lazily on first use from the speaking thread itself, or use a dedicated STA thread with its own object lifetime for all SAPI5 calls.

### 8. Downsampling resample — likely periodic artifacts from phase reset
- **File**: `voice/stt.py`, `SounddeviceMicrophone._resample()` / `_callback()`
- The linear-interpolation resampler recomputes `pos = i * ratio` starting from index 0 on every single audio callback, rather than carrying the fractional sample offset over from the end of the previous callback. When `blocksize / ratio` isn't a clean integer for the device's actual native rate (only exactly-3x cases like 48000→16000 with a blocksize divisible by 3 avoid the issue), every callback boundary drops or duplicates a fractional sample, which will surface as small periodic clicks in continuous audio.
- **Fix**: keep a running fractional phase (e.g. `self._resample_phase: float = 0.0`) across calls to `_callback`, so the interpolation continues smoothly instead of resetting each time. Verify with an actual recorded sample at a non-3x-multiple device rate (e.g. 44100→16000, ratio ≈2.756) — that's the case most likely to expose the artifact audibly.

### 9. Housekeeping — don't commit the compiled native binary
- `native/libjarvis_native.so` is a build artifact `setup_native.py` regenerates per-platform at install time. Committing it risks a stale Linux `.so` shadowing a fresh build, or bloating the repo with binaries for every OS over time. Add `native/*.so`, `native/*.dll`, `native/*.dylib` to `.gitignore` and remove the tracked one (`git rm --cached`), keeping only `jarvis_native.c` in version control.

---

## REPORTING PROTOCOL

- Nothing gets marked done without: the diff, the exact command used to verify it, and the real output pasted in full.
- "This was already correct" is not exempt — the whole reason this v2 prompt exists is that the last pass said several things were correct when they weren't. Prove it the same way you'd prove a fix, including for items 3–6 above where the fix is mostly documentation.
- For Phase 1 items 1–2 specifically: a passing test is not sufficient proof by itself — also show the actual call site being exercised (e.g., a log line or assertion that `audit_prompt_security` was invoked and returned a real value, not just that the function exists and importable).
- Update `CHANGELOG.md` per actual merged change with a real commit hash — and don't create a new instance of the Phase 0.5 gap while fixing it.

## HARD CONSTRAINTS

- Don't break any test Phase 0.6 confirmed was genuinely passing (56 of them).
- Don't rename a public method, class, or config key without grepping for and updating every call site.
- Work on a feature branch, not `main` — Guardian's integrity baseline is tied to deploy state.
- If fixing Phase 1.2 (token budget wiring) requires changing `ContextEngine`'s public method signatures, grep every call site of `create_builder` and `assemble_system_context` before changing them — this class is used across the memory/context subsystem, not just in one place.
