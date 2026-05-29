# FinalPlanner

Frontend-only private planner built with Next.js App Router.

## Shape

This repo now follows the same structure as the standalone planner folder:

```text
app source: src/app
shared UI: src/components
local planner engine: src/lib/api.ts
static assets: public
deployment: Vercel
```

There is no FastAPI backend, Celery worker, Railway config, database migration, or planner reset path in this version. Pages use local static planner data and browser `localStorage` for session/progress.

## Local Development

```bash
npm ci
npm run dev
```

## Build

```bash
npm run build
```

## Deployment

Vercel builds from the repository root:

```json
{
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

## Planner Lock

The local planner engine keeps the June 1 lock:

- No daily tasks before `2026-06-01`
- `/dashboard/realtime` local data returns waiting/locked state before start
- `/daily-plan` local data returns an empty list before start
- Planner window verification remains valid in local data
