# BRJARVIS Control Plane UI

This directory contains the rebuilt React/TypeScript/Vite web UI for BRJARVIS. It is designed as a static frontend served by the existing FastAPI application.

## Commands

Run `pnpm install` once, then use `pnpm dev` for local development. The Vite dev server proxies `/api` and `/ws` to the local FastAPI server. Run `pnpm typecheck` for strict TypeScript validation. Run `pnpm build` to create a production bundle in `frontend/dist`. Run `pnpm build:static` to build and copy that bundle to `src/brjarvis/web/static/dist`, which is served by FastAPI.

The rebuilt interface is exposed safely at `/web/rebuild` and `/web/control-plane` while the legacy `/web` entry remains available for rollback during migration.

## Architecture

The UI is organized around a typed platform layer, explicit application state projections, a replay-aware realtime client, shared accessible components, and feature surfaces for command center, tasks, approvals, workspace, artifacts, memory, Career OS, integrations, and operations. The backend remains authoritative for identity, authorization, task state, approvals, execution, persistence, and provider decisions.

The client now attempts the existing BRJARVIS task, artifact, health, and connector routes by default and falls back to deterministic local data when a route is unavailable or authentication is not present. Set `VITE_DEMO_MODE=true` for an explicit frontend-only demo. Set `VITE_API_BASE_URL` when the API is served from a different origin.
