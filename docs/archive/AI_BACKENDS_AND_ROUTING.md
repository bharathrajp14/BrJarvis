# AI Backends and Gateway Routing

Br-Jarvis now includes a small, provider-neutral gateway router in `brjarvis.gateway.routing`. It provides one routing surface over local and hosted AI backends while keeping provider SDKs outside the routing policy. The configuration model follows the useful parts of OmniRoute: one endpoint abstraction, named policies, capability-aware eligibility, transparent fallback, and provider isolation. OmniRouter's public project describes the same broad pattern as a multi-provider pool with one endpoint, automatic fallback, and multiple routing strategies [1]. The academic OmniRouter paper frames routing as a constrained optimization problem that balances quality, cost, and capacity rather than making only a local greedy decision [2].

> **Design choice:** Br-Jarvis keeps the first implementation deterministic and easy to audit. It supports priority, latency, cost, weighted, and round-robin policies, plus capability filtering and per-backend cooldowns. More advanced quota and quality scoring can be added later without changing provider adapters.

## Configuration

Edit [`config/ai_gateway.yaml`](../config/ai_gateway.yaml). Each backend has a stable `id`, provider/model metadata, optional `base_url`, an environment-variable reference for credentials, capability labels, and routing hints. Secrets are never stored in the YAML file.

| Field | Meaning |
|---|---|
| `id` | Stable name used by routes and status output. |
| `provider` / `model` | Human-readable provider and model metadata. |
| `base_url` | Provider or local gateway endpoint. |
| `api_key_env` | Name of the environment variable containing the key. |
| `enabled` | Quickly include or exclude a backend. |
| `priority` | Lower values are preferred by `priority`. |
| `weight` | Relative selection weight for `weighted`. |
| `cost_per_1k_tokens` | Relative cost used by `cost`; local backends can be `0`. |
| `latency_ms` | Baseline latency used by `latency`. |
| `capabilities` | Labels such as `chat`, `code`, `vision`, `tools`, and `agent`. |

A route names a strategy and the eligible backend order. `required_capabilities` prevents a backend from receiving requests it cannot satisfy, and `max_fallbacks` bounds the number of attempts.

## Python usage

```python
from brjarvis.gateway import AIGatewayRouter

router = AIGatewayRouter.from_file("config/ai_gateway.yaml", backend_factory=make_backend)

# Register existing BaseBackend instances, or let make_backend create them lazily.
router.register("local_ollama", ollama_backend)
router.register("proxy_brain", proxy_backend)

response = router.complete(
    messages=[{"role": "user", "content": "Review this function."}],
    policy="coding",
    capability="code",
)
print(response.backend_id, response.model, response.text)
```

`route()` is useful when the caller wants an explainable decision without making a network request. `status()` returns safe operational metadata and excludes credential values.

## Supported policies

| Strategy | Behavior | Best use |
|---|---|---|
| `priority` | Ordered, deterministic selection. | Local-first or explicit primary/fallback chains. |
| `latency` | Lowest configured latency first. | Interactive commands and voice responses. |
| `cost` | Lowest configured token cost first. | Budget-sensitive workloads. |
| `weighted` | Weighted distribution across healthy candidates. | Load spreading across accounts/providers. |
| `round_robin` | Cycles through candidates. | Even distribution when backends are equivalent. |

When a backend raises an exception, it is placed into a short cooldown and the next candidate is attempted. Cooldown is in-memory and intentionally conservative; it does not alter provider credentials or write secrets to disk.

## Using the gateway from the existing AgentRouter

The legacy `AgentRouter` remains backward-compatible, but it can now delegate an individual request to a named gateway policy. This makes rollout gradual and avoids changing existing callers unexpectedly:

```python
from brjarvis.router.core import AgentRouter

router = AgentRouter()
router.enable_gateway()  # loads config/ai_gateway.yaml
answer = router.run(
    "code",
    [{"role": "user", "content": "Review this function."}],
    "",
    routing_policy="coding",
    capability="code",
)
```

If `PrivacyMode.LOCAL_ONLY` is active, the router automatically replaces the requested policy with the explicit `local` policy, which contains only `local_ollama`. The gateway can be inspected with `router.gateway_status()`.

## Connecting existing adapters

The router accepts any object implementing the existing backend contract, including the adapters under `brjarvis.integrations.backends`. A factory can map `BackendConfig.provider` to `OllamaBackend`, `OpenAIBackend`, `GeminiBackend`, or another compatible adapter. This keeps gateway routing configurable without adding provider-specific conditionals to the orchestrator.

## Research references

[1]: https://github.com/diegosouzapw/OmniRoute "OmniRoute GitHub repository"
[2]: https://www.kdd.org/exploration_files/p107_Omnirouter_camera_ready.pdf "OmniRouter: Budget and Performance Controllable Multi-LLM Routing"
