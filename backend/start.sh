#!/bin/sh
set -eu

cd "$(dirname "$0")"

alembic upgrade head
if [ -n "${LIFE_OS_DATABASE_URL:-}" ]; then
  alembic -c life_os_alembic.ini upgrade head
else
  echo "LIFE_OS_DATABASE_URL is not set; skipping Life OS migrations"
fi
python -m app.production_seed

exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --access-logfile - \
  --error-logfile - \
  --timeout 120
