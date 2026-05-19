#!/bin/sh
set -eu

alembic upgrade head
if [ -n "${LIFE_OS_DATABASE_URL:-}" ]; then
  alembic -c life_os_alembic.ini upgrade head
fi
python -m app.production_seed

exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --access-logfile - \
  --error-logfile - \
  --timeout 120
