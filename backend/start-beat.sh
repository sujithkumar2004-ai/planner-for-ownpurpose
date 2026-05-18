#!/bin/sh
set -eu

exec celery -A app.tasks beat \
  --loglevel="${CELERY_LOG_LEVEL:-INFO}" \
  --schedule="${CELERY_BEAT_SCHEDULE_FILE:-/tmp/celerybeat-schedule}"

