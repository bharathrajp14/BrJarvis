# BR JARVIS — HEALTH CHECKS & TELEMETRY SPECIFICATION

## 1. Health Endpoints (`/api/v1/health/...`)

- **`/health/live`**: Liveness probe returning `200 OK` if process event loop is active.
- **`/health/ready`**: Readiness probe checking database connectivity and core service initialization.
- **`/health/components`**: Deep diagnostic returning status of all 12 core subsystems:
  - Permissions & Security Policy
  - Artifact Manager & Export Storage
  - Action Verifier & Browser Engine
  - Sandbox Process Execution Engine
  - Router & Multi-LLM Gateway
  - Skills & Tools Registry
  - SQLite WAL Database Store
  - Audio & Voice Engine
  - Vision & Screen Capture
  - UI Signal Bridge
