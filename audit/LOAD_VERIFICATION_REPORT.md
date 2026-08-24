# BRJARVIS WebSocket and Store-Hydration Load Verification
## Scope and method
The test uses isolated in-process fakes, not production services. WebSocket runs exercised 1, 10, 50, and 100 clients; 20–50 sequential broadcasts; zero and 10 ms client send delays; and a 100-client case with 50 ms delay and 10% failing clients. The hydration harness imports the updated TypeScript API client, mocks HTTP responses, measures the nine parallel panel requests, tests 0–500 projects, 0/5/20 ms response delays, one panel outage, and 20 concurrent snapshots.
## Results
| Path | Measurement | Result |
|---|---|---|
| WebSocket `broadcast_log` | Max clients / max global send overlap | 100 / 100 |
| WebSocket `broadcast_log` | Delivery integrity | PASS |
| WebSocket `broadcast_log` | Max per-event p50 across cases | 64.486 ms |
| WebSocket `broadcast_ws_event` | Max clients / max global send overlap | 100 / 100 |
| WebSocket `broadcast_ws_event` | Delivery integrity | PASS |
| WebSocket `broadcast_ws_event` | Max per-event p50 across cases | 62.342 ms |
| Store hydration | Requests per snapshot | [9] |
| Store hydration | Peak parallel fetches per snapshot | [9] |
| Store hydration | Worst sampled p95 | 42.214 ms |
| Store hydration | Request count independent of project count | PASS |

## Detailed Measurements

| Scenario | `broadcast_log` | `broadcast_ws_event` |
|---|---:|---:|
| 100 clients, 50 events, zero-delay fake clients | 1.339 ms/event p50; 5,000/5,000 delivered | 0.912 ms/event p50; 5,000/5,000 delivered |
| 100 clients, 20 events, 10 ms fake send delay | 18.522 ms/event p50; 2,000/2,000 delivered | 15.793 ms/event p50; 2,000/2,000 delivered |
| 100 clients, 20 events, 50 ms delay, 10% failures | 64.486 ms/event p50; 1,800/1,800 successful sends | 62.342 ms/event p50; 1,800/1,800 successful sends |
| 20 concurrent hydration snapshots, 100 projects, 5 ms response delay | 38.933 ms total wall time | 20 snapshots × 9 requests; no project-dependent request growth |

For hydration, the request count was exactly **9** and peak per-snapshot fetch concurrency exactly **9** for all 12 combinations of 0, 10, 100, and 500 projects with 0, 5, and 20 ms mocked response delays. The sampled p95 values were 42.214 ms, 15.462 ms, and 31.017 ms for the 0-project cases at 0, 5, and 20 ms delay respectively; at 500 projects they were 18.451 ms, 17.490 ms, and 33.887 ms. The 42.214 ms value is a cold-start/outlier sample, not a project-size trend.

## Interpretation

The updated WebSocket implementation achieves true per-event fan-out: with 100 clients and a 10 ms fake send delay, global in-flight sends reach 100 while each fake client has only one send in flight. Sequential broadcast calls preserve delivery integrity, and failing clients do not prevent successful clients from receiving their events. The 0.5-second per-client timeout was not reached by the tested 50 ms case.
The hydration change removes the project-count-dependent HTTP fan-out: every sampled snapshot made exactly nine requests whether the server returned 0, 10, 100, or 500 projects. The request layer remained nine-way concurrent. Under the mocked 20 ms response delay, the worst sampled p95 was reported in the JSON artifact; the 20-snapshot concurrent case is also recorded there.
The failure case confirms that a failed artifacts panel is reported as `error` with a user-safe message while the overall connection remains `connected` when health succeeds. This is the intended degraded-state behavior, although the UI still needs to render the optional `panelHealth` map with visible retry controls.

## Regression Verification

The post-load regression suite completed with **361 passed and 1 skipped in 38.34 seconds**. The frontend TypeScript and Vite production build also passed, producing a 252.98 kB JavaScript bundle and 76.68 kB gzip size. A chart script was prepared but could not run because the attached project virtual environment does not contain Matplotlib; the raw JSON results and Markdown tables are the authoritative artifacts.

## Limitations and next tests
These are deterministic application-level load tests, not a network-level soak test. They do not measure browser rendering, TLS, proxy buffering, kernel socket limits, real database latency, provider latency, multiple worker processes, or memory growth over hours. Before release, run a staging soak with real WebSockets, a bounded per-client queue, reverse proxy, multiple workers, and memory/CPU telemetry. The current implementation bounds each broadcast send wait but still creates one awaitable per target; a queue-based sender remains the next scalability step for sustained high-volume logs.
