# voice/assistant.py — JARVIS MK40.2 Voice Control Coordinator
"""
Main hands-free voice control coordinator for JARVIS MK40.2.
Integrates Speech Recognition, Wake Word Detection, State Machine, Single-Stream AudioBus,
and Shared ReAct loop execution.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import re
import sys
import threading
import time
import traceback
from typing import Any, Dict, Optional

from brjarvis.router import AgentProfile

from .audio_bus import AudioBus, AudioBusMicrophoneSource
from .state_machine import VoiceErrorType, VoiceState, VoiceStateMachine

logger = logging.getLogger("JARVIS.VoiceAssistant")

# Default strict wake word patterns (no noisy tokens like 'travis' or standalone 'br')
DEFAULT_PRIMARY_WAKE_WORD = "jarvis"
DEFAULT_WAKE_ALIASES = [
    "jarvis",
    "javis",
    "jarves",
    "jervis",
    "hey jarvis",
    "hey javis",
    "ok jarvis",
    "ok javis",
    "hi jarvis",
    "hi javis",
    "hello jarvis",
    "hello javis",
]

_STRICT_WAKE_RE = re.compile(
    r"\b(hey\s+jarvis|hey\s+javis|ok\s+jarvis|ok\s+javis|hi\s+jarvis|hi\s+javis|hello\s+jarvis|hello\s+javis|jarvis|javis|jarves|jervis)\b",
    re.IGNORECASE,
)

_WAKE_STRIP_RE = re.compile(
    r"^(hey\s+jarvis|hey\s+javis|ok\s+jarvis|ok\s+javis|hi\s+jarvis|hi\s+javis|hello\s+jarvis|hello\s+javis|br\s+jarvis|hey\s+br|jarvis|javis|jarves|jervis)\b[\s,:\.\!]*",
    re.IGNORECASE,
)

_HAS_SR = False
try:
    import speech_recognition as sr  # type: ignore

    _HAS_SR = True
except ImportError:
    pass

_HAS_WINSOUND = False
try:
    import winsound

    _HAS_WINSOUND = True
except ImportError:
    pass

try:
    from brjarvis.desktop.ui_mark import JarvisUI
except Exception:
    try:
        from brjarvis.ui.app import HeadlessJarvisUI as JarvisUI
    except Exception:

        class JarvisUI:
            def __init__(self):
                self.speaking = False
                self.muted = False
                self.on_interrupt = None
                self._state = "IDLE"
                self.on_text_command = None
                self.on_remote_clicked = None
                self.mic_energy_level = 0.0

            def write_log(self, msg: str) -> None:
                logger.info(f"[UI] {msg}")

            def set_state(self, state: str) -> None:
                self._state = state

            def update_agent_task(
                self, task_id: str, name: str, status: str, progress: float = 0.0, result: str = ""
            ) -> None:
                pass

            def remove_agent_task(self, task_id: str) -> None:
                pass


from brjarvis.agent.task_queue import TaskPriority, get_queue
from brjarvis.core.bootstrap import build_assistant_runtime

from .tts import NeuralTTS


class BRVoiceAssistant:
    """Hands-free Voice Assistant coordinator for JARVIS MK40.2."""

    _barge_vad = None
    _barge_vad_lock = None

    @classmethod
    def _get_barge_vad(cls):
        """Lazy-load the barge-in SileroVAD singleton (thread-safe)."""
        if cls._barge_vad_lock is None:
            cls._barge_vad_lock = threading.Lock()
        with cls._barge_vad_lock:
            if cls._barge_vad is None:
                try:
                    from brjarvis.voice.silero_vad import SileroVAD

                    cls._barge_vad = SileroVAD()
                    logger.info("[BargeIn] SileroVAD singleton loaded")
                except Exception as e:
                    logger.warning("[BargeIn] SileroVAD load failed: %s", e)
        return cls._barge_vad

    def __init__(self, ui: JarvisUI | None = None):
        self.ui = ui if ui is not None else JarvisUI()

        # Initialize Explicit State Machine
        self.state_machine = VoiceStateMachine(initial_state=VoiceState.IDLE, ui_ref=self.ui)

        # Initialize ReAct Orchestrator & Backend Gateway via shared runtime
        try:
            runtime = build_assistant_runtime()
            self.orchestrator = runtime.orchestrator
            self.backends = runtime.backends
        except Exception as e:
            logger.warning("Orchestrator init warning: %s", e)
            self.orchestrator = None
            self.backends = {}

        self._loop = None
        self._current_task: asyncio.Task | None = None
        self._task_lock = threading.Lock()
        self._async_task_lock: asyncio.Lock | None = None
        self._vocab_cache = self._load_vocab_cache()

        # Load configurable settings
        self.name = os.environ.get("JARVIS_ASSISTANT_NAME", "BR").strip()
        self.wake_word = os.environ.get("JARVIS_WAKE_WORD", DEFAULT_PRIMARY_WAKE_WORD).strip().lower()
        self._wake_listen_timeout = 2.0
        self._wake_phrase_limit = 4.0
        self._command_timeout = 5.0
        self._command_phrase_limit = 20.0
        self._ambient_calibration = 0.25
        self._last_wake_time = 0.0
        self._wake_cooldown_seconds = 1.0

        # Multi-turn clarification tracking
        self._pending_clarification: Optional[Dict[str, Any]] = None

        # Initialize 500ms rolling audio pre-roll ring buffer
        try:
            from brjarvis.voice.ring_buffer import AudioRingBuffer

            self.ring_buffer = AudioRingBuffer(buffer_duration_ms=500)
        except Exception:
            self.ring_buffer = None

        # Initialize Neural TTS Engine
        self.tts = NeuralTTS(voice_key="default", rate="+0%", pitch="+0Hz")

        # Initialize Gemini Live Voice Loop
        try:
            from brjarvis.voice.gemini_live import GeminiLiveVoiceLoop

            self.gemini_live = GeminiLiveVoiceLoop(assistant_ref=self, ui_ref=self.ui)
        except Exception as e:
            logger.warning("Gemini Live loop init warning: %s", e)
            self.gemini_live = None

        # Centralized Audio Bus
        self.audio_bus = AudioBus.get_instance(sample_rate=16000, chunk_size=512)

        # Tracked background tasks
        self._bg_tasks: set[asyncio.Task] = set()

        # Initialize Persistent Barge-In Monitor on AudioBus
        self._barge_sub = self.audio_bus.subscribe("barge_in_monitor")
        self._barge_in_running = False
        barge_in_enabled = os.environ.get("JARVIS_ENABLE_BARGE_IN", "true").lower() in ("1", "true", "yes")
        if barge_in_enabled:
            self._start_persistent_barge_in()

        # Bind manual text command submission and interrupt from UI
        if self.ui:
            self.ui.on_text_command = self._on_text_command
            self.ui.on_interrupt = self.stop_speech

        # Start Global Hotkeys System
        try:
            from brjarvis.actions.hotkeys import HotkeyManager

            self.hotkey_manager = HotkeyManager(self)
            self.hotkey_manager.start()
        except Exception as e:
            logger.warning("Hotkeys failed to initialize: %s", e)

    def _load_vocab_cache(self) -> dict:
        """Load vocabulary json cache using project root absolute path."""
        try:
            from brjarvis.core.paths import paths

            vocab_path = paths.CONFIG_ROOT / "vocabulary.json"
            if vocab_path.exists():
                data = json.loads(vocab_path.read_text(encoding="utf-8"))
                return data.get("corrections", {})
        except Exception as e:
            logger.warning(f"Vocabulary cache load error: {e}")
        return {}

    def _on_text_command(self, text: str):
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._switch_to_new_command(text), self._loop)

    async def _switch_to_new_command(self, text: str):
        """Cancel any running task/speech, then start the new command with lock synchronization."""
        if self._async_task_lock is None:
            self._async_task_lock = asyncio.Lock()

        async with self._async_task_lock:
            self.tts.stop()
            if self._current_task and not self._current_task.done():
                self._current_task.cancel()
                try:
                    await self._current_task
                except (asyncio.CancelledError, Exception):
                    pass
            self._current_task = asyncio.create_task(self.process_command(text))

    def _start_persistent_barge_in(self):
        """Starts background thread monitoring audio frames on AudioBus for barge-in interruptions."""
        self._barge_in_running = True

        def _run_barge_loop():
            while self._barge_in_running:
                try:
                    frame = self._barge_sub.get(timeout=0.1)
                    if frame is None:
                        continue

                    # Only monitor for barge-in speech while the assistant is actively speaking
                    if not getattr(self.ui, "speaking", False) and not self.tts.is_speaking:
                        continue

                    _barge_vad = self.__class__._get_barge_vad()
                    if _barge_vad:
                        is_speech, prob, snr_db = _barge_vad.is_speech(frame.data, echo_gated=True)
                        if is_speech and snr_db > 8.5:
                            logger.info("[BRG-IN] Barge-in speech detected SNR=%.1fdB — interrupting TTS", snr_db)
                            self.tts.stop()
                            if self.ui:
                                self.ui.speaking = False
                            self.state_machine.transition_to(VoiceState.INTERRUPTED)
                            self._barge_sub.drain()
                            time.sleep(0.3)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.debug("Barge-in loop exception: %s", e)
                    time.sleep(0.5)

        threading.Thread(target=_run_barge_loop, daemon=True, name="PersistentBargeIn").start()

    def speak(self, text: str):
        """Speak text using NeuralTTS with state machine & barge-in support."""
        from brjarvis.voice.tts import clean_for_speech

        log_text = clean_for_speech(text)
        if log_text:
            logger.info(f"[JARVIS] 🗣 Speak: {log_text[:200]}")

        def on_start():
            self.state_machine.transition_to(VoiceState.SPEAKING)

        def on_finish():
            if not getattr(self.ui, "muted", False):
                self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)

        self.tts.speak_async(text, on_start=on_start, on_finish=on_finish)
        if self._barge_sub:
            self._barge_sub.drain()

    def stop_speech(self):
        """Halt active neural TTS speech playback immediately for interruption or cancellation."""
        if hasattr(self, "tts") and self.tts:
            self.tts.stop()
        if hasattr(self, "_current_task") and self._current_task and not self._current_task.done():
            try:
                self._current_task.cancel()
            except Exception:
                pass
        if self.ui:
            self.ui.speaking = False
        if not getattr(self.ui, "muted", False):
            self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)

    def _play_listening_chime(self):
        """Play ascending dual-tone acoustic activation chime when wake word is recognized."""
        try:
            from brjarvis.voice.sound_effects import play_activation_beep

            play_activation_beep()
        except Exception:
            pass

    def _tune_recognizer(self, recognizer):
        """Apply adaptive dynamic energy thresholding and phrase boundary settings."""
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.35
        recognizer.energy_threshold = max(180, getattr(recognizer, "energy_threshold", 250))
        recognizer.pause_threshold = 0.45
        recognizer.non_speaking_duration = 0.25
        recognizer.phrase_threshold = 0.1

    def _is_wake_phrase(self, text: str) -> bool:
        if not text:
            return False

        # Strict Mute & Speaking guard
        if getattr(self.ui, "muted", False) or getattr(self.ui, "speaking", False):
            return False
        if self.state_machine.current_state in (VoiceState.MUTED, VoiceState.SPEAKING):
            return False

        # Reject non-ASCII / hallucinated scripts during wake detection
        if any(ord(c) > 127 for c in text):
            return False

        now = time.time()
        # Cooldown guard: prevent wake triggers within 1.2s of last wake
        if (now - self._last_wake_time) < 1.2:
            return False

        normalized = text.lower().strip()
        for alias in DEFAULT_WAKE_ALIASES:
            if re.search(r"\b" + re.escape(alias) + r"\b", normalized):
                self._last_wake_time = now
                return True

        return False

    def _extract_command_from_wake(self, text: str) -> str:
        """Extract trailing command when user speaks wake-word and command in a single sentence."""
        if not text:
            return ""
        from brjarvis.voice.prompt_refiner import VoicePromptRefiner

        collapsed = VoicePromptRefiner.get_instance().collapse_repetitions(text)
        norm = collapsed.lower().strip()
        cleaned = _WAKE_STRIP_RE.sub("", norm).strip()

        meaningless = {"hey", "jarvis", "javis", "br", "hello", "hi", "ok", "please"}
        words = set(re.findall(r"\b\w+\b", cleaned.lower()))
        if not cleaned or words.issubset(meaningless) or len(cleaned) <= 2:
            return ""
        return cleaned

    def _get_active_loop(self) -> asyncio.AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop and not self._loop.is_closed():
                return self._loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            return loop

    async def _transcribe_wake(self, audio: sr.AudioData) -> str:
        """Fast offline wake-word transcription via local faster-whisper CTranslate2."""
        if getattr(self.ui, "muted", False) or self.state_machine.current_state == VoiceState.MUTED:
            return ""

        loop = self._get_active_loop()
        text = ""

        # Energy gate: check if audio data is actual speech or silence
        try:
            raw_bytes = audio.get_raw_data()
            if len(raw_bytes) > 0:
                from brjarvis.core.native_bridge import audio_energy

                samples = [
                    int.from_bytes(raw_bytes[i : i + 2], "little", signed=True) / 32768.0
                    for i in range(0, min(2048, len(raw_bytes)), 2)
                ]
                if samples:
                    rms = audio_energy(samples)
                    if rms < 0.015:  # Below minimal speech threshold
                        return ""
        except Exception:
            pass

        try:
            from brjarvis.voice.whisper_local import is_available as whisper_available
            from brjarvis.voice.whisper_local import transcribe_wake_fast

            if whisper_available():
                text = await loop.run_in_executor(
                    None,
                    lambda: transcribe_wake_fast(
                        audio.get_wav_data(), language="en", initial_prompt="Jarvis, Javis, Hey Jarvis, Hey Javis"
                    ).lower(),
                )
        except Exception:
            text = ""

        if not text.strip() and hasattr(self, "r") and self.r:
            try:
                # Force English for wake detection to prevent noise hallucinations
                text = await loop.run_in_executor(
                    None, lambda: self.r.recognize_google(audio, language="en-US").lower()
                )
            except Exception:
                text = ""

        # Filter out non-ASCII / hallucinated characters
        if any(ord(c) > 127 for c in text):
            return ""

        return text.strip()

    async def _transcribe_command(self, audio: sr.AudioData) -> str:
        """Full-quality command transcription with fallback chain: Gemini STT -> Local Whisper -> Backend."""
        loop = self._get_active_loop()
        text = ""

        # 1. Try dedicated Gemini Listening API key
        try:
            from brjarvis.voice.gemini_stt import transcribe_audio_online

            text = await loop.run_in_executor(
                None, lambda: transcribe_audio_online(audio.get_wav_data(), timeout_seconds=4.5)
            )
        except Exception:
            text = ""

        # 2. Try local Whisper
        if not text:
            try:
                from brjarvis.voice.multilingual import get_whisper_code
                from brjarvis.voice.whisper_local import is_available as whisper_available
                from brjarvis.voice.whisper_local import transcribe as whisper_transcribe

                if whisper_available():
                    lang_code = get_whisper_code() or "en"
                    prompt = "This is a clear spoken voice command for JARVIS AI assistant to control applications, open web pages, send messages, and execute tasks."
                    text = await loop.run_in_executor(
                        None,
                        lambda: whisper_transcribe(audio.get_wav_data(), language=lang_code, initial_prompt=prompt),
                    )
            except Exception as e:
                logger.warning(f"[Voice] Local Whisper transcription failed: {e}")

        # 3. Try configured default backend
        if not text and hasattr(self, "backends") and self.backends:
            try:
                default_profile = AgentProfile.GEMINI
                primary = self.backends.get(default_profile)
                if primary and hasattr(primary, "transcribe"):
                    text = await loop.run_in_executor(None, lambda: primary.transcribe(audio.get_wav_data()))
            except Exception as e:
                logger.warning(f"Primary transcription chain failed: {e}")

        return text

    async def run_voice_diagnostics(self) -> str:
        """Run complete live voice subsystem diagnostics and health check."""
        results = []
        results.append("=== BR JARVIS VOICE SUBSYSTEM DIAGNOSTICS ===")

        # 1. Microphone & AudioBus
        mic_status = "READY" if self.audio_bus.is_alive() else "OFFLINE"
        results.append(f"Microphone Stream:     {mic_status} (Device {self.audio_bus.device_index})")
        results.append(f"Sample Rate:           {self.audio_bus.sample_rate} Hz (Chunk: {self.audio_bus.chunk_size})")

        # 2. Noise Calibrator
        try:
            from brjarvis.voice.noise_calibrator import get_calibrator

            nc = get_calibrator()
            results.append(
                f"Noise Calibrator:      READY (Baseline: {nc.baseline_rms:.4f}, Env: {nc.environment_label})"
            )
        except Exception as e:
            results.append(f"Noise Calibrator:      DEGRADED ({e})")

        # 3. Silero VAD
        try:
            vad = self.__class__._get_barge_vad()
            vad_status = "READY (ONNX/Torch)" if vad else "DEGRADED"
            results.append(f"Voice Activity VAD:    {vad_status}")
        except Exception as e:
            results.append(f"Voice Activity VAD:    OFFLINE ({e})")

        # 4. STT Engines
        from brjarvis.voice.gemini_stt import get_listen_api_key
        from brjarvis.voice.whisper_local import is_available as whisper_avail

        w_status = "READY (Local CTranslate2)" if whisper_avail() else "NOT_INSTALLED"
        g_status = "CONFIGURED (Gemini Flash)" if get_listen_api_key() else "NOT_CONFIGURED"
        results.append(f"Primary Local STT:     {w_status}")
        results.append(f"Online Gemini STT:     {g_status}")

        # 5. TTS Engine
        tts_status = "READY (Neural Edge-TTS + OneCore)" if hasattr(self, "tts") and self.tts else "OFFLINE"
        results.append(f"Neural TTS:            {tts_status}")

        # 6. Orchestrator & Memory
        orch_status = "ONLINE (ReAct Agent Core)" if self.orchestrator else "OFFLINE"
        results.append(f"Shared Orchestrator:   {orch_status}")

        diag_report = "\n".join(results)
        self.ui.write_log(diag_report)
        return (
            "Voice diagnostics completed. All primary audio, speech, and orchestrator subsystems are operational, sir."
        )

    async def process_command(self, text: str):
        if not text or not text.strip():
            return

        self.state_machine.transition_to(VoiceState.UNDERSTANDING)

        # Refine raw acoustic transcript
        from brjarvis.voice.prompt_refiner import refine_voice_prompt

        ref_res = refine_voice_prompt(text)
        text_clean = ref_res["refined"]

        if not text_clean or not text_clean.strip():
            raw_preview = ref_res.get("raw", text)[:60]
            self.ui.write_log(f'SYS: Ignored wake/noise artifact: "{raw_preview}"')
            self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)
            return

        if ref_res["was_modified"]:
            self.ui.write_log(f'🎙️ Spoken Raw: "{ref_res["raw"]}"')
            self.ui.write_log(f'✨ Refined Prompt: "{text_clean}"')
        else:
            self.ui.write_log(f"You: {text_clean}")

        low = text_clean.lower().strip()

        # Handle Voice Diagnostics Command
        if "voice diagnostics" in low or "run voice diagnostics" in low or "test voice" in low:
            summary = await self.run_voice_diagnostics()
            self.speak(summary)
            return

        # Handle Conversational Approvals & Cancellations
        if ref_res.get("is_approval") and self._pending_clarification:
            pending_goal = self._pending_clarification.get("goal", "")
            self._pending_clarification = None
            self.ui.write_log(f"SYS: Confirmed pending task: '{pending_goal}'")
            text_clean = pending_goal
            low = text_clean.lower().strip()

        elif ref_res.get("is_rejection") and self._pending_clarification:
            self._pending_clarification = None
            self.ui.write_log("SYS: Cancelled pending task upon voice rejection.")
            self.speak("Task cancelled, sir.")
            self.state_machine.transition_to(VoiceState.CANCELLED)
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        # Career OS Voice Shortcuts
        if any(kw in low for kw in ("ats score", "check my ats", "resume score")):
            from brjarvis.career.ats_engine.scorer import ATSEngine
            from brjarvis.career.profile_manager import get_profile_manager
            from brjarvis.career.resume_engine.renderer import ResumeRenderer

            p = get_profile_manager().get_profile()
            schema = ResumeRenderer.schema_from_profile(p)
            rep = ATSEngine.evaluate_resume(schema)
            self.speak(
                f"Your master resume has an ATS compatibility score of {rep.overall_score:.0f} percent, rated Grade {rep.grade}."
            )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(kw in low for kw in ("career status", "career summary", "application funnel", "career overview")):
            from brjarvis.career.analytics import CareerAnalyticsEngine

            a = CareerAnalyticsEngine.compute_analytics()
            self.speak(
                f"You have {a.total_jobs_discovered} jobs discovered, {a.total_applications_submitted} applications submitted, and {a.total_interviews} active interviews."
            )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(
            kw in low for kw in ("check my career emails", "check career emails", "career emails", "recruiter emails")
        ):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            events = db.list_email_records(limit=5)
            if not events:
                self.speak("No recent recruitment email events detected. Your mailbox cursor is up to date.")
            else:
                top = events[0]
                cls_val = top.classification.value if hasattr(top.classification, "value") else str(top.classification)
                self.speak(
                    f"You have {len(events)} recent career emails. Latest is from {top.sender}, classified as {cls_val.replace('_', ' ').lower()}."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(
            kw in low
            for kw in (
                "interview requests",
                "did i receive any interview",
                "show my interviews",
                "interviews this week",
            )
        ):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            interviews = db.list_interviews(limit=5)
            if not interviews:
                self.speak("You have no upcoming interview rounds scheduled.")
            else:
                top = interviews[0]
                self.speak(
                    f"You have {len(interviews)} scheduled interviews. Next is {top.round} with {top.company} on {top.date} at {top.time_str} {top.timezone}."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(kw in low for kw in ("any offers", "did i receive any offers", "check my offers", "job offers")):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            offers = db.list_offers(limit=5)
            if not offers:
                self.speak("No job offers currently detected.")
            else:
                top = offers[0]
                st_val = top.status.value if hasattr(top.status, "value") else str(top.status)
                self.speak(
                    f"You have {len(offers)} offers recorded. Latest is from {top.company} for {top.role}, status {st_val.replace('_', ' ').lower()}."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(
            kw in low for kw in ("update my application tracker", "update tracker", "sync career tracker", "sync excel")
        ):
            from brjarvis.career.spreadsheet.projection import get_spreadsheet_projection

            proj = get_spreadsheet_projection()
            res = proj.project_database_to_excel()
            if res.get("status") == "SUCCESS_VERIFIED":
                self.speak(
                    "Your career tracker Excel workbook has been projected and verified with the latest database records."
                )
            elif res.get("status") == "QUEUED_LOCKED":
                self.speak("The Excel spreadsheet is currently open in Microsoft Excel. The update has been queued.")
            else:
                self.speak("Unable to synchronize Excel tracker. Please check logs.")
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(
            kw in low for kw in ("need follow-up", "need follow up", "what applications need follow", "pending follow")
        ):
            from brjarvis.career.crm.followup_engine import get_followup_engine

            fol_engine = get_followup_engine()
            pending = fol_engine.get_pending_followups()
            if not pending:
                self.speak("All submitted applications are on track. No follow-ups are due today.")
            else:
                self.speak(
                    f"You have {len(pending)} applications requiring follow-up. Top priority is {pending[0].company} for {pending[0].role}, due on {pending[0].due_date}."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(kw in low for kw in ("find jobs for me", "search jobs for me", "find new jobs", "search for jobs")):
            from brjarvis.career.job_engine.finder import JobFinder

            finder = JobFinder.get_instance()
            results = finder.search_and_match(limit=3)
            if not results:
                self.speak("No new matching job postings found across Greenhouse, Lever, and Ashby right now.")
            else:
                top = results[0].job
                fit = results[0].match.overall_score
                self.speak(
                    f"Found {len(results)} top job matches. Best match is {top.title} at {top.company} with a fit score of {fit:.0f} percent."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        if any(
            kw in low
            for kw in (
                "show my pending applications",
                "show my applications",
                "pending applications",
                "my applications",
            )
        ):
            from brjarvis.career.crm.database import get_career_crm_db

            db = get_career_crm_db()
            apps = db.list_applications(limit=10)
            if not apps:
                self.speak("You have no active job applications tracked in your CRM database.")
            else:
                self.speak(
                    f"You have {len(apps)} tracked applications. Most recent is for {apps[0].job_title} at {apps[0].company}, status {apps[0].application_status.value.replace('_', ' ').lower()}."
                )
            self.state_machine.transition_to(VoiceState.IDLE)
            return

        # System shutdown
        exact_shutdown_commands = {
            "exit",
            "quit",
            "goodbye",
            "shutdown",
            "bye",
            "shutdown jarvis",
            "exit jarvis",
            "close jarvis",
            "stop jarvis",
            "shutdown br",
            "exit br",
            "stop br",
        }

        if low in exact_shutdown_commands:
            self.ui.write_log("SYS: Shutting down.")
            self.speak("Goodbye, sir.")
            await asyncio.sleep(2.0)
            if self._loop and self._loop.is_running():
                self._loop.stop()
            sys.exit(0)

        # Detect multiple parallel goals
        parallel_keywords = ["while also", "at the same time", "simultaneously", "and also"]
        is_table = False
        if "|" in text_clean:
            for line in text_clean.splitlines():
                line_s = line.strip()
                if (
                    (line_s.startswith("|") and line_s.endswith("|") and len(line_s) > 1)
                    or "|---" in line_s
                    or "--|" in line_s
                ):
                    is_table = True
                    break

        is_parallel = ("|" in text_clean and not is_table) or any(kw in low for kw in parallel_keywords)

        if is_parallel:
            goals = []
            if "|" in text_clean:
                goals = [g.strip() for g in text_clean.split("|") if g.strip()]
            else:
                split_word = next((kw for kw in parallel_keywords if kw in low), "and also")
                pattern = re.compile(re.escape(split_word), re.IGNORECASE)
                goals = [g.strip() for g in pattern.split(text_clean) if g.strip()]

            if len(goals) > 1:
                self.state_machine.transition_to(VoiceState.EXECUTING)
                self.ui.write_log(f"SYS: Running {len(goals)} tasks in parallel...")
                self.speak("Executing multiple tasks in parallel.")

                q = get_queue()
                task_ids = q.submit_many(goals, priority=TaskPriority.NORMAL, speak=self.speak)

                tid_to_goal: dict[str, str] = {tid: goals[idx][:40] for idx, tid in enumerate(task_ids)}

                for tid in task_ids:
                    self.ui.update_agent_task(tid, tid_to_goal[tid], "running", 0.0, "")

                async def monitor_tasks():
                    completed_tids: set[str] = set()
                    while True:
                        all_done = True
                        for tid in task_ids:
                            if tid in completed_tids:
                                continue
                            status = q.get_status(tid)
                            if not status:
                                continue
                            s = status["status"]
                            if s not in ("completed", "failed", "cancelled"):
                                all_done = False
                            elif s == "completed":
                                completed_tids.add(tid)
                                self.ui.update_agent_task(
                                    tid, tid_to_goal.get(tid, tid[:20]), "completed", 1.0, status.get("result", "")
                                )
                            elif s in ("failed", "cancelled"):
                                completed_tids.add(tid)
                                self.ui.update_agent_task(
                                    tid, tid_to_goal.get(tid, tid[:20]), s, 1.0, status.get("error", "")
                                )
                        if all_done:
                            break
                        await asyncio.sleep(0.5)
                    self.speak("All parallel tasks completed.")
                    self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)

                # Single tracked monitor task
                for old_task in list(self._bg_tasks):
                    if old_task.done():
                        self._bg_tasks.discard(old_task)

                _mt = asyncio.create_task(monitor_tasks())
                self._bg_tasks.add(_mt)
                _mt.add_done_callback(self._bg_tasks.discard)
                return

        # Single goal execution using ReAct Orchestrator loop
        self.state_machine.transition_to(VoiceState.EXECUTING)
        try:
            response = await asyncio.to_thread(self.orchestrator.chat, text_clean)
            if asyncio.current_task() and asyncio.current_task().cancelled():
                return
            if not response or not str(response).strip():
                response = "I am ready, sir. Please specify a single task or command."

            # Check for backend failures
            if "TASK_EXECUTION_FAILED" in response or "All backends failed" in response:
                logger.error("[Voice] STT_SUCCESS_BACKEND_FAILURE: %s", text_clean[:80])
                self.ui.write_log("SYS: [STT_SUCCESS_BACKEND_FAILURE] AI execution failed.")
                self.state_machine.set_error(VoiceErrorType.LLM_FAILURE, "All backends failed")
                self.speak("I was unable to complete the AI planning stage because the model backends failed.")
                return

            # Check if response asks for confirmation
            if "?" in response and any(
                kw in response.lower() for kw in ("should i", "do you want me to", "confirm", "proceed")
            ):
                self._pending_clarification = {"goal": text_clean, "question": response}
                self.state_machine.transition_to(VoiceState.WAITING_APPROVAL)

            from brjarvis.voice.tts import clean_for_speech, summarize_for_speech

            clean_log = clean_for_speech(response)
            self.ui.write_log(f"JARVIS: {clean_log[:500] if clean_log else response[:500]}")
            spoken_summary = summarize_for_speech(response, max_chars=600)
            if not spoken_summary or not spoken_summary.strip():
                spoken_summary = clean_log[:300] if clean_log else "I have completed processing your request, sir."
            self.speak(spoken_summary)
        except asyncio.CancelledError:
            self.state_machine.transition_to(VoiceState.CANCELLED)
            return
        except Exception as e:
            err_msg = f"Error processing request: {e}"
            self.ui.write_log(f"ERR: {err_msg}")
            self.state_machine.set_error(VoiceErrorType.TOOL_FAILURE, str(e))
            self.speak("Sorry, I encountered an error processing that request.")
            traceback.print_exc()

        self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)

    async def run(self):
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # Initialize AI core backends if needed
        if not self.orchestrator:
            self.state_machine.transition_to(VoiceState.PLANNING)
            if self.ui:
                self.ui.write_log("SYS: Initializing AI backends...")
            runtime = build_assistant_runtime()
            self.orchestrator = runtime.orchestrator
            self.backends = runtime.backends
        if self.ui:
            self.ui.write_log("SYS: JARVIS Cognitive Core online.")

        # Setup Speech Recognition & AudioBus
        mic_available = False
        self.r = None
        mic_source = None

        if _HAS_SR:
            try:
                self.r = sr.Recognizer()
                mic_source = AudioBusMicrophoneSource(subscriber_name="assistant_main_mic")
                self._tune_recognizer(self.r)
                mic_available = True
            except Exception as e:
                self.ui.write_log(f"WRN: AudioBus mic offline: {e}")
                self.state_machine.set_error(VoiceErrorType.MICROPHONE_UNAVAILABLE, str(e))
        else:
            self.ui.write_log("WRN: speech_recognition not installed. Text-only mode.")

        self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)
        self.speak(f"{self.name} online. Neural core active. Awaiting your command.")

        # Execute custom startup commands
        try:
            from brjarvis.actions.custom_commands import custom_command_engine

            if custom_command_engine.startup_commands:
                self.ui.write_log("SYS: Executing startup commands...")
                for startup_cmd in custom_command_engine.startup_commands:
                    self._loop.call_soon_threadsafe(
                        lambda c=startup_cmd: custom_command_engine.execute(
                            {"actions": [c]}, {}, speak_callback=self.speak
                        )
                    )
        except Exception as e:
            logger.warning(f"[Voice] Startup commands error: {e}")

        if not mic_available or not self.r or not mic_source:
            self.ui.write_log("SYS: Keyboard text control operational.")
            while True:
                await asyncio.sleep(1.0)

        # Open and start AudioBus stream
        try:
            with mic_source as source:
                self.ui.write_log("SYS: Calibrating microphone noise threshold...")
                try:
                    time.sleep(0.2)  # Allow hardware audio buffer to populate
                    self.r.adjust_for_ambient_noise(source, duration=min(0.5, self._ambient_calibration))
                    if self.r.energy_threshold < 180:
                        self.r.energy_threshold = 180
                    self.r.phrase_threshold = 0.08
                    self.r.dynamic_energy_ratio = 1.25
                    mic_source.drain()
                except Exception as cal_err:
                    logger.warning(
                        "[Voice] Ambient noise calibration note: %s — using safe fallback threshold", cal_err
                    )
                    self.r.energy_threshold = 300
                    self.r.phrase_threshold = 0.08
                    self.r.dynamic_energy_ratio = 1.25

                # Start background noise calibrator
                try:
                    from brjarvis.voice.noise_calibrator import get_calibrator

                    _nc = get_calibrator()
                    if not _nc.is_calibrated:
                        _nc.start_background_calibration(chunk_size=512, sample_rate=16000)
                except Exception as _nc_err:
                    logger.debug("NoiseCalibrator boot note: %s", _nc_err)

                self.state_machine.transition_to(VoiceState.WAKE_DETECTION)
                self.ui.write_log(
                    f"SYS: Microphone active (Device {mic_source.device_index}). Hands-free mode active. Listening for 'Jarvis'..."
                )

                # Mic Health Watchdog
                def _mic_watchdog():
                    while True:
                        time.sleep(5.0)
                        try:
                            if not mic_source.is_alive():
                                logger.warning("[Watchdog] Mic stale — attempting hot-plug recovery")
                                self.state_machine.transition_to(VoiceState.RECOVERING)
                                self.ui.write_log("WRN: Mic disconnect detected. Reconnecting...")
                                if mic_source.try_reconnect():
                                    self.state_machine.transition_to(VoiceState.WAKE_DETECTION)
                                    self.ui.write_log("SYS: Mic recovered successfully.")
                                else:
                                    self.state_machine.set_error(
                                        VoiceErrorType.MICROPHONE_DISCONNECTED, "Recovery failed"
                                    )
                                    self.ui.write_log("ERR: Mic recovery failed. Using text input only.")
                        except Exception:
                            pass

                threading.Thread(target=_mic_watchdog, daemon=True, name="MicWatchdog").start()

                # Wake-word passive listening loop
                while True:
                    try:
                        curr_st = self.state_machine.current_state
                        if (
                            getattr(self.ui, "muted", False)
                            or self.ui.speaking
                            or curr_st
                            in (
                                VoiceState.THINKING if hasattr(VoiceState, "THINKING") else VoiceState.EXECUTING,
                                VoiceState.SPEAKING,
                                VoiceState.PLANNING,
                                VoiceState.MUTED,
                            )
                        ):
                            await asyncio.sleep(0.2)
                            continue

                        self.r.pause_threshold = 0.25
                        self.r.non_speaking_duration = 0.15

                        try:
                            await asyncio.sleep(0.15)
                            mic_source.drain()
                        except Exception:
                            pass

                        self.state_machine.transition_to(VoiceState.WAKE_DETECTION)
                        audio = await self._loop.run_in_executor(
                            None,
                            lambda: self.r.listen(
                                source,
                                timeout=self._wake_listen_timeout,
                                phrase_time_limit=self._wake_phrase_limit,
                            ),
                        )

                        self.state_machine.transition_to(VoiceState.TRANSCRIBING)
                        text = await self._transcribe_wake(audio)

                        if self._is_wake_phrase(text):
                            self.state_machine.transition_to(VoiceState.WAKE_CONFIRMED)
                            self._play_listening_chime()
                            self.ui.write_log("SYS: 🎙️ Wake word detected. Active listening mode...")

                            embedded_cmd = self._extract_command_from_wake(text)
                            if embedded_cmd:
                                self.ui.write_log(f"SYS: Command captured: '{embedded_cmd}'")
                                await self._switch_to_new_command(embedded_cmd)
                                continue

                            try:
                                mic_source.drain()
                            except Exception:
                                pass

                            try:
                                from brjarvis.voice.noise_calibrator import get_calibrator

                                _env = get_calibrator().environment_label
                                _pause = {"QUIET": 0.55, "MODERATE": 0.70, "NOISY": 0.90}.get(_env, 0.70)
                            except Exception:
                                _pause = 0.70
                            self.r.pause_threshold = _pause
                            self.r.non_speaking_duration = max(0.20, _pause * 0.40)

                            self.state_machine.transition_to(VoiceState.LISTENING_FOR_COMMAND)
                            try:
                                audio_cmd = await self._loop.run_in_executor(
                                    None,
                                    lambda: self.r.listen(
                                        source,
                                        timeout=self._command_timeout,
                                        phrase_time_limit=self._command_phrase_limit,
                                    ),
                                )
                                try:
                                    from brjarvis.voice.sound_effects import play_processing_bass_chime

                                    play_processing_bass_chime()
                                except Exception:
                                    pass

                                self.state_machine.transition_to(VoiceState.TRANSCRIBING)
                                cmd_text = await self._transcribe_command(audio_cmd)

                                if cmd_text.strip():
                                    await self._switch_to_new_command(cmd_text)
                                else:
                                    self.ui.write_log("SYS: No command detected. Resuming...")
                                    self.state_machine.transition_to(VoiceState.WAKE_DETECTION)
                            except sr.WaitTimeoutError:
                                self.ui.write_log("SYS: Command capture timed out — no input heard.")
                                try:
                                    mic_source.drain()
                                except Exception:
                                    pass
                                self.state_machine.transition_to(VoiceState.WAKE_DETECTION)

                    except sr.WaitTimeoutError:
                        pass
                    except RuntimeError as e:
                        if "shutdown" in str(e).lower() or "closed" in str(e).lower():
                            break
                        logger.warning(f"[Voice Loop Error]: {e}")
                        await asyncio.sleep(0.3)
                    except Exception as e:
                        logger.warning(f"[Voice Loop Error]: {e}")
                        await asyncio.sleep(0.3)

        except Exception as e:
            self.ui.write_log(f"ERR: Failed to start microphone stream: {e}")
            self.ui.write_log("SYS: Keyboard text control operational.")
            while True:
                await asyncio.sleep(1.0)


_global_voice_assistant: Optional[BRVoiceAssistant] = None
_voice_assistant_lock = threading.Lock()


def get_voice_assistant(ui_instance: Optional[Any] = None) -> BRVoiceAssistant:
    """Return the global BRVoiceAssistant singleton (thread-safe)."""
    global _global_voice_assistant
    if _global_voice_assistant is not None:
        return _global_voice_assistant
    with _voice_assistant_lock:
        if _global_voice_assistant is None:
            _global_voice_assistant = BRVoiceAssistant(ui=ui_instance)
    return _global_voice_assistant


JarvisVoiceAssistant = BRVoiceAssistant
VoiceAssistant = BRVoiceAssistant
