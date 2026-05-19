from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    CalendarEvent,
    DailyCheckIn,
    Exam,
    ExamDate,
    ExamDateStatus,
    FocusSession,
    GeneratedDailyTask,
    Goal,
    GoalStatus,
    Habit,
    HabitLog,
    LifeTask,
    Milestone,
    ProductivityLog,
    StudyPlan,
    StudyTaskType,
    SyllabusSubject,
    SyllabusTopic,
    TaskStatus,
    TravelModeSettings,
)


OFFICIAL_EXAM_SOURCES = {
    "CAT2026": "https://iimcat.ac.in/",
    "GATE_DA_2026": "https://gate2026.iitg.ac.in/",
    "GATE_ME_2026": "https://gate2026.iitg.ac.in/",
    "JAM_MA_2026": "https://jam2026.iitb.ac.in/",
    "JAM_PH_2026": "https://jam2026.iitb.ac.in/",
}


EXAM_CATALOG = {
    "CAT2026": {
        "name": "CAT 2026",
        "date": date(2026, 11, 29),
        "status": ExamDateStatus.TENTATIVE,
        "description": "Common Admission Test preparation plan.",
        "subjects": {
            "VARC": ["Reading comprehension", "Para summary", "Para jumbles", "Odd sentence", "Vocabulary in context", "Critical reasoning"],
            "LRDI": ["Arrangements", "Games and tournaments", "Routes and networks", "Tables and charts", "Set theory", "Logical caselets"],
            "Quant": ["Arithmetic", "Algebra", "Geometry", "Number systems", "Modern math", "Mensuration"],
        },
    },
    "GATE_DA_2026": {
        "name": "GATE DA 2026",
        "date": date(2026, 2, 15),
        "status": ExamDateStatus.OFFICIAL,
        "description": "GATE Data Science and Artificial Intelligence preparation plan.",
        "subjects": {
            "Probability/Statistics": ["Counting", "Probability axioms", "Random variables", "Distributions", "Estimation", "Hypothesis testing"],
            "Linear Algebra": ["Vector spaces", "Matrices", "Rank", "Eigenvalues", "SVD", "Projections"],
            "Calculus/Optimization": ["Limits", "Differentiability", "Partial derivatives", "Gradient descent", "Convex optimization", "Lagrange multipliers"],
            "Programming/DSA": ["Python programming", "Complexity", "Arrays", "Trees", "Graphs", "Dynamic programming"],
            "DBMS/Warehousing": ["ER model", "Relational algebra", "SQL", "Normalization", "Indexing", "Data warehousing"],
            "ML": ["Regression", "Classification", "SVM", "Trees", "Clustering", "Model evaluation"],
            "AI": ["Search", "Logic", "Planning", "Knowledge representation", "Reasoning", "Neural networks"],
        },
    },
    "GATE_ME_2026": {
        "name": "GATE ME 2026",
        "date": date(2026, 2, 14),
        "status": ExamDateStatus.OFFICIAL,
        "description": "GATE Mechanical Engineering preparation plan.",
        "subjects": {
            "Engineering Mathematics": ["Linear algebra", "Calculus", "Differential equations", "Complex variables", "Probability", "Numerical methods"],
            "Applied Mechanics": ["Engineering mechanics", "Strength of materials", "Theory of machines", "Vibrations", "Machine design"],
            "Fluid/Thermal": ["Fluid mechanics", "Heat transfer", "Thermodynamics", "IC engines", "Refrigeration", "Turbomachinery"],
            "Materials/Manufacturing/Industrial": ["Materials", "Casting", "Metal forming", "Machining", "Metrology", "Operations research"],
        },
    },
    "JAM_MA_2026": {
        "name": "JAM MA 2026",
        "date": date(2026, 2, 15),
        "status": ExamDateStatus.OFFICIAL,
        "description": "IIT JAM Mathematics preparation plan.",
        "subjects": {
            "Real Analysis": ["Sequences", "Series", "Continuity", "Differentiability", "Riemann integration", "Metric spaces"],
            "Multivariable Calculus": ["Partial derivatives", "Multiple integrals", "Vector calculus", "Maxima minima", "Jacobians"],
            "Differential Equations": ["First order ODE", "Higher order ODE", "Power series solutions", "Systems of ODE"],
            "Linear Algebra": ["Matrices", "Vector spaces", "Linear transformations", "Eigenvalues", "Inner product spaces"],
            "Algebra": ["Groups", "Subgroups", "Cyclic groups", "Rings", "Fields", "Polynomials"],
        },
    },
    "JAM_PH_2026": {
        "name": "JAM PH 2026",
        "date": date(2026, 2, 15),
        "status": ExamDateStatus.OFFICIAL,
        "description": "IIT JAM Physics preparation plan.",
        "subjects": {
            "Mathematical Methods": ["Vector algebra", "Calculus", "Differential equations", "Matrices", "Fourier series", "Complex analysis"],
            "Mechanics": ["Newtonian mechanics", "Central force", "Rigid body", "Lagrangian mechanics", "Special relativity"],
            "Waves/Optics": ["Oscillations", "Wave motion", "Interference", "Diffraction", "Polarization"],
            "E&M": ["Electrostatics", "Magnetostatics", "Maxwell equations", "EM waves", "Circuits"],
            "Thermodynamics": ["Laws of thermodynamics", "Kinetic theory", "Statistical physics", "Entropy"],
            "Modern Physics": ["Quantum basics", "Atomic physics", "Nuclear physics", "Solid state basics"],
            "Electronics": ["Semiconductors", "Diodes", "Transistors", "Op-amps", "Digital logic"],
        },
    },
}


