#!/bin/sh
set -eu

exec celery -A app.tasks worker \
  --loglevel="${CELERY_LOG_LEVEL:-INFO}" \
  --concurrency="${CELERY_CONCURRENCY:-2}"

