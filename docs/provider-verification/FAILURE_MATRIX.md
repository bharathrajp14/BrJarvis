# Provider Failure & Fault Recovery Matrix

This document maps all observed, simulated, and handled failure modes across the BRJARVIS multi-provider runtime.

## Failure Mode Taxonomy & Operational Responses

| Failure Mode | HTTP / Exception Pattern | Detected State | Gateway Action | State Transition |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication Failure** | HTTP 401, 403, `invalid_api_key`, `unauthorized` | `AUTH_FAILED` | Immediate isolation; 24h cooldown; skip provider without retry storms | `* -> AUTH_FAILED` |
| **Rate Limit / Quota Exceeded** | HTTP 429, `rate limit`, `too many requests` | `RATE_LIMITED` | Read `Retry-After` or `x-ratelimit-reset`; engage exponential cooldown; attempt fallback | `* -> RATE_LIMITED` |
| **Provider Timeout** | `TimeoutError`, `httpx.TimeoutException` | `DEGRADED` | Retry with backoff; record consecutive timeouts; if threshold exceeded, trip circuit | `HEALTHY -> DEGRADED` |
| **Connection Refused / Down** | `ConnectionRefusedError`, `getaddrinfo failed` | `OFFLINE` | Immediate failover to next eligible candidate in fallback hierarchy | `* -> OFFLINE` |
| **Server Error** | HTTP 500, 502, 503, 504 | `OPEN_CIRCUIT` | Record consecutive failures; trip breaker after 4 failures; cooldown before probe | `DEGRADED -> OPEN_CIRCUIT` |
| **Mid-Stream Failure** | Socket drop during text or audio chunk streaming | Fail Fast | Terminate stream with `GatewayError`; do not emit garbled or partial duplicate tokens | Error Emitted |

## Verified Fault Injection Scenarios

1. **Proxy 503 Outage**: Simulated via `gateway.inject_fault("proxy", ...)`. Verified clean fallback to OpenRouter in 3.86s.
2. **Groq STT Timeout**: Verified failover to Gemini Audio or truthful error emission without crash.
3. **Gemini TTS Down**: Verified mid-task failure isolation while preserving `task_id`, `run_id`, memory ledger, and generated artifacts.
4. **All Providers Exhausted**: Verified terminal `GatewayError` reporting exact attempt depth without infinite loop.
