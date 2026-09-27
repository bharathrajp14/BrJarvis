# Provider Verification Matrix

This matrix establishes the verified, ground-truth operational baseline for all primary, native, and external providers integrated into BRJARVIS.

| Provider ID | Provider Type | Base URL / SDK | Default Model | Verified Models | Capabilities | Health State | Free / Local |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`proxy`** | Local Gateway | `http://localhost:8045/v1` | `gemini-3.1-pro-high` | `gemini-3.1-pro-high`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `gemini-3.8-flash-high`, `gemini-3.7-flash-high`, `gemini-3.8-flash-low`, `gemini-3.1-flash-image`, `gpt-oss-120b-medium`, `gemini-2.5-pro` | `chat`, `code`, `reasoning`, `deep_reasoning`, `fast_reasoning`, `vision`, `image_understanding` | `HEALTHY` | Local Proxy |
| **`groq`** | External STT | `https://api.groq.com/openai/v1` | `whisper-large-v3-turbo` | `whisper-large-v3-turbo`, `whisper-large-v3` | `speech_to_text`, `stt`, `transcription` | `HEALTHY` | Cloud (Free Quota) |
| **`gemini_audio`**| External Native | Google AI Studio (`google-genai`) | `gemini-3.8-flash-lite-tts` | `gemini-3.8-flash-lite-tts`, `gemini-3.8-flash-tts`, `gemini-3.8-live` | `text_to_speech`, `tts`, `voice`, `audio`, `realtime_voice` | `HEALTHY` | Cloud |
| **`pollinations`** | External Media | `https://gen.pollinations.ai` | `tongyi-mai/z-image-turbo` | `tongyi-mai/z-image-turbo`, `black-forest-labs/flux.1.1-pro`, `flux` | `image_generation`, `image`, `media_generation` | `HEALTHY` | Cloud |
| **`openrouter`** | External Fallback | `https://openrouter.ai/api/v1` | `openrouter/free` | `openrouter/free`, dynamically discovered `:free` models | `chat`, `code`, `reasoning`, `vision`, `image_understanding`, `general_free_fallback` | `HEALTHY` | Free Tier |
| **`elevenlabs`** | External Premium | `https://api.elevenlabs.io/v1` | `eleven_turbo_v2_5` | `eleven_turbo_v2_5`, `eleven_multilingual_v2` | `text_to_speech`, `tts` | `AUTH_FAILED` / `UNAVAILABLE` (Key Restricted) | Premium |

## Architectural Separation of Concerns
BRJARVIS strictly separates:
- **Provider**: The infrastructure execution backend (`proxy`, `groq`, `gemini_audio`, `pollinations`, `openrouter`, `elevenlabs`).
- **Model**: The specific model weights addressed (`gemini-3.1-pro-high`, `claude-sonnet-4-6`, `whisper-large-v3-turbo`, etc.).
- **Capability**: The functional contract required by the task (`TEXT_REASONING`, `CODE`, `DEEP_REASONING`, `FAST_REASONING`, `VISION`, `SPEECH_TO_TEXT`, `TEXT_TO_SPEECH`, `REALTIME_VOICE`, `IMAGE_GENERATION`, `GENERAL_FREE_FALLBACK`).
