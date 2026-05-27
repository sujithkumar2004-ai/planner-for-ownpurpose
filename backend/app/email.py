import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import GeneratedDailyTask, Notification, NotificationType, TaskStatus, User, WarningLevel
from app.services import build_weekly_review, daily_recovery_plan

logger = logging.getLogger(__name__)


def send_email(subject: str, html: str) -> bool:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY is not configured; email skipped: %s", subject)
        return False
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
        json={"from": settings.email_from, "to": [settings.email_to], "subject": subject, "html": html},
        timeout=20,
    )
    if response.status_code >= 400:
        logger.error("Resend failed: %s %s", response.status_code, response.text)
        return False
    return True


def send_daily_missed_task_email(db: Session, user: User, target_date) -> bool:
    plan = daily_recovery_plan(db, user.id, target_date)
    generated = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user.id, GeneratedDailyTask.task_date == target_date)).all()
    planned = [task.title for task in generated]
    completed = [task.title for task in generated if task.status == TaskStatus.COMPLETED]
    missed_generated = [task.title for task in generated if task.status != TaskStatus.COMPLETED]
    if not plan["missed_tasks"] and not generated:
        return False
    html = f"""
    <h2>FinalPlanner Daily Accountability</h2>
    <p><strong>Date:</strong> {target_date}</p>
    <p><strong>Planned:</strong> {len(planned)} block(s)</p>
    <p><strong>Actually completed:</strong> {len(completed)} block(s)</p>
    <p><strong>Daily discipline score:</strong> {plan["score"]}/100 ({plan["status"]})</p>
    <p><strong>Warning level:</strong> {plan["warning_level"]}</p>
    <h3>Planned vs actual</h3>
    <ul>{"".join(f"<li>{task} - {'done' if task in completed else 'missed'}</li>" for task in planned[:12])}</ul>
    <h3>Missed blocks</h3>
    <ul>{"".join(f"<li>{task}</li>" for task in (missed_generated or plan["missed_tasks"])[:12])}</ul>
    <h3>Tomorrow recovery plan</h3>
    <ul>{"".join(f"<li>{item}</li>" for item in plan["tomorrow"]["priorities"])}</ul>
    <p><strong>Optional task lock:</strong> {plan["tomorrow"]["locked_optional_tasks"]}</p>
    """
    sent = send_email(f"FinalPlanner Daily Accountability - {target_date}", html)
    db.add(Notification(user_id=user.id, type=NotificationType.EMAIL, title="Daily missed-task email", body=f"Daily alert sent: {sent}", level=WarningLevel.RED))
    db.commit()
    return sent


def send_weekly_summary_email(db: Session, user: User, week_end) -> bool:
    review = build_weekly_review(db, user.id, week_end)
    html = f"""
    <h2>FinalPlanner Weekly Monk Mode Review</h2>
    <p><strong>Week:</strong> {review.week_start} to {review.week_end}</p>
    <p><strong>Weekly score:</strong> {review.weekly_score}%</p>
    <p><strong>Best day:</strong> {review.best_day}</p>
    <p><strong>Worst day:</strong> {review.worst_day}</p>
    <h3>Missed blocks</h3>
    <ul>{"".join(f"<li>{name}: {count}</li>" for name, count in review.missed_blocks.items())}</ul>
    <h3>Next week focus</h3>
    <ul>{"".join(f"<li>{item}</li>" for item in review.next_week_focus.get("protect_non_negotiables", []))}</ul>
    <p><strong>Correction day:</strong> {review.correction_day}</p>
    """
    sent = send_email(f"Weekly Monk Mode Review - {review.week_end}", html)
    db.add(Notification(user_id=user.id, type=NotificationType.EMAIL, title="Weekly summary email", body=f"Weekly summary sent: {sent}", level=WarningLevel.YELLOW))
    db.commit()
    return sent
