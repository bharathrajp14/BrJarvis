# Provider Fallback Matrix

This document defines the deterministic fallback chains, modality compatibility rules, and cascading failure protections implemented in the BRJARVIS gateway.

## Capability Fallback Chains

| Capability | Primary Provider / Model | Fallback Tier 1 | Fallback Tier 2 | Terminal Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **`TEXT_REASONING`** | `proxy` (`gemini-3.1-pro-high`) | `openrouter` (`openrouter/free`) | — | `GatewayError` (truthful failure) |
| **`CODE`** | `proxy` (`claude-sonnet-4-6`) | `openrouter` (`openrouter/free`) | — | `GatewayError` (truthful failure) |
| **`DEEP_REASONING`** | `proxy` (`claude-opus-4-6-thinking`) | `proxy` (`gemini-3.1-pro-high`) | — | `GatewayError` |
| **`FAST_REASONING`** | `proxy` (`gemini-3.8-flash-low`) | `openrouter` (`openrouter/free`) | — | `GatewayError` |
| **`VISION`** | `proxy` (`gemini-3.1-flash-image`) | `openrouter` (`openrouter/free`) | — | `GatewayError` |
| **`SPEECH_TO_TEXT`** | `groq` (`whisper-large-v3-turbo`) | `gemini_audio` | — | `GatewayError` |
| **`TEXT_TO_SPEECH`** | `gemini_audio` (`gemini-3.8-flash-lite-tts`) | `elevenlabs` (`eleven_turbo_v2_5`) | — | `GatewayError` |
| **`IMAGE_GENERATION`** | `pollinations` (`tongyi-mai/z-image-turbo`) | `pollinations` (`black-forest-labs/flux.1.1-pro`) | — | `GatewayError` |
| **`GENERAL_FREE_FALLBACK`** | `openrouter` (`openrouter/free`) | — | — | `NoRouteAvailableError` |

## Modality Compatibility Enforcement
The gateway strictly prevents cross-modality fallback:
- `IMAGE_GENERATION` requests **never** fall back to text models (e.g. OpenRouter).
- `SPEECH_TO_TEXT` requests **never** fall back to text reasoning models.
- Audio modalities require binary audio input/output adapters.

## Cascading Failure Protection & Circuit Braking
1. **Per-Invocation Visited Tracking**: Visited providers are recorded in `visited_providers: set[str]`. A failed provider is **never** retried during the same invocation cascade (preventing $A \to B \to A$ infinite loops).
2. **Maximum Fallback Depth**: Hard-capped at `max_fallback_depth = 3`.
3. **State Machine Circuit Breaker**:
   - `OPEN_CIRCUIT` trips after 4 consecutive failures.
   - 30-second exponential backoff cooldown.
   - Transition to `HALF_OPEN` enables single-probe trial before full restoration to `HEALTHY`.
