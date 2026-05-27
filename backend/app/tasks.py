from datetime import date

from sqlalchemy import select

from app.celery_app import celery_app
from app.database import SessionLocal
from app.email import send_daily_missed_task_email, send_weekly_summary_email
from app.life_os import refresh_exam_dates, run_daily_accountability_cycle
from app.life_os_database import LifeOSSessionLocal
from app.services import users_for_alerts
from app.models import User


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


@celery_app.task(name="app.tasks.run_daily_accountability_regeneration")
def run_daily_accountability_regeneration() -> dict:
    user_db = SessionLocal()
    life_db = LifeOSSessionLocal()
    processed = 0
    try:
        user_ids = [row[0] for row in user_db.execute(select(User.id)).all()]
        for user_id in user_ids:
            run_daily_accountability_cycle(life_db, user_id, date.today())
            processed += 1
        return {"processed": processed}
    finally:
        user_db.close()
        life_db.close()
