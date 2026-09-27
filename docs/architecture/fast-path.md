# Deterministic Fast-Path Optimization Architecture

## 1. Redefinition of Zero-Token Execution
Previously, "fast-path" was treated as a separate substring matcher that fired on isolated keywords:
$$\text{BAD: } \text{"excel sheet"} \in \text{user\_input} \implies \text{open\_excel}() \rightarrow \text{return}$$

In the new canonical architecture:
**Zero-token execution is a performance optimization INSIDE the canonical runtime, NOT an independent semantic pipeline.**

It is granted **only** when the **COMPLETE** request has been deterministically understood as a single atomic action without remainder:
$$\text{GOOD: } \text{RequestUnderstanding.deterministic\_eligible} = \text{True}$$

## 2. Fast-Path Eligibility Criteria
All of the following conditions must simultaneously hold:
1. **Atomicity**: Request must be strictly `ATOMIC` (exactly 1 actionable operation).
2. **Completeness Score**: Completeness $\ge 0.85$.
3. **No Remaining Text**: Unconsumed text must be empty or purely whitespace/punctuation.
4. **No Sequencers**: Contains no sequencing phrases (`then`, `and then`, `after that`, `next`).
5. **No Conditions**: Contains no conditional keywords (`if`, `unless`, `only if`, `fallback`).
6. **No Negations**: Contains no negation terms (`don't`, `do not`, `never`, `without`).
7. **No Ambiguous Pronouns**: Contains no unresolved referents (`it`, `that`, `this`, `the file`).
8. **No Question / Hypothetical Marker**: Is not an informational question or hypothetical simulation.
9. **Acceptable Risk**: Risk level must be `LOW` or `MEDIUM` (never destructive without explicit confirmation).

## 3. Fast-Path Performance Metrics
- Simple Atomic App Launch (`"open Chrome"`): **< 20ms** latency, **0 LLM tokens**.
- Simple Atomic URL Open (`"open github.com"`): **< 25ms** latency, **0 LLM tokens**.
- Grouped Diagnostic Query (`"show CPU and RAM usage"`): **< 40ms** latency, **0 LLM tokens**.
- Multi-step requests (`"open Excel and show CPU usage"`): Seamlessly decomposed and executed sequentially or planned via the Agent Loop.