def ensure_exam_catalog(db: Session, user_id: int | None = None) -> None:
    for exam_index, (code, config) in enumerate(EXAM_CATALOG.items()):
        exam = db.scalar(select(Exam).where(Exam.code == code))
        if not exam:
            exam = Exam(code=code, name=config["name"], description=config["description"], active=True)
            db.add(exam)
            db.flush()
        else:
            exam.name = config["name"]
            exam.description = config["description"]
            exam.active = True

        exam_date = db.scalar(select(ExamDate).where(ExamDate.exam_id == exam.id, ExamDate.label == "Main exam"))
        if not exam_date:
            exam_date = ExamDate(exam_id=exam.id, label="Main exam")
            db.add(exam_date)
        if not exam_date.manually_overridden:
            exam_date.exam_date = config["date"]
            exam_date.status = config["status"]
            exam_date.source_url = OFFICIAL_EXAM_SOURCES[code]
            exam_date.source_name = "Official exam website"

        for subject_index, (subject_name, topics) in enumerate(config["subjects"].items()):
            subject = db.scalar(select(SyllabusSubject).where(SyllabusSubject.exam_id == exam.id, SyllabusSubject.name == subject_name))
            if not subject:
                subject = SyllabusSubject(exam_id=exam.id, name=subject_name)
                db.add(subject)
                db.flush()
            subject.order_index = subject_index
            subject.weight = 1.0
            for topic_index, topic_name in enumerate(topics):
                topic = db.scalar(select(SyllabusTopic).where(SyllabusTopic.subject_id == subject.id, SyllabusTopic.name == topic_name))
                if not topic:
                    topic = SyllabusTopic(subject_id=subject.id, name=topic_name, progress_percent=0, weak_score=50)
                    db.add(topic)
                topic.order_index = topic_index
                topic.difficulty = 2 + ((exam_index + subject_index + topic_index) % 4)
                topic.estimated_hours = float(3 + topic.difficulty)
                topic.source_ref = f"{config['name']} syllabus import"

        if user_id and not db.scalar(select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.exam_id == exam.id)):
            db.add(StudyPlan(user_id=user_id, exam_id=exam.id, active=True, available_hours_per_day=4.0))

    if user_id and not db.scalar(select(TravelModeSettings).where(TravelModeSettings.user_id == user_id)):
        db.add(TravelModeSettings(user_id=user_id))
    db.commit()


def get_travel_settings(db: Session, user_id: int) -> TravelModeSettings:
    settings = db.scalar(select(TravelModeSettings).where(TravelModeSettings.user_id == user_id))
    if not settings:
        settings = TravelModeSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def refresh_exam_dates(db: Session) -> list[ExamDate]:
    ensure_exam_catalog(db)
    refreshed: list[ExamDate] = []
    for exam in db.scalars(select(Exam)).all():
        exam_date = db.scalar(select(ExamDate).where(ExamDate.exam_id == exam.id, ExamDate.label == "Main exam"))
        if not exam_date or exam_date.manually_overridden:
            continue
        source_url = OFFICIAL_EXAM_SOURCES.get(exam.code)
        found = None
        if source_url:
            try:
                html = requests.get(source_url, timeout=8).text
                found = _extract_date_for_exam(exam.code, html)
            except requests.RequestException:
                found = None
        if found:
            exam_date.exam_date = found
            exam_date.status = ExamDateStatus.OFFICIAL
        exam_date.refreshed_at = datetime.utcnow()
        db.add(exam_date)
        refreshed.append(exam_date)
    db.commit()
    return refreshed


