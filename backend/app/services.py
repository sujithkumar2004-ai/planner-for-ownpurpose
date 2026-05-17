from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    DailyTask,
    DisciplineScore,
    DisciplineStatus,
    DistractionLog,
    ExamTopic,
    GymLog,
    MockTest,
    Notification,
    NotificationType,
    RecoveryMode,
    SleepLog,
    TaskCategory,
    TravelBreak,
    User,
    Warning,
    WarningLevel,
    WeeklyReview,
)


MANDATORY_CATEGORIES = {
    TaskCategory.BACKEND,
    TaskCategory.LLM_AGENTIC_AI,
    TaskCategory.EXAM_FOUNDATION,
    TaskCategory.EXAM_ROTATION,
    TaskCategory.REVISION,
    TaskCategory.GYM,
    TaskCategory.JOURNAL,
}


def completion_for_date(db: Session, user_id: int, target_date: date) -> float:
    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.task_date == target_date)).all()
    if not tasks:
        return 0
    return round(sum(1 for task in tasks if task.completed) / len(tasks) * 100, 2)


def travel_mode_active(db: Session, user_id: int, target_date: date) -> bool:
    return bool(
        db.scalar(
            select(TravelBreak).where(
                TravelBreak.user_id == user_id,
                TravelBreak.start_date <= target_date,
                TravelBreak.end_date >= target_date,
            )
        )
    )


def score_status(score: int) -> DisciplineStatus:
    if score >= 85:
        return DisciplineStatus.ELITE
    if score >= 70:
        return DisciplineStatus.ON_TRACK
    if score >= 50:
        return DisciplineStatus.WARNING
    return DisciplineStatus.CRITICAL


def warning_level_for_score(score: int) -> WarningLevel:
    if score >= 85:
        return WarningLevel.GREEN
    if score >= 70:
        return WarningLevel.YELLOW
    if score >= 50:
        return WarningLevel.ORANGE
    return WarningLevel.RED


def task_done(tasks: list[DailyTask], category: TaskCategory) -> bool:
    return any(task.category == category and task.completed for task in tasks)


def calculate_daily_discipline_score(db: Session, user_id: int, target_date: date) -> DisciplineScore:
    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.task_date == target_date)).all()
    sleep = db.scalar(select(SleepLog).where(SleepLog.user_id == user_id, SleepLog.sleep_date == target_date))
    distraction_minutes = db.scalar(
        select(func.coalesce(func.sum(DistractionLog.minutes), 0)).where(
            DistractionLog.user_id == user_id,
            DistractionLog.log_date == target_date,
        )
    )
    in_travel = travel_mode_active(db, user_id, target_date)

    if in_travel:
        formula = any(task.title == "Formula Revision" and task.completed for task in tasks)
        reading = any(task.title == "Reading / Vocab" and task.completed for task in tasks)
        journal = any(task.category == TaskCategory.JOURNAL and task.completed for task in tasks)
        walking = any("walk" in task.title.lower() and task.completed for task in tasks)
        breakdown = {
            "light_revision": 35 if formula else 0,
            "reading_vocab": 25 if reading else 0,
            "journal": 20 if journal else 0,
            "walking": 10 if walking else 0,
            "sleep_target_met": 5 if sleep and sleep.hours >= 6 else 0,
            "no_distraction_penalty": 5 if (distraction_minutes or 0) == 0 else 0,
        }
    else:
        revision_or_journal = task_done(tasks, TaskCategory.REVISION) and task_done(tasks, TaskCategory.JOURNAL)
        breakdown = {
            "backend_block_completed": 20 if task_done(tasks, TaskCategory.BACKEND) else 0,
            "llm_agentic_ai_block_completed": 20 if task_done(tasks, TaskCategory.LLM_AGENTIC_AI) else 0,
            "exam_foundation_completed": 15 if task_done(tasks, TaskCategory.EXAM_FOUNDATION) else 0,
            "specialized_exam_block_completed": 15 if task_done(tasks, TaskCategory.EXAM_ROTATION) else 0,
            "revision_journal_completed": 10 if revision_or_journal else 0,
            "gym_completed": 10 if task_done(tasks, TaskCategory.GYM) else 0,
            "sleep_target_met": 5 if sleep and sleep.hours >= 6 else 0,
            "no_distraction_penalty": 5 if (distraction_minutes or 0) == 0 else 0,
        }

    total = int(sum(breakdown.values()))
    existing = db.scalar(select(DisciplineScore).where(DisciplineScore.user_id == user_id, DisciplineScore.score_date == target_date))
    score = existing or DisciplineScore(user_id=user_id, score_date=target_date)
    score.score = total
    score.status = score_status(total)
    score.breakdown = breakdown
    score.travel_mode = in_travel
    score.warning_level = warning_level_for_score(total)
    score.recovery_mode = should_activate_recovery(db, user_id, target_date)
    db.add(score)
    db.commit()
    db.refresh(score)
    if score.recovery_mode:
        activate_recovery_mode(db, user_id, target_date + timedelta(days=1))
    return score


