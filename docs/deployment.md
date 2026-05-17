# Deployment

## Frontend: Vercel

1. Import the GitHub repository.
2. Set root directory to `frontend`.
3. Add `NEXT_PUBLIC_API_BASE_URL` pointing to the Render backend.
4. Push to GitHub. Vercel auto-deploys on push.

## Backend: Render

1. Create a Render Blueprint from `infra/render.yaml`.
2. Set `DATABASE_URL` to Supabase PostgreSQL.
3. Set `REDIS_URL` to Upstash or Redis Cloud.
4. Set `RESEND_API_KEY`, `EMAIL_FROM`, and `EMAIL_TO`.
5. The web service runs FastAPI. Worker runs Celery. Beat runs scheduled email jobs.

## Database: Supabase

Use Supabase PostgreSQL for production. Run Alembic migrations from the backend service before deployment promotion:

```bash
cd backend
alembic upgrade head
```

## Backups

Use Supabase scheduled backups. For additional exports, run weekly `pg_dump` from a GitHub Actions secret-backed workflow or Render cron job and store encrypted dumps in private object storage.