def _extract_date_for_exam(code: str, html: str) -> date | None:
    compact = re.sub(r"\s+", " ", html)
    patterns = [
        r"(\d{1,2})\s+February\s+2026",
        r"February\s+(\d{1,2}),?\s+2026",
        r"(\d{1,2})\s+November\s+2026",
        r"November\s+(\d{1,2}),?\s+2026",
    ]
    month = 11 if code == "CAT2026" else 2
    for pattern in patterns:
        for match in re.finditer(pattern, compact, flags=re.IGNORECASE):
            day = int(match.group(1))
            if 1 <= day <= 31:
                return date(2026, month, day)
    return None


def generate_daily_tasks(db: Session, user_id: int, target_date: date | None = None, force: bool = False) -> list[GeneratedDailyTask]:
    ensure_exam_catalog(db, user_id)
    target_date = target_date or date.today()
    if force:
        existing = db.scalars(
            select(GeneratedDailyTask).where(
                GeneratedDailyTask.user_id == user_id,
                GeneratedDailyTask.task_date == target_date,
                GeneratedDailyTask.status != TaskStatus.COMPLETED,
            )
        ).all()
        for task in existing:
            db.delete(task)
        db.commit()

    existing_today = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date)).all()
    if existing_today:
        return existing_today

    travel = get_travel_settings(db, user_id)
    plans = db.scalars(select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.active.is_(True))).all()
    available_minutes = travel.daily_minutes if travel.enabled else int(sum(plan.available_hours_per_day for plan in plans) * 60 / max(len(plans), 1))
    available_minutes = max(45, min(available_minutes, 360))

    carry_forward_missed_tasks(db, user_id, target_date, travel.enabled)
    created: list[GeneratedDailyTask] = []
    per_task_minutes = 30 if travel.enabled else 55
    max_tasks = max(2, available_minutes // per_task_minutes)
    for plan in plans:
        exam = db.scalar(select(Exam).where(Exam.id == plan.exam_id).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics)))
        if not exam:
            continue
        exam_date = min((d.exam_date for d in exam.dates), default=target_date + timedelta(days=180))
        days_left = max((exam_date - target_date).days, 0)
        pending_topics = sorted(
            [topic for subject in exam.subjects for topic in subject.topics if topic.progress_percent < 100],
            key=lambda topic: (topic.progress_percent, -topic.weak_score, -topic.difficulty, topic.id),
        )
        if not pending_topics:
            continue
        topic = pending_topics[(target_date.toordinal() + exam.id) % len(pending_topics)]
        task_types = _task_mix(days_left, travel.enabled, travel.allow_mock_tests)
        for task_type in task_types[: max(1, max_tasks // max(len(plans), 1))]:
            title = _task_title(exam, topic, task_type)
            if db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date, GeneratedDailyTask.title == title, GeneratedDailyTask.task_type == task_type)):
                continue
            task = GeneratedDailyTask(
                user_id=user_id,
                exam_id=exam.id,
                topic_id=topic.id,
                task_date=target_date,
                title=title,
                task_type=task_type,
                estimated_minutes=_task_minutes(task_type, travel.enabled),
                priority=5 if topic.weak_score >= 70 or days_left < 45 else 3,
                generated_reason=_task_reason(days_left, topic, travel.enabled),
            )
            db.add(task)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                return db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date).order_by(GeneratedDailyTask.priority.desc(), GeneratedDailyTask.id)).all()
            created.append(task)
            _ensure_calendar_event_for_task(db, user_id, task, len(created))
            if len(created) >= max_tasks:
                break
        if len(created) >= max_tasks:
            break

    if not created:
        task = GeneratedDailyTask(
            user_id=user_id,
            task_date=target_date,
            title="Review formulas and error log",
            task_type=StudyTaskType.FORMULA_REVIEW,
            estimated_minutes=30,
            generated_reason="Fallback lightweight review task",
        )
        db.add(task)
        db.flush()
        created.append(task)
        _ensure_calendar_event_for_task(db, user_id, task, 1)

    db.commit()
    return db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date).order_by(GeneratedDailyTask.priority.desc(), GeneratedDailyTask.id)).all()


