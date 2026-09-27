"""Provider adapters; provider SDK imports remain inside this package."""

from .base import BaseAdapter, InMemoryAdapter
from .claude import ClaudeAdapter
from .elevenlabs import ElevenLabsAdapter
from .gemini import GeminiAdapter
from .gemini_audio import AudioSynthesisResult, GeminiAudioAdapter
from .groq_stt import GroqSTTAdapter
from .ollama import OllamaAdapter
from .openai import OpenAIAdapter
from .openrouter import OpenRouterAdapter
from .pollinations import ImageArtifact, PollinationsAdapter

__all__ = [
    "BaseAdapter",
    "InMemoryAdapter",
    "OpenAIAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "OllamaAdapter",
    "GroqSTTAdapter",
    "GeminiAudioAdapter",
    "AudioSynthesisResult",
    "PollinationsAdapter",
    "ImageArtifact",
    "OpenRouterAdapter",
    "ElevenLabsAdapter",
]
