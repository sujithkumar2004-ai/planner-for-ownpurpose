from celery import Celery
from celery.schedules import crontab
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config import get_settings

settings = get_settings()
redis_url = settings.redis_url
if redis_url.startswith("rediss://") and "ssl_cert_reqs=" not in redis_url:
    parts = urlsplit(redis_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["ssl_cert_reqs"] = "CERT_REQUIRED"
    redis_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

celery_app = Celery("finalplanner", broker=redis_url, backend=redis_url)
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
