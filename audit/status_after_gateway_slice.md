# BrJarvis Rebuild Status — Gateway Slice

**Date:** 2026-08-28  
**Working tree:** `main`, one commit ahead of `origin/main`; changes remain uncommitted.

## Completed in this slice

The rebuild now has a canonical `src/jarvis/gateway/` package. It defines provider-neutral `ModelRequest` and `ModelResponse` contracts, a `ProviderAdapter` protocol, typed gateway errors, capability-aware routing, circuit-breaker state, and the single `ModelGateway.generate()` / `ModelGateway.stream()` entrypoints.

The adapter boundary includes a reusable OpenAI-compatible adapter plus canonical Claude, Gemini, and Ollama adapter modules. Provider SDK construction remains inside the gateway adapter package. The current `config/models.yaml` catalogue can be loaded through `build_configured_gateway()`, preserving its fallback hierarchy and capability mappings as logical model adapters behind the existing proxy.

The new gateway is registered by the `jarvis.core.bootstrap.AssistantRuntime` composition root. The core doctor now confirms `ModelGateway` registration and reports the configured logical providers without exposing credentials.

The legacy `src/brjarvis/gateway/`, `src/brjarvis/router/`, and `src/brjarvis/integrations/backends/` packages are intentionally still present. They will be removed only after downstream consumers are migrated and the replacement passes the full cutover gates.

## Verification

| Check | Result |
|---|---|
| Gateway unit and contract tests | **6 passed** |
| Core + gateway focused tests | **12 passed** |
| Full regression suite | **373 passed, 1 skipped** |
| New core + gateway Ruff checks | Passed |
| New core + gateway Pyright checks | **0 errors, 0 warnings** |
| Gateway compilation | Passed through focused test/import execution |
| `python start.py core-doctor` | Healthy; gateway registered as `ModelGateway` |

## Next recommended work

The next step is to migrate the first gateway consumer, preferably the orchestrator or CLI request path, behind `AssistantRuntime.gateway`. Add compatibility translation for legacy backend callers, then run end-to-end request tests before deleting any legacy router or backend module.
