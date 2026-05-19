from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery("finalplanner", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = settings.timezone
celery_app.conf.beat_schedule = {
    "daily-missed-task-email-1130pm": {
        "task": "app.tasks.send_daily_missed_task_emails",
        "schedule": crontab(hour=23, minute=30),
    },
    "weekly-summary-sunday-9pm": {
        "task": "app.tasks.send_weekly_summary_emails",
        "schedule": crontab(hour=21, minute=0, day_of_week="sun"),
    },
    "refresh-exam-dates-daily": {
        "task": "app.tasks.refresh_exam_dates",
        "schedule": crontab(hour=5, minute=30),
    },
}