def carry_forward_missed_tasks(db: Session, user_id: int, target_date: date, travel_enabled: bool) -> None:
    missed = db.scalars(
        select(GeneratedDailyTask).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date < target_date,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE]),
        ).order_by(GeneratedDailyTask.task_date, GeneratedDailyTask.priority.desc()).limit(3)
    ).all()
    for old_task in missed:
        old_task.status = TaskStatus.OVERDUE
        db.add(old_task)
        if travel_enabled and old_task.task_type in {StudyTaskType.MOCK, StudyTaskType.PRACTICE}:
            task_type = StudyTaskType.REVISION
            title = f"Light carry-forward: {old_task.title}"
            minutes = 25
        else:
            task_type = old_task.task_type
            title = f"Carry-forward: {old_task.title}"
            minutes = min(old_task.estimated_minutes, 45)
        if not db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date, GeneratedDailyTask.title == title)):
            carried = GeneratedDailyTask(
                user_id=user_id,
                exam_id=old_task.exam_id,
                topic_id=old_task.topic_id,
                task_date=target_date,
                title=title,
                task_type=task_type,
                estimated_minutes=minutes,
                priority=old_task.priority + 1,
                generated_reason="Missed work carried forward automatically",
                carried_from_task_id=old_task.id,
            )
            db.add(carried)
            db.flush()
            _ensure_calendar_event_for_task(db, user_id, carried, 1)


def complete_generated_task(db: Session, user_id: int, task_id: int, status: TaskStatus) -> GeneratedDailyTask | None:
    task = db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.id == task_id, GeneratedDailyTask.user_id == user_id))
    if not task:
        return None
    task.status = status
    task.completed_at = datetime.utcnow() if status == TaskStatus.COMPLETED else None
    db.add(task)
    event = db.scalar(select(CalendarEvent).where(CalendarEvent.user_id == user_id, CalendarEvent.generated_task_id == task.id))
    if event:
        event.completed = status == TaskStatus.COMPLETED
        db.add(event)
    if status == TaskStatus.COMPLETED and task.topic_id:
        topic = db.scalar(select(SyllabusTopic).where(SyllabusTopic.id == task.topic_id))
        if topic:
            increment = 8 if task.task_type in {StudyTaskType.CONCEPT, StudyTaskType.PRACTICE, StudyTaskType.PYQ} else 4
            topic.progress_percent = min(100, topic.progress_percent + increment)
            topic.weak_score = max(0, topic.weak_score - increment)
            db.add(topic)
    update_productivity_log(db, user_id, task.task_date)
    db.commit()
    db.refresh(task)
    return task


def update_productivity_log(db: Session, user_id: int, target_date: date) -> ProductivityLog:
    tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date)).all()
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    pending = sum(1 for task in tasks if task.status in {TaskStatus.PENDING, TaskStatus.ACTIVE})
    overdue = db.scalar(select(func.count(GeneratedDailyTask.id)).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date < target_date, GeneratedDailyTask.status != TaskStatus.COMPLETED)) or 0
    focus_minutes = db.scalar(
        select(func.coalesce(func.sum(FocusSession.duration_minutes), 0)).where(
            FocusSession.user_id == user_id,
            FocusSession.start_time >= datetime.combine(target_date, time.min),
            FocusSession.start_time <= datetime.combine(target_date, time.max),
        )
    ) or 0
    score = round((completed / max(len(tasks), 1) * 75) + min(focus_minutes / 120, 1) * 25, 1)
    log = db.scalar(select(ProductivityLog).where(ProductivityLog.user_id == user_id, ProductivityLog.log_date == target_date)) or ProductivityLog(user_id=user_id, log_date=target_date)
    log.completed_tasks = completed
    log.pending_tasks = pending
    log.overdue_tasks = overdue
    log.focus_minutes = int(focus_minutes)
    log.productivity_score = score
    db.add(log)
    return log


