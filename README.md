# FinalPlanner Monk Mode Life OS

Private production-grade discipline enforcement platform for exam preparation, backend engineering, LLM / Agentic AI learning, gym, sleep, anti-distraction tracking, warnings, recovery mode, travel mode, analytics, notifications, and Resend email accountability.

## Stack

- Frontend: Next.js 14 App Router, TypeScript, TailwindCSS, shadcn-style UI primitives, Zustand, React Query, Framer Motion, PWA support
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Alembic, Celery, Redis
- Life OS data store: MySQL via `mysql+pymysql` for exams, syllabus, generated daily tasks, calendar events, travel mode, and productivity logs
- Auth: JWT
- Email: Resend
- Monitoring: Sentry and structured logging hooks
- Deployment: Vercel frontend, Railway backend, Supabase PostgreSQL, Upstash Redis

## Repository Structure

```text
frontend/
backend/
infra/
docs/
.github/workflows/
docker-compose.yml
.env.example
README.md
```

## Monk Mode Rules

- Daily minimum score: 70.
- Weekly minimum score: 75.
- Backend and LLM blocks are non-negotiable.
- Gym is mandatory Monday-Friday.
- One travel break only, maximum 14 continuous days.
- Social media and entertainment are penalty minutes.
- Two consecutive critical days activate recovery mode.
- Weekly score below 70 marks correction planning.
- No mock test in 14 days is RED.
- Sleep below 6 hours for 3 days is RED.

## Discipline Score

The backend calculates a daily score out of 100:

- Backend block completed: 20
- LLM / Agentic AI block completed: 20
- Exam foundation completed: 15
- Specialized exam block completed: 15
- Revision and journal completed: 10
- Gym completed: 10
- Sleep target met: 5
- No distraction penalty: 5

Statuses:

- 85+: Elite
- 70-84: On Track
- 50-69: Warning
- Below 50: Critical

## Local Setup

```bash
cp .env.example .env
docker compose up -d db redis
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Celery:

```bash
cd backend
celery -A app.tasks worker --loglevel=INFO
celery -A app.tasks beat --loglevel=INFO
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

## Email Setup

Create a Resend API key and configure:

```bash
EMAIL_FROM=FinalPlanner <alerts@your-domain.com>
EMAIL_TO=skpersonal04@gmail.com
RESEND_API_KEY=re_...
```

Daily missed-task email runs at 11:30 PM. Weekly summary runs Sunday at 9 PM.

## Core Backend APIs

- `POST /auth/register`
- `POST /auth/login`
- `GET /dashboard`
- `GET /daily-plan?date=YYYY-MM-DD`
- `PATCH /tasks/{id}/complete`
- `GET /monk-mode/daily-score`
- `GET /monk-mode/recovery-plan`
- `GET /weekly-review`
- `POST /sleep/log`
- `POST /distractions/log`
- `GET /notifications`
- `POST /email/daily-alert`
- `POST /email/weekly-summary`
- `GET /warnings`
- `POST /warnings/generate`
- `GET /analytics`

## Deployment

Frontend:

1. Import the GitHub repo in Vercel.
2. Keep the Vercel root directory at the repository root so root `vercel.json` can run `cd frontend && npm ci && npm run build`.
3. Set `NEXT_PUBLIC_API_BASE_URL`.
4. Push to `main`; Vercel auto-deploys.
5. Configure `NEXT_PUBLIC_SENTRY_DSN` after creating the Sentry frontend project.

Backend:

1. Create a Railway project connected to the GitHub repository.
2. Add one Railway service for the FastAPI web backend using root `railway.json`.
3. Add a second Railway service for the Celery worker and set its Railway config to `infra/railway-worker.json`.
4. Add a third Railway service for Celery beat and set its Railway config to `infra/railway-beat.json`.
5. Set `DATABASE_URL`, `DIRECT_URL`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, and `SENTRY_DSN`.
6. Use Supabase/Railway PostgreSQL and Upstash Redis.
7. Set `LIFE_OS_DATABASE_URL` to the same PostgreSQL database, or to a second PostgreSQL database if you want the planner tables isolated.
8. Run Life OS PostgreSQL migrations with `alembic -c life_os_alembic.ini upgrade head`.
9. Railway auto-deploys on GitHub push.
10. Health check path is `/health`.
11. The web service runs legacy `alembic upgrade head` before Gunicorn/Uvicorn; add `alembic -c life_os_alembic.ini upgrade head` when `LIFE_OS_DATABASE_URL` is configured.
12. Optional production seed is controlled by `RUN_PRODUCTION_SEED`, `PRODUCTION_SEED_EMAIL`, and `PRODUCTION_SEED_PASSWORD`.

CI/CD:

- `.github/workflows/ci.yml` builds frontend and compiles backend.
- `.github/workflows/backend-cron.yml` can trigger an external cron URL if you prefer GitHub Actions scheduling.
- `.github/workflows/railway-smoke.yml` verifies production frontend and backend URLs after secrets are configured.

Required hosted secrets:

- Vercel: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SENTRY_DSN`
- Railway/Render: `DATABASE_URL`, `DIRECT_URL`, `LIFE_OS_DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `SENTRY_DSN`
- GitHub Actions: `BACKEND_URL`, `FRONTEND_URL`, optional `BACKEND_CRON_URL`

Railway GitHub auto-deploy:

1. In Railway, create a new project from the GitHub repo.
2. Select branch `main`.
3. Enable automatic deploys for the web service.
4. Create separate worker and beat services from the same repo, using `infra/railway-worker.json` and `infra/railway-beat.json`.
5. Railway will deploy on each push to `main`; no CLI deployment is required.

Deployment verification scripts:

```bash
scripts/verify-railway-env.sh .env.railway.example
BACKEND_URL=https://your-backend.up.railway.app FRONTEND_URL=https://your-app.vercel.app scripts/verify-production-smoke.sh
AUTH_TOKEN=<jwt> BACKEND_URL=https://your-backend.up.railway.app scripts/verify-authenticated-api.sh
AUTH_TOKEN=<jwt> BACKEND_URL=https://your-backend.up.railway.app scripts/verify-email-alerts.sh
scripts/verify-celery-config.sh
```

`verify-railway-env.sh` is expected to fail against `.env.railway.example` until every placeholder value is replaced with real Supabase, Upstash, Resend, Sentry, JWT, and Vercel values.

## Backups

Use Supabase automated backups. For additional private backups, schedule encrypted `pg_dump` exports from Railway cron or GitHub Actions into private object storage.