def should_activate_recovery(db: Session, user_id: int, target_date: date) -> bool:
    scores = db.scalars(
        select(DisciplineScore).where(
            DisciplineScore.user_id == user_id,
            DisciplineScore.score_date.in_([target_date, target_date - timedelta(days=1)]),
        )
    ).all()
    return len(scores) == 2 and all(score.score < 50 for score in scores)


def activate_recovery_mode(db: Session, user_id: int, recovery_date: date) -> RecoveryMode:
    plan = {
        "priority": ["Backend Engineering", "LLM / Agentic AI", "Exam Common Foundation"],
        "locked_optional_tasks": True,
        "new_task_policy": "reduced",
    }
    recovery = db.scalar(select(RecoveryMode).where(RecoveryMode.user_id == user_id, RecoveryMode.recovery_date == recovery_date))
    if not recovery:
        recovery = RecoveryMode(user_id=user_id, recovery_date=recovery_date, reason="Daily score below 50 for 2 consecutive days", priority_plan=plan)
    recovery.active = True
    recovery.priority_plan = plan
    db.add(recovery)

    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.task_date == recovery_date)).all()
    for task in tasks:
        task.locked = task.category not in {TaskCategory.BACKEND, TaskCategory.LLM_AGENTIC_AI, TaskCategory.EXAM_FOUNDATION}
        task.mandatory = task.category in MANDATORY_CATEGORIES

    db.add(Warning(user_id=user_id, rule_code="recovery_mode", level=WarningLevel.RED, message="Recovery mode activated: backend, LLM, and exam foundation are the only priorities."))
    db.add(Notification(user_id=user_id, type=NotificationType.RECOVERY, title="Recovery mode activated", body="Optional tasks are locked until recovery priorities are completed.", level=WarningLevel.RED))
    db.commit()
    db.refresh(recovery)
    return recovery


def missed_mandatory_tasks(db: Session, user_id: int, target_date: date) -> list[DailyTask]:
    return db.scalars(
        select(DailyTask).where(
            DailyTask.user_id == user_id,
            DailyTask.task_date == target_date,
            DailyTask.mandatory.is_(True),
            DailyTask.completed.is_(False),
        )
    ).all()