def build_live_dashboard(db: Session, user_id: int) -> dict:
    today = date.today()
    tasks = generate_daily_tasks(db, user_id, today)
    update_productivity_log(db, user_id, today)
    db.commit()
    log = db.scalar(select(ProductivityLog).where(ProductivityLog.user_id == user_id, ProductivityLog.log_date == today))
    events = db.scalars(
        select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_at >= datetime.combine(today, time.min),
            CalendarEvent.start_at <= datetime.combine(today, time.max),
        ).order_by(CalendarEvent.start_at)
    ).all()
    exams = db.scalars(select(Exam).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics))).all()
    exam_readiness = []
    weak_topics = []
    next_exam = None
    for exam in exams:
        topics = [topic for subject in exam.subjects for topic in subject.topics]
        completion = round(sum(topic.progress_percent for topic in topics) / max(len(topics), 1), 1)
        upcoming_dates = [d.exam_date for d in exam.dates if d.exam_date >= today]
        exam_date = min(upcoming_dates) if upcoming_dates else min((d.exam_date for d in exam.dates), default=today)
        days_left = max((exam_date - today).days, 0)
        readiness = round(min(100, completion * 0.75 + max(0, 100 - days_left) * 0.25), 1)
        exam_readiness.append({"exam_id": exam.id, "name": exam.name, "exam_date": exam_date.isoformat(), "days_left": days_left, "syllabus_completion": completion, "readiness_score": readiness})
        if next_exam is None or (exam_date >= today and exam_date < date.fromisoformat(next_exam["exam_date"])):
            next_exam = {"name": exam.name, "exam_date": exam_date.isoformat(), "days_left": days_left}
        for topic in sorted(topics, key=lambda t: (-t.weak_score, t.progress_percent))[:2]:
            if topic.progress_percent < 75:
                weak_topics.append({"exam": exam.name, "topic": topic.name, "progress": round(topic.progress_percent, 1), "weak_score": round(topic.weak_score, 1)})
    active_task = next((task for task in tasks if task.status == TaskStatus.ACTIVE), None) or next((task for task in tasks if task.status == TaskStatus.PENDING), None)
    habits = db.scalars(select(Habit).where(Habit.user_id == user_id)).all()
    habit_logs = db.scalars(select(HabitLog).join(Habit).where(Habit.user_id == user_id, HabitLog.log_date == today, HabitLog.completed.is_(True))).all()
    checkin = db.scalar(select(DailyCheckIn).where(DailyCheckIn.user_id == user_id, DailyCheckIn.log_date == today))
    return {
        "today_tasks": [_task_payload(db, task) for task in tasks],
        "completed_count": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
        "pending_count": sum(1 for task in tasks if task.status in {TaskStatus.PENDING, TaskStatus.ACTIVE}),
        "overdue_count": log.overdue_tasks if log else 0,
        "active_task": _task_payload(db, active_task) if active_task else None,
        "current_streak": sum(habit.current_streak for habit in habits),
        "exam_readiness": exam_readiness,
        "syllabus_completion": round(sum(item["syllabus_completion"] for item in exam_readiness) / max(len(exam_readiness), 1), 1),
        "focus_minutes_today": log.focus_minutes if log else 0,
        "focus_minutes_week": _focus_minutes_week(db, user_id, today),
        "calendar_events_today": [_event_payload(event) for event in events],
        "next_exam_countdown": next_exam,
        "weak_topics": weak_topics[:8],
        "recommended_next_action": active_task.title if active_task else "Plan tomorrow from the Exams page",
        "productivity_score": log.productivity_score if log else 0,
        "habit_completion_rate": round(len(habit_logs) / max(len(habits), 1) * 100, 1),
        "daily_checkin": checkin.productivity_score if checkin else None,
        "travel_mode": get_travel_settings(db, user_id).enabled,
    }


