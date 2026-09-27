# BR JARVIS MK40.2 — Flaky Test Elimination & Stability Policy

## 1. Zero Tolerance for Test Flakiness
A test suite with intermittent failures is considered broken. Tests must produce deterministic outcomes across multiple consecutive executions.

## 2. Forbidden Patterns
- **Arbitrary `time.sleep()`**: Tests must not rely on arbitrary sleep intervals for asynchronous coordination. Use deterministic condition polling (`wait_until(condition, timeout=...)`) or event bus synchronization.
- **Shared Mutable Global State**: Tests modifying singletons or global configuration must restore original state in fixture teardown.
- **Race-Prone Sockets/Ports**: Network tests must use dynamically allocated ephemeral ports (`port 0`) or mocked transports.
- **Real Audio/Microphone Calls in Unit Tests**: Hardware audio streams must be mocked in unit suites (`tests/unit`) and isolated to physical verification suites.

## 3. Quarantining Protocol
1. Any test failing sporadically (< 99.9% pass rate over 50 runs) must be flagged with `@pytest.mark.quarantine`.
2. Quarantined tests do not block master CI gates but generate urgent repair issues.
3. Root cause must be diagnosed (concurrency race, stale state, or timing dependency) and resolved before un-quarantining.
