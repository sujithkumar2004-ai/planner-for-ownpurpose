# Deployment

## Frontend: Vercel

1. Import the GitHub repository.
2. Set root directory to `frontend`.
3. Add `NEXT_PUBLIC_API_BASE_URL` pointing to the Railway backend.
4. Push to GitHub. Vercel auto-deploys on push.

## Backend: Railway

1. Create a Railway project from the GitHub repository.
2. Create the FastAPI web service from root `railway.json`.
3. Create a Celery worker service using `infra/railway-worker.json`.
4. Create a Celery beat service using `infra/railway-beat.json`.
5. Set `DATABASE_URL` to the Supabase pooled connection string.
6. Set `DIRECT_URL` to the Supabase direct connection string for Alembic migrations.
7. Set `REDIS_URL` to Upstash Redis.
8. Set `RESEND_API_KEY`, `EMAIL_FROM`, and `EMAIL_TO`.
9. The web service runs FastAPI through Gunicorn/Uvicorn. Worker runs Celery. Beat runs scheduled email jobs.

Railway should be connected directly to GitHub with automatic deploys enabled on branch `main`. No manual CLI deploy is required after setup.

## Verification

```bash
scripts/verify-railway-env.sh .env.railway.example
BACKEND_URL=https://your-backend.up.railway.app FRONTEND_URL=https://your-app.vercel.app scripts/verify-production-smoke.sh
AUTH_TOKEN=<jwt> BACKEND_URL=https://your-backend.up.railway.app scripts/verify-authenticated-api.sh
AUTH_TOKEN=<jwt> BACKEND_URL=https://your-backend.up.railway.app scripts/verify-email-alerts.sh
scripts/verify-celery-config.sh
```

Confirm Celery worker and beat are running in Railway service logs. Beat must show the daily 11:30 PM task and Sunday 9 PM task loaded from `app.celery_app`.

## Database: Supabase

Use Supabase PostgreSQL for production. Run Alembic migrations from the backend service before deployment promotion:

```bash
cd backend
alembic upgrade head
```

## Backups

Use Supabase scheduled backups. For additional exports, run weekly `pg_dump` from a GitHub Actions secret-backed workflow or Railway cron job and store encrypted dumps in private object storage.
