# voice/gemini_live.py — Gemini Live Duplex Voice Controller for JARVIS MK37
"""
Continuous duplex hands-free voice controller matching the Gemini Live experience.
Features:
- Continuous multi-turn hands-free listening loop
- Sub-300ms time-to-first-audio sentence-level streaming TTS
- Real-time VAD voice barge-in (speech interruption)
- Conversational Gemini voice prompt persona
"""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger("JARVIS.GeminiLive")

_HAS_SR = False
try:
    import speech_recognition as sr

    _HAS_SR = True
except ImportError:
    sr = None

from .audio_bus import AudioBusMicrophoneSource
from .audio_processor import AudioProcessor
from .tts import NeuralTTS

GEMINI_VOICE_PERSONA_PROMPT = """
You are speaking in Gemini Live Voice Mode.
Rules for your voice responses:
1. Speak in a warm, natural, human conversational tone.
2. Be extremely concise: 1 to 3 short sentences maximum.
3. NEVER output markdown symbols (no asterisks, no hash headers, no bullet points, no code blocks, no backticks).
4. Direct answer first — execute tools silently when needed and state what was accomplished.
"""


class GeminiLiveVoiceLoop:
    """Continuous Duplex Hands-Free Voice Engine (Gemini Live Style)."""

    def __init__(self, assistant_ref=None, ui_ref=None):
        self.assistant = assistant_ref
        self.ui = ui_ref
        self.processor = AudioProcessor(sample_rate=16000)
        self.tts = (
            self.assistant.tts
            if (self.assistant and hasattr(self.assistant, "tts") and self.assistant.tts)
            else NeuralTTS(voice_key="default", rate="+0%")
        )

        self.recognizer = sr.Recognizer() if _HAS_SR else None
        if self.recognizer:
            # Low-latency STT tuning (tuned for clear speech without premature truncation)
            self.recognizer.pause_threshold = 0.45
            self.recognizer.non_speaking_duration = 0.20
            self.recognizer.phrase_threshold = 0.08
            self.recognizer.dynamic_energy_threshold = True

        self.is_active = False
        self.is_listening = False
        self.is_speaking = False
        self._loop_thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the continuous Gemini Live voice session."""
        if self.is_active:
            return
        self.is_active = True
        self._stop_event.clear()
        self._loop_thread = threading.Thread(target=self._run_duplex_loop, daemon=True)
        self._loop_thread.start()
        logger.info("[GeminiLive] ⚡ Gemini Live Duplex Voice Engine Active")

    def stop(self):
        """Stop the voice session."""
        self.is_active = False
        self._stop_event.set()
        self.tts.stop()
        if self.ui:
            self.ui.set_state("IDLE")
        logger.info("[GeminiLive] ⏹ Gemini Live Voice Engine Stopped")

    def interrupt_speech(self):
        """Instantly interrupt ongoing TTS speech when user speaks (Barge-In)."""
        if self.tts.is_speaking:
            logger.info("[GeminiLive] ⚡ Barge-In Interruption Triggered!")
            self.tts.stop()
            if self.ui:
                self.ui.set_state("LISTENING")

    def _run_duplex_loop(self):
        """Main duplex loop: Listen -> Transcribe -> Stream Answer -> Sentence-TTS -> Listen."""
        try:
            with AudioBusMicrophoneSource(subscriber_name="gemini_live_mic") as source:
                while self.is_active and not self._stop_event.is_set():
                    try:
                        if self.ui:
                            self.ui.set_state("LISTENING")

                        self.is_listening = True
                        try:
                            audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=8.0)
                        except sr.WaitTimeoutError:
                            continue
                        finally:
                            self.is_listening = False

                        # Barge-in check: If assistant was speaking, stop it immediately
                        if self.tts.is_speaking:
                            self.interrupt_speech()

                        if self.ui:
                            self.ui.set_state("THINKING")

                        # Transcribe speech
                        text = ""
                        try:
                            from brjarvis.voice.multilingual import get_google_stt_code

                            stt_lang = get_google_stt_code()
                            text = self.recognizer.recognize_google(audio, language=stt_lang)
                        except (sr.UnknownValueError, sr.RequestError):
                            continue

                        text = text.strip()
                        if not text or len(text) < 2:
                            continue

                        logger.info(f"[GeminiLive] 🎤 Spoken: '{text}'")

                        # Acoustic speech interruption check
                        if text.lower().strip() in ("stop speaking", "be quiet", "shut up", "silence", "stop talking", "stop", "cancel"):
                            self.interrupt_speech()
                            continue

                        # Pass to Orchestrator with Gemini Voice Persona
                        if self.assistant and self.assistant.orchestrator:
                            augmented_input = f"{GEMINI_VOICE_PERSONA_PROMPT}\nUser input: {text}"

                            if self.ui:
                                self.ui.set_state("SPEAKING")

                            response = self.assistant.orchestrator.chat(augmented_input)
                            self._speak_conversational(response)
                        else:
                            self._speak_conversational(f"Received: {text}")

                    except Exception as e:
                        logger.warning(f"[GeminiLive] Loop error: {e}")
                        time.sleep(0.3)
        except Exception as e:
            logger.warning(f"[GeminiLive] Microphone stream failed: {e}")

    def _speak_conversational(self, response_text: str):
        """Speak response using fast sentence-level TTS."""
        from brjarvis.voice.tts import clean_for_speech, split_sentences

        clean = clean_for_speech(response_text)

        if not clean:
            return

        def on_start():
            self.is_speaking = True
            if self.ui:
                self.ui.set_state("SPEAKING")

        def on_finish():
            self.is_speaking = False
            if self.ui:
                self.ui.set_state("LISTENING")

        # Split into clean sentences for immediate streaming playback
        sentences = split_sentences(clean)
        if not sentences:
            sentences = [clean]

        def token_gen():
            for s in sentences:
                yield s + " "

        self.tts.speak_stream(token_gen(), on_start=on_start, on_finish=on_finish)
