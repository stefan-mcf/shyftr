# ShyftR React Console

Status: local developer-preview console for inspecting and reviewing local Cells. It is not a hosted dashboard.

## Setup

```bash
cd apps/console
cp .env.example .env
npm install
npm run dev
npm run build
npm audit --omit=dev
```

The Vite dev server binds to `127.0.0.1` by default. The console expects the local ShyftR service from `docs/api.md`.

## Environment

`apps/console/.env.example` documents the local API base URL. Keep real `.env` files untracked.

## Current console capabilities

The current console code and `src/shyftr/console_api.py` support local Cell summaries, Spark review queues, Charge exploration, proposal decisions, Pack/Signal flows, hygiene/diagnostics, pilot metrics, operator-burden views, and policy-tuning projections. Mutating UI paths delegate to existing Regulator/ledger functions; the console is not an independent truth store.

## Boundaries

- Use synthetic or operator-approved local Cells.
- Do not commit screenshots unless they are scrubbed and intentionally added.
- Do not imply cloud hosting or multi-tenant operation from this console.
