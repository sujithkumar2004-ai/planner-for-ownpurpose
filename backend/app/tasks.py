from datetime import date

from app.celery_app import celery_app
from app.database import SessionLocal
from app.email import send_daily_missed_task_email, send_weekly_summary_email
from app.life_os import refresh_exam_dates
from app.life_os_database import LifeOSSessionLocal
from app.services import users_for_alerts


@celery_app.task(name="app.tasks.send_daily_missed_task_emails")
def send_daily_missed_task_emails() -> dict:
    db = SessionLocal()
    sent = 0
    try:
        for user in users_for_alerts(db):
            if send_daily_missed_task_email(db, user, date.today()):
                sent += 1
        return {"sent": sent}
    finally:
        db.close()


@celery_app.task(name="app.tasks.send_weekly_summary_emails")
def send_weekly_summary_emails() -> dict:
    db = SessionLocal()
    sent = 0
    try:
        for user in users_for_alerts(db):
            if send_weekly_summary_email(db, user, date.today()):
                sent += 1
        return {"sent": sent}
    finally:
        db.close()


@celery_app.task(name="app.tasks.refresh_exam_dates")
def refresh_exam_dates_task() -> dict:
    db = LifeOSSessionLocal()
    try:
        refreshed = refresh_exam_dates(db)
        return {"refreshed": len(refreshed)}
    finally:
        db.close()
