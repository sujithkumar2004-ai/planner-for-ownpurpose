# FinalPlanner Monk Mode Life OS

Private production-grade discipline enforcement platform for exam preparation, backend engineering, LLM / Agentic AI learning, gym, sleep, anti-distraction tracking, warnings, recovery mode, travel mode, analytics, notifications, and Resend email accountability.

## Stack

- Frontend: Next.js 14 App Router, TypeScript, TailwindCSS, shadcn-style UI primitives, Zustand, React Query, Framer Motion, PWA support
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Alembic, Celery, Redis
- Auth: JWT
- Email: Resend
- Monitoring: Sentry and structured logging hooks
- Deployment: Vercel frontend, Render backend, Supabase PostgreSQL, Upstash / Redis Cloud

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
2. Set root directory to `frontend`.
3. Set `NEXT_PUBLIC_API_BASE_URL`.
4. Push to `main`; Vercel auto-deploys.
5. Configure `NEXT_PUBLIC_SENTRY_DSN` after creating the Sentry frontend project.

Backend:

1. Create a Render Blueprint using `infra/render.yaml`.
2. Set `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, and `SENTRY_DSN`.
3. Use Supabase PostgreSQL and Upstash / Redis Cloud.
4. Render auto-deploys on GitHub push.
5. Health check path is `/health`.
6. The Docker start command runs `alembic upgrade head` before Gunicorn/Uvicorn.
7. Optional production seed is controlled by `RUN_PRODUCTION_SEED`, `PRODUCTION_SEED_EMAIL`, and `PRODUCTION_SEED_PASSWORD`.

CI/CD:

- `.github/workflows/ci.yml` builds frontend and compiles backend.
- `.github/workflows/backend-cron.yml` can trigger an external cron URL if you prefer GitHub Actions scheduling.
- `.github/workflows/render-smoke.yml` verifies production frontend and backend URLs after secrets are configured.

Required hosted secrets:

- Vercel: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SENTRY_DSN`
- Render: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `SENTRY_DSN`
- GitHub Actions: `BACKEND_HEALTH_URL`, `FRONTEND_URL`, optional `BACKEND_CRON_URL`

## Backups

Use Supabase automated backups. For additional private backups, schedule encrypted `pg_dump` exports from Render cron or GitHub Actions into private object storage.
