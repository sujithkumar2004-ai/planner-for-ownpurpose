#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CELERY_APP="$ROOT/backend/app/celery_app.py"
TASKS="$ROOT/backend/app/tasks.py"

grep -q "daily-missed-task-email-1130pm" "$CELERY_APP"
grep -q "app.tasks.send_daily_missed_task_emails" "$CELERY_APP"
grep -q "weekly-summary-sunday-9pm" "$CELERY_APP"
grep -q "app.tasks.send_weekly_summary_emails" "$CELERY_APP"
grep -q "def send_daily_missed_task_emails" "$TASKS"
grep -q "def send_weekly_summary_emails" "$TASKS"

echo "Celery beat schedule and task entrypoints are configured."
