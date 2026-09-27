# BRJARVIS Control Plane UI

The control plane is a React, TypeScript, and Vite application served as packaged static content by the BRJARVIS FastAPI server. It uses the backend as the authority for authentication, tasks, approvals, projects, files, artifacts, memory, contacts, Career OS, connectors, notifications, and runtime health. It does not fabricate fallback records.

## Development

```bash
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend typecheck
pnpm --dir frontend build:static
```

For local frontend development, run `pnpm --dir frontend dev`. Vite proxies `/api` and `/ws` to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` when the API uses another origin; REST, authentication, and WebSocket clients share that base.

`build:static` runs the production TypeScript/Vite build and copies `frontend/dist` into `src/brjarvis/web/static/dist`. The copied bundle is intentionally tracked because package builds do not run Node and the FastAPI wheel must contain a ready-to-serve UI.

## Product surfaces

- **Command** — create durable agent tasks and import files into persistent knowledge.
- **Tasks** — filter tasks and inspect authoritative phases, progress, steps, provider routing, and linked output.
- **Approvals** — approve or reject pending protected actions.
- **Workspace** — create/delete projects, upload files, and preview persisted text files.
- **Artifacts** — preview, verify, and download generated artifacts.
- **Memory** — create, search, and delete scoped persistent memories.
- **Career OS** — review profile readiness, search jobs, and generate an ATS resume.
- **Relationships** — create, prioritize, and remove contacts while monitoring project delivery.
- **Integrations** — inspect tools, save credentials to the server vault, and test connectors.
- **Operations** — distinguish REST health from realtime health, inspect readiness, and manage notifications.

## Interaction and security model

The app creates an HttpOnly browser session from the configured server API key. Credentials are never written to browser storage. Destructive operations retain explicit confirmation or backend approval gates. Snapshot refreshes preserve navigation and the selected task, while WebSocket cleanup stops heartbeats and reconnection after an intentional disconnect.

Navigation is hash-addressable (`#/tasks`, `#/workspace`, and so on), keyboard accessible, and responsive from desktop to narrow mobile layouts. `Ctrl+K` opens live global search. The interface includes complete light/dark tokens, visible focus treatment, truthful empty/error states, accessible progress/status semantics, and reduced-motion support.