def build_life_os_weekly_review(db: Session, user_id: int, week_end: date | None = None) -> dict:
    week_end = week_end or date.today()
    week_start = week_end - timedelta(days=6)
    tasks = db.scalars(
        select(GeneratedDailyTask).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= week_start,
            GeneratedDailyTask.task_date <= week_end,
        )
    ).all()
    completed = [task for task in tasks if task.status == TaskStatus.COMPLETED]
    missed = [task for task in tasks if task.status in {TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE, TaskStatus.SKIPPED} and task.task_date < date.today()]
    dashboard = build_live_dashboard(db, user_id)
    weak_topics = dashboard["weak_topics"][:5]
    next_week_plan = []
    for item in weak_topics:
        next_week_plan.append(
            {
                "focus": item["topic"],
                "exam": item["exam"],
                "plan": "2 concept/practice blocks, 1 PYQ block, and 1 revision pass",
            }
        )
    if not next_week_plan and dashboard["active_task"]:
        next_week_plan.append({"focus": dashboard["active_task"]["title"], "exam": dashboard["active_task"].get("exam_name"), "plan": "Finish the active block and regenerate the next plan."})
    completion_rate = round(len(completed) / max(len(tasks), 1) * 100, 1)
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "summary": f"Completed {len(completed)} of {len(tasks)} generated tasks with {len(missed)} missed or overdue blocks.",
        "completed_tasks": len(completed),
        "missed_tasks": len(missed),
        "completion_rate": completion_rate,
        "weak_topics": weak_topics,
        "next_week_plan": next_week_plan,
        "recommended_action": dashboard["recommended_next_action"],
    }