def generate_warnings(db: Session, user_id: int) -> list[Warning]:
    db.query(Warning).filter(Warning.user_id == user_id, Warning.active.is_(True)).update({"active": False})
    today = date.today()
    warnings: list[Warning] = []

    def add(rule_code: str, level: WarningLevel, message: str) -> None:
        warning = Warning(user_id=user_id, rule_code=rule_code, level=level, message=message, active=True)
        db.add(warning)
        warnings.append(warning)

    for category, rule_code, label in [
        (TaskCategory.BACKEND, "missed_backend_2_days", "Backend Engineering"),
        (TaskCategory.LLM_AGENTIC_AI, "missed_llm_2_days", "LLM / Agentic AI"),
    ]:
        recent = db.scalars(
            select(DailyTask).where(
                DailyTask.user_id == user_id,
                DailyTask.category == category,
                DailyTask.task_date.in_([today - timedelta(days=1), today - timedelta(days=2)]),
            )
        ).all()
        if len(recent) == 2 and all(not task.completed for task in recent):
            add(rule_code, WarningLevel.ORANGE, f"{label} was missed for 2 continuous days.")

    weekday_start = today - timedelta(days=7)
    gym_count = db.scalar(
        select(func.count(GymLog.id)).where(
            GymLog.user_id == user_id,
            GymLog.log_date >= weekday_start,
            GymLog.completed.is_(True),
        )
    )
    if (gym_count or 0) < 3:
        add("no_gym_3_weekdays", WarningLevel.ORANGE, "Gym completion is below 3 weekdays this week.")

    latest_mock = db.scalar(select(func.max(MockTest.taken_on)).where(MockTest.user_id == user_id))
    if latest_mock is None or latest_mock <= today - timedelta(days=14):
        add("no_mock_14_days", WarningLevel.RED, "No mock test has been logged in the last 14 days.")

    recent_revision = db.scalar(
        select(func.count(DailyTask.id)).where(
            DailyTask.user_id == user_id,
            DailyTask.category == TaskCategory.REVISION,
            DailyTask.task_date >= today - timedelta(days=5),
            DailyTask.completed.is_(True),
        )
    )
    if (recent_revision or 0) == 0:
        add("no_revision_5_days", WarningLevel.ORANGE, "No revision block has been completed in the last 5 days.")

    backlog_count = db.scalar(select(func.count(ExamTopic.id)).where(ExamTopic.user_id == user_id, ExamTopic.backlog_percent > 25))
    if (backlog_count or 0) > 0:
        add("topic_backlog_25", WarningLevel.RED, f"{backlog_count} exam topics have backlog above 25%.")

    travel_breaks = db.scalars(select(TravelBreak).where(TravelBreak.user_id == user_id)).all()
    for travel in travel_breaks:
        duration = (travel.end_date - travel.start_date).days + 1
        if duration > 14:
            add("travel_over_14", WarningLevel.RED, "Travel break exceeds the 14 day maximum.")

    today_completion = completion_for_date(db, user_id, today)
    if today_completion < 60:
        add("daily_below_60", WarningLevel.YELLOW, f"Daily completion is {today_completion}% today.")

    low_sleep_days = db.scalar(
        select(func.count(SleepLog.id)).where(
            SleepLog.user_id == user_id,
            SleepLog.sleep_date >= today - timedelta(days=3),
            SleepLog.hours < 6,
        )
    )
    if (low_sleep_days or 0) >= 3:
        add("low_sleep_3_days", WarningLevel.RED, "Sleep was below 6 hours for 3 days.")

    mandatory_missed = missed_mandatory_tasks(db, user_id, today)
    if mandatory_missed:
        add("mandatory_block_missed", WarningLevel.RED, f"{len(mandatory_missed)} mandatory Monk Mode blocks are incomplete today.")

    week_scores = [calculate_daily_discipline_score(db, user_id, today - timedelta(days=offset)).score for offset in range(7)]
    weekly_score = round(sum(week_scores) / 7, 2)
    if weekly_score < 70:
        add("weekly_below_70", WarningLevel.ORANGE, f"Weekly score is {weekly_score}%.")

    db.commit()
    for warning in warnings:
        db.refresh(warning)
    return warnings


def build_weekly_review(db: Session, user_id: int, week_end: date | None = None) -> WeeklyReview:
    end = week_end or date.today()
    start = end - timedelta(days=6)
    scores = [calculate_daily_discipline_score(db, user_id, start + timedelta(days=offset)) for offset in range(7)]
    average = round(sum(score.score for score in scores) / 7, 2)
    best = max(scores, key=lambda score: score.score)
    worst = min(scores, key=lambda score: score.score)
    missed: dict[str, int] = {}
    for offset in range(7):
        day = start + timedelta(days=offset)
        for task in missed_mandatory_tasks(db, user_id, day):
            missed[task.title] = missed.get(task.title, 0) + 1
    focus = {
        "protect_non_negotiables": ["Backend Engineering", "LLM / Agentic AI", "Gym Monday-Friday"],
        "repair_blocks": sorted(missed, key=missed.get, reverse=True)[:3],
        "minimum_daily_score": 70,
        "minimum_weekly_score": 75,
    }
    review = db.scalar(select(WeeklyReview).where(WeeklyReview.user_id == user_id, WeeklyReview.week_start == start))
    if not review:
        review = WeeklyReview(user_id=user_id, week_start=start, week_end=end)
    review.weekly_score = average
    review.best_day = best.score_date.isoformat()
    review.worst_day = worst.score_date.isoformat()
    review.missed_blocks = missed
    review.next_week_focus = focus
    review.correction_day = average < 70
    db.add(review)
    if average < 70:
        db.add(Notification(user_id=user_id, type=NotificationType.WEEKLY_REVIEW, title="Monday correction day", body="Weekly score fell below 70%. Next Monday is marked for backlog repair.", level=WarningLevel.RED))
    db.commit()
    db.refresh(review)
    return review


def daily_recovery_plan(db: Session, user_id: int, target_date: date) -> dict:
    score = calculate_daily_discipline_score(db, user_id, target_date)
    missed = [task.title for task in missed_mandatory_tasks(db, user_id, target_date)]
    return {
        "score": score.score,
        "status": score.status.value,
        "warning_level": score.warning_level.value,
        "missed_tasks": missed,
        "tomorrow": {
            "mode": "recovery" if score.score < 50 else "normal",
            "priorities": ["Backend Engineering", "LLM / Agentic AI", "Exam Common Foundation"] if missed else ["Protect non-negotiable blocks"],
            "locked_optional_tasks": score.score < 50,
        },
    }


def users_for_alerts(db: Session) -> list[User]:
    return db.scalars(select(User)).all()
