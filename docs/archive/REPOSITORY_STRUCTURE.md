# REPOSITORY STRUCTURE & ARCHITECTURE: BR JARVIS MK40.2+

## Architecture Overview
The BR JARVIS repository follows a clean, layered architecture separating core system domain logic, application interfaces, configuration, runtime data, user workspace, and test infrastructure.

```
BR-JARVIS/
├── src/
│   └── brjarvis/
│       ├── core/               # System kernel, DI container, event bus, paths
│       ├── agent/              # Autonomous agent loop, planner, executor, verifier
│       ├── orchestrator/       # Master orchestrator, task coordinator
│       ├── execution/          # Consolidated execution engine & process runner
│       ├── tools/              # Agent tools & dynamic tool registry
│       ├── actions/            # System actions, computer control, document builder
│       ├── connectors/         # External service integrations (Gmail, Calendar, etc.)
│       ├── memory/             # Episodic, semantic, vector, working memory
│       ├── history/            # Session history, execution history, audit logs
│       ├── workflow/           # DAG workflow engine, parallel task graphs
│       ├── tasks/              # Task scheduler, context isolation, state machine
│       ├── security/           # Policy engine, sandbox capabilities, path validator
│       ├── guardian/           # Integrity guardian, tamper detection, redteam
│       ├── router/             # Intent router, model router, gateway
│       ├── career/             # Career OS (Profile, Resume, ATS, Jobs, CRM)
│       ├── browser/            # Playwright automation, browser agent
│       ├── voice/              # Wake word, STT, TTS, VAD, audio bus
│       ├── vision/             # Vision engine, OCR, UI detector, screen streamer
│       ├── ui/                 # Desktop PySide6 UI widgets, canvas renderers
│       ├── desktop/            # Desktop Cyberpunk HUD & Floating Widget
│       ├── skills/             # Skills engine, skill loader, skill library
│       ├── integrations/       # Multi-LLM backends & mobile bridge
│       ├── native/             # C/C++ bindings & low-latency shared libraries
│       ├── diagnostics/        # Doctor, health checks, self-healing repairs
│       └── apps/               # Application controllers (bootstrap, cli, web, desktop, voice)
│
├── apps/                       # Lightweight application launchers
│   ├── cli/main.py
│   ├── web/main.py
│   ├── desktop/main.py
│   └── voice/main.py
│
├── tests/                      # Automated test suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── adversarial/
│   ├── reliability/
│   ├── benchmarks/
│   └── fixtures/
│
├── scripts/                    # Utilities and automation
│   ├── development/
│   ├── build/
│   ├── migration/
│   ├── diagnostics/
│   └── release/
│
├── config/                     # Configuration and schemas
│   ├── default/
│   ├── development/
│   ├── production/
│   ├── examples/
│   └── schemas/
│
├── docs/                       # System documentation
│   ├── architecture/
│   ├── features/
│   ├── operations/
│   ├── security/
│   ├── testing/
│   ├── audits/
│   ├── migrations/
│   └── archive/
│
├── assets/                     # Static media & templates
│   ├── templates/
│   ├── icons/
│   ├── images/
│   └── static/
│
├── runtime/                    # Generated runtime data (Git-ignored)
│   ├── artifacts/
│   ├── logs/
│   ├── captures/
│   ├── reports/
│   ├── temporary/
│   └── state/
│
├── workspace/                  # User workspace data (Git-ignored)
│   ├── documents/
│   ├── resumes/
│   ├── career/
│   ├── projects/
│   └── user-data/
│
├── pyproject.toml              # Modern package discovery & console scripts
├── setup.py                    # Backward-compatible build script
├── pytest.ini                  # Pytest configuration
├── pyrightconfig.json          # Type checking configuration
├── README.md                   # Project documentation
├── LICENSE                     # MIT License
├── .gitignore                  # Exclusion rules
├── start.py                    # Canonical bootstrap launcher shim
├── brjarvis.py                 # Canonical CLI launcher shim
├── main.py                     # Canonical legacy entrypoint
├── server.py                   # Canonical web server shim
├── ui.py                       # Canonical UI shim
└── permissions.py              # Canonical security policy shim
```