def build_life_os_notifications(db: Session, user_id: int) -> list[dict]:
    today = date.today()
    dashboard = build_live_dashboard(db, user_id)
    notifications: list[dict] = []
    overdue = dashboard["overdue_count"]
    if overdue:
        notifications.append(
            {
                "id": "overdue",
                "type": "overdue",
                "title": "Overdue study blocks",
                "body": f"{overdue} task(s) are overdue. The backlog engine will redistribute the highest priority items.",
                "level": "RED" if overdue >= 3 else "ORANGE",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    pending = dashboard["pending_count"]
    if pending:
        notifications.append(
            {
                "id": "daily_tasks",
                "type": "daily_task_reminder",
                "title": "Daily plan waiting",
                "body": f"{pending} task(s) remain for today. Next action: {dashboard['recommended_next_action']}",
                "level": "YELLOW",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    if dashboard["next_exam_countdown"]:
        next_exam = dashboard["next_exam_countdown"]
        notifications.append(
            {
                "id": "exam_countdown",
                "type": "exam_countdown",
                "title": f"{next_exam['name']} countdown",
                "body": f"{next_exam['days_left']} day(s) left until {next_exam['exam_date']}.",
                "level": "RED" if next_exam["days_left"] <= 21 else "GREEN",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    weekly = build_life_os_weekly_review(db, user_id, today)
    notifications.append(
        {
            "id": "weekly_review",
            "type": "weekly_review",
            "title": "AI weekly review ready",
            "body": weekly["summary"],
            "level": "GREEN" if weekly["completion_rate"] >= 70 else "ORANGE",
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    return notifications


def build_life_os_analytics(db: Session, user_id: int) -> dict:
    today = date.today()
    build_live_dashboard(db, user_id)
    logs = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        update_productivity_log(db, user_id, day)
        log = db.scalar(select(ProductivityLog).where(ProductivityLog.user_id == user_id, ProductivityLog.log_date == day))
        logs.append(
            {
                "date": day.isoformat(),
                "completion": round(log.completed_tasks / max(log.completed_tasks + log.pending_tasks, 1) * 100, 1) if log else 0,
                "productivity_score": log.productivity_score if log else 0,
                "focus_minutes": log.focus_minutes if log else 0,
            }
        )
    db.commit()
    dashboard = build_live_dashboard(db, user_id)
    return {
        "study_hours_graph": [{"date": item["date"], "hours": round(item["focus_minutes"] / 60, 2)} for item in logs],
        "completion_trend": [{"date": item["date"], "completion": item["completion"]} for item in logs],
        "streak_graph": [{"date": item["date"], "streak": dashboard["current_streak"] if item["date"] == today.isoformat() else 0} for item in logs],
        "topic_progress_heatmap": dashboard["weak_topics"],
        "exam_readiness": dashboard["exam_readiness"],
        "productivity_trend": [{"date": item["date"], "score": item["productivity_score"]} for item in logs],
    }


def build_life_os_settings(db: Session, user_id: int) -> dict:
    ensure_exam_catalog(db, user_id)
    plans = db.scalars(select(StudyPlan).where(StudyPlan.user_id == user_id)).all()
    exams = {exam.id: exam.name for exam in db.scalars(select(Exam)).all()}
    travel = get_travel_settings(db, user_id)
    return {
        "selected_exams": [
            {"exam_id": plan.exam_id, "exam_name": exams.get(plan.exam_id, "Exam"), "active": plan.active, "available_hours_per_day": plan.available_hours_per_day}
            for plan in plans
        ],
        "travel_mode": {
            "enabled": travel.enabled,
            "allow_mock_tests": travel.allow_mock_tests,
            "daily_minutes": travel.daily_minutes,
            "notes": travel.notes,
        },
        "notification_preferences": {
            "daily_task_reminders": True,
            "overdue_alerts": True,
            "exam_countdown_alerts": True,
            "weekly_review_email": True,
        },
    }


def build_monitoring_overview(db: Session, user_id: int) -> dict:
    today = date.today()
    dashboard = build_live_dashboard(db, user_id)
    goals = db.scalars(select(Goal).where(Goal.user_id == user_id)).all()
    milestones = db.scalars(select(Milestone).join(Goal).where(Goal.user_id == user_id)).all()
    life_tasks = db.scalars(select(LifeTask).where(LifeTask.user_id == user_id)).all()
    overdue_life_tasks = [task for task in life_tasks if task.due_date and task.due_date < today and task.status != TaskStatus.COMPLETED]
    upcoming_deadlines = [
        {
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "status": task.status.value,
        }
        for task in sorted([task for task in life_tasks if task.due_date and task.status != TaskStatus.COMPLETED], key=lambda item: item.due_date)[:6]
    ]
    active_goals = [goal for goal in goals if goal.status == GoalStatus.ACTIVE]
    completed_milestones = [milestone for milestone in milestones if milestone.completed]
    return {
        "today_completed_tasks": dashboard["completed_count"],
        "today_pending_tasks": dashboard["pending_count"],
        "missed_tasks": dashboard["overdue_count"] + len(overdue_life_tasks),
        "habit_completion": dashboard["habit_completion_rate"],
        "study_hours": round(dashboard["focus_minutes_today"] / 60, 2),
        "focus_minutes": dashboard["focus_minutes_today"],
        "productivity_score": dashboard["productivity_score"],
        "streak": dashboard["current_streak"],
        "weekly_trend": build_life_os_analytics(db, user_id)["completion_trend"],
        "upcoming_deadlines": upcoming_deadlines,
        "exam_countdown": dashboard["next_exam_countdown"],
        "active_goals": len(active_goals),
        "goal_progress": round(len(completed_milestones) / max(len(milestones), 1) * 100, 1) if milestones else 0,
        "recommended_next_action": dashboard["recommended_next_action"],
    }


def build_monitoring_daily(db: Session, user_id: int, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    tasks = generate_daily_tasks(db, user_id, target_date)
    update_productivity_log(db, user_id, target_date)
    db.commit()
    log = db.scalar(select(ProductivityLog).where(ProductivityLog.user_id == user_id, ProductivityLog.log_date == target_date))
    habits = db.scalars(select(Habit).where(Habit.user_id == user_id)).all()
    completed_habits = db.scalars(select(HabitLog).join(Habit).where(Habit.user_id == user_id, HabitLog.log_date == target_date, HabitLog.completed.is_(True))).all()
    return {
        "date": target_date.isoformat(),
        "tasks": [_task_payload(db, task) for task in tasks],
        "completed_tasks": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
        "pending_tasks": sum(1 for task in tasks if task.status in {TaskStatus.PENDING, TaskStatus.ACTIVE}),
        "overdue_tasks": log.overdue_tasks if log else 0,
        "habit_completion": round(len(completed_habits) / max(len(habits), 1) * 100, 1) if habits else 0,
        "focus_minutes": log.focus_minutes if log else 0,
        "productivity_score": log.productivity_score if log else 0,
    }


def build_monitoring_weekly(db: Session, user_id: int, week_end: date | None = None) -> dict:
    week_end = week_end or date.today()
    week_start = week_end - timedelta(days=6)
    days = [build_monitoring_daily(db, user_id, week_start + timedelta(days=offset)) for offset in range(7)]
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days,
        "completed_tasks": sum(day["completed_tasks"] for day in days),
        "pending_tasks": sum(day["pending_tasks"] for day in days),
        "focus_minutes": sum(day["focus_minutes"] for day in days),
        "average_productivity_score": round(sum(day["productivity_score"] for day in days) / max(len(days), 1), 1),
    }


def _task_mix(days_left: int, travel_enabled: bool, allow_mock_tests: bool) -> list[StudyTaskType]:
    if travel_enabled:
        mix = [StudyTaskType.REVISION, StudyTaskType.FORMULA_REVIEW, StudyTaskType.READING]
        return mix + ([StudyTaskType.MOCK] if allow_mock_tests and days_left < 30 else [])
    if days_left < 21:
        return [StudyTaskType.MOCK, StudyTaskType.ANALYSIS, StudyTaskType.PYQ, StudyTaskType.REVISION]
    if days_left < 60:
        return [StudyTaskType.PYQ, StudyTaskType.PRACTICE, StudyTaskType.REVISION, StudyTaskType.MOCK]
    return [StudyTaskType.CONCEPT, StudyTaskType.PRACTICE, StudyTaskType.REVISION]


def _task_title(exam: Exam, topic: SyllabusTopic, task_type: StudyTaskType) -> str:
    labels = {
        StudyTaskType.CONCEPT: "Concept build",
        StudyTaskType.PRACTICE: "Practice set",
        StudyTaskType.REVISION: "Revision",
        StudyTaskType.MOCK: "Mock test",
        StudyTaskType.PYQ: "PYQ drill",
        StudyTaskType.FORMULA_REVIEW: "Formula review",
        StudyTaskType.READING: "Reading pass",
        StudyTaskType.ANALYSIS: "Mock analysis",
    }
    return f"{exam.name}: {labels[task_type]} - {topic.name}"


def _task_minutes(task_type: StudyTaskType, travel_enabled: bool) -> int:
    if travel_enabled:
        return 25 if task_type != StudyTaskType.MOCK else 60
    return {StudyTaskType.MOCK: 120, StudyTaskType.ANALYSIS: 45, StudyTaskType.PYQ: 60, StudyTaskType.PRACTICE: 60}.get(task_type, 45)


def _task_reason(days_left: int, topic: SyllabusTopic, travel_enabled: bool) -> str:
    if travel_enabled:
        return "Travel mode is on, so this is a lightweight task."
    if days_left < 45:
        return f"Exam is near and {topic.name} still needs reinforcement."
    return f"Selected because progress is {topic.progress_percent:.0f}% and weak score is {topic.weak_score:.0f}."


def _ensure_calendar_event_for_task(db: Session, user_id: int, task: GeneratedDailyTask, order_index: int) -> None:
    if db.scalar(select(CalendarEvent).where(CalendarEvent.user_id == user_id, CalendarEvent.generated_task_id == task.id)):
        return
    start_hour = 7 + ((order_index - 1) * 2)
    start_at = datetime.combine(task.task_date, time(hour=min(start_hour, 21), minute=0))
    end_at = start_at + timedelta(minutes=task.estimated_minutes)
    db.add(CalendarEvent(user_id=user_id, generated_task_id=task.id, title=task.title, start_at=start_at, end_at=end_at, event_type="generated_study"))


def _event_payload(event: CalendarEvent) -> dict:
    return {
        "id": event.id,
        "generated_task_id": event.generated_task_id,
        "title": event.title,
        "description": event.description,
        "start_at": event.start_at.isoformat(),
        "end_at": event.end_at.isoformat(),
        "event_type": event.event_type,
        "completed": event.completed,
    }


def _task_payload(db: Session, task: GeneratedDailyTask | None) -> dict:
    if task is None:
        return {}
    topic = db.scalar(select(SyllabusTopic).where(SyllabusTopic.id == task.topic_id)) if task.topic_id else None
    exam = db.scalar(select(Exam).where(Exam.id == task.exam_id)) if task.exam_id else None
    return {
        "id": task.id,
        "exam_id": task.exam_id,
        "exam_name": exam.name if exam else None,
        "topic_id": task.topic_id,
        "topic_name": topic.name if topic else None,
        "task_date": task.task_date.isoformat(),
        "title": task.title,
        "task_type": task.task_type.value,
        "status": task.status.value,
        "estimated_minutes": task.estimated_minutes,
        "priority": task.priority,
        "generated_reason": task.generated_reason,
    }


def task_payload(db: Session, task: GeneratedDailyTask | None) -> dict:
    return _task_payload(db, task)


def _focus_minutes_week(db: Session, user_id: int, today: date) -> int:
    week_start = today - timedelta(days=today.weekday())
    return int(db.scalar(select(func.coalesce(func.sum(FocusSession.duration_minutes), 0)).where(FocusSession.user_id == user_id, FocusSession.start_time >= datetime.combine(week_start, time.min))) or 0)
