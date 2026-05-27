from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re

import requests
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    CalendarEvent,
    DailyCheckIn,
    DistractionLog,
    Exam,
    ExamDate,
    ExamDateStatus,
    FocusSession,
    GeneratedDailyTask,
    GeneratedTaskLog,
    Goal,
    GoalStatus,
    GymLog,
    Habit,
    HabitLog,
    LifeTask,
    Milestone,
    MockScore,
    ProductivityLog,
    SleepLog,
    StudyPlan,
    StudyTaskType,
    SyllabusSubject,
    SyllabusTopic,
    TaskStatus,
    TravelModeSettings,
)
from app.planner_engine import (
    ExamPlanningInput,
    TopicPlanningInput,
    calculate_backlog_pressure,
    calculate_daily_capacity,
    generate_dynamic_day_plan,
)

PLANNER_START = date(2026, 6, 1)
PLANNER_END = date(2027, 6, 1)
PLANNER_TOTAL_DAYS = (PLANNER_END - PLANNER_START).days + 1
DISTRACTION_LIMIT_MINUTES = 60
CHECKIN_REQUIRED_FIELDS = (
    "wake_up_time",
    "sleep_time",
    "study_hours_completed",
    "mood_score",
    "energy_score",
    "todays_win",
    "todays_failure",
)

BACKEND_MODULES = [
    "FastAPI",
    "Express",
    "APIs",
    "auth",
    "PostgreSQL",
    "Redis",
    "Docker",
    "CI/CD",
    "deployment",
    "system design",
]

LLM_MODULES = [
    "Python AI",
    "prompt engineering",
    "embeddings",
    "vector DB",
    "RAG",
    "agents",
    "tool calling",
    "memory",
    "evals",
    "deployment",
]


OFFICIAL_EXAM_SOURCES = {
    "CAT": "https://iimcat.ac.in/",
    "GATE_DA": "https://gate2026.iitg.ac.in/",
    "GATE_ME": "https://gate2026.iitg.ac.in/",
    "JAM_MA": "https://jam2026.iitb.ac.in/",
    "JAM_PH": "https://jam2026.iitb.ac.in/",
}


EXAM_CATALOG = {
    "CAT": {
        "name": "CAT",
        "date": date(2026, 11, 29),
        "status": ExamDateStatus.TENTATIVE,
        "description": "Common Admission Test preparation plan.",
        "subjects": {
            "VARC": ["Reading comprehension", "Para summary", "Para jumbles", "Odd sentence", "Vocabulary in context", "Critical reasoning"],
            "LRDI": ["Arrangements", "Games and tournaments", "Routes and networks", "Tables and charts", "Set theory", "Logical caselets"],
            "Quant": ["Arithmetic", "Algebra", "Geometry", "Number systems", "Modern math", "Mensuration"],
        },
    },
    "GATE_DA": {
        "name": "GATE DA",
        "date": date(2027, 2, 15),
        "status": ExamDateStatus.TENTATIVE,
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
    "GATE_ME": {
        "name": "GATE Mechanical",
        "date": date(2027, 2, 14),
        "status": ExamDateStatus.TENTATIVE,
        "description": "GATE Mechanical Engineering preparation plan.",
        "subjects": {
            "Engineering Mathematics": ["Linear algebra", "Calculus", "Differential equations", "Complex variables", "Probability", "Numerical methods"],
            "Applied Mechanics": ["Engineering mechanics", "Strength of materials", "Theory of machines", "Vibrations", "Machine design"],
            "Fluid/Thermal": ["Fluid mechanics", "Heat transfer", "Thermodynamics", "IC engines", "Refrigeration", "Turbomachinery"],
            "Materials/Manufacturing/Industrial": ["Materials", "Casting", "Metal forming", "Machining", "Metrology", "Operations research"],
        },
    },
    "JAM_MA": {
        "name": "JAM Mathematics",
        "date": date(2027, 2, 15),
        "status": ExamDateStatus.TENTATIVE,
        "description": "IIT JAM Mathematics preparation plan.",
        "subjects": {
            "Real Analysis": ["Sequences", "Series", "Continuity", "Differentiability", "Riemann integration", "Metric spaces"],
            "Multivariable Calculus": ["Partial derivatives", "Multiple integrals", "Vector calculus", "Maxima minima", "Jacobians"],
            "Differential Equations": ["First order ODE", "Higher order ODE", "Power series solutions", "Systems of ODE"],
            "Linear Algebra": ["Matrices", "Vector spaces", "Linear transformations", "Eigenvalues", "Inner product spaces"],
            "Algebra": ["Groups", "Subgroups", "Cyclic groups", "Rings", "Fields", "Polynomials"],
        },
    },
    "JAM_PH": {
        "name": "JAM Physics",
        "date": date(2027, 2, 15),
        "status": ExamDateStatus.TENTATIVE,
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


_catalog_ensured_users = set()
_active_syllabus_topics_cache = None
_travel_settings_cache = {}
_exam_cache = {}
_study_plans_cache = {}
_bulk_reset_mode = False


def planner_not_started(today: date | None = None) -> bool:
    return (today or date.today()) < PLANNER_START


def waiting_for_planner_start(today: date | None = None) -> dict:
    current = today or date.today()
    days_left = max((PLANNER_START - current).days, 0)
    return {
        "status": "waiting" if days_left else "active",
        "locked": days_left > 0,
        "today": current.isoformat(),
        "planner_start_date": PLANNER_START.isoformat(),
        "days_until_start": days_left,
        "message": f"Planner is locked until {PLANNER_START.isoformat()}. No daily tasks or backlog are created before the start date."
        if days_left
        else "Planner is active.",
    }


def clear_life_os_caches() -> None:
    global _active_syllabus_topics_cache, _travel_settings_cache, _catalog_ensured_users, _exam_cache, _study_plans_cache, _bulk_reset_mode
    _active_syllabus_topics_cache = None
    _travel_settings_cache.clear()
    _catalog_ensured_users.clear()
    _exam_cache.clear()
    _study_plans_cache.clear()
    _bulk_reset_mode = False


def ensure_exam_catalog(db: Session, user_id: int | None = None) -> None:
    if user_id and user_id in _catalog_ensured_users:
        return
    for legacy_exam in db.scalars(select(Exam).where(Exam.code.notin_(list(EXAM_CATALOG.keys())))).all():
        legacy_exam.active = False
        db.add(legacy_exam)
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
            priority = 5 if code in {"CAT", "GATE_DA"} else 3
            db.add(StudyPlan(user_id=user_id, exam_id=exam.id, active=True, available_hours_per_day=4.0, priority=priority, start_date=PLANNER_START, end_date=PLANNER_END))

    if user_id and not db.scalar(select(TravelModeSettings).where(TravelModeSettings.user_id == user_id)):
        db.add(TravelModeSettings(user_id=user_id))
    db.commit()
    global _active_syllabus_topics_cache
    _active_syllabus_topics_cache = None
    if user_id:
        _catalog_ensured_users.add(user_id)


def get_travel_settings(db: Session, user_id: int) -> TravelModeSettings:
    settings = db.scalar(select(TravelModeSettings).where(TravelModeSettings.user_id == user_id))
    if not settings:
        settings = TravelModeSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def planner_date(target_date: date | None = None) -> date:
    value = target_date or date.today()
    if value < PLANNER_START:
        return PLANNER_START
    if value > PLANNER_END:
        return PLANNER_END
    return value


def next_planner_date(target_date: date | None = None) -> date:
    return min(planner_date(target_date) + timedelta(days=1), PLANNER_END)


def travel_mode_active(settings: TravelModeSettings, target_date: date) -> bool:
    if not settings.enabled:
        return False
    if settings.start_date and target_date < settings.start_date:
        return False
    if settings.end_date and target_date > settings.end_date:
        return False
    return True


def _weighted_available_hours(plans: list[StudyPlan]) -> float:
    if not plans:
        return 2.0
    weighted_hours = sum(plan.available_hours_per_day * max(plan.priority, 1) for plan in plans)
    total_priority = sum(max(plan.priority, 1) for plan in plans)
    return max(0.75, weighted_hours / max(total_priority, 1))


def refresh_exam_dates(db: Session) -> list[ExamDate]:
    ensure_exam_catalog(db)
    refreshed: list[ExamDate] = []
    for exam in db.scalars(select(Exam).where(Exam.active.is_(True))).all():
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
        r"(\d{1,2})\s+(February|November)\s+(2026|2027)",
        r"(February|November)\s+(\d{1,2}),?\s+(2026|2027)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, compact, flags=re.IGNORECASE):
            groups = match.groups()
            if groups[0].isdigit():
                day = int(groups[0])
                month_name = groups[1]
                year = int(groups[2])
            else:
                month_name = groups[0]
                day = int(groups[1])
                year = int(groups[2])
            month = 11 if month_name.lower() == "november" else 2
            found = date(year, month, day)
            if 1 <= day <= 31 and PLANNER_START <= found <= PLANNER_END:
                return found
    return None


def generate_daily_tasks(db: Session, user_id: int, target_date: date | None = None, force: bool = False) -> list[GeneratedDailyTask]:
    ensure_exam_catalog(db, user_id)
    if planner_not_started():
        return []
    target_date = target_date or planner_date()
    if target_date < PLANNER_START or target_date > PLANNER_END:
        return []
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
    in_travel = travel_mode_active(travel, target_date)
    plans = db.scalars(
        select(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.active.is_(True),
            StudyPlan.start_date <= target_date,
            StudyPlan.end_date >= target_date,
        )
    ).all()
    comeback = comeback_mode_summary(db, user_id, target_date)
    available_hours = _weighted_available_hours(plans)
    overdue_count = db.scalar(
        select(func.count(GeneratedDailyTask.id)).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < target_date,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE]),
        )
    ) or 0
    dynamic_exam_inputs: list[ExamPlanningInput] = []
    exams_by_id: dict[int, Exam] = {}
    topics_by_id: dict[int, SyllabusTopic] = {}
    for plan in plans:
        exam = db.scalar(select(Exam).where(Exam.id == plan.exam_id).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics)))
        if not exam:
            continue
        exams_by_id[exam.id] = exam
        exam_date = min((d.exam_date for d in exam.dates), default=target_date + timedelta(days=180))
        topic_inputs = []
        for subject in exam.subjects:
            for topic in subject.topics:
                if topic.progress_percent >= 100:
                    continue
                topics_by_id[topic.id] = topic
                topic_inputs.append(
                    TopicPlanningInput(
                        topic_id=topic.id,
                        progress_percent=topic.progress_percent,
                        weak_score=topic.weak_score,
                        difficulty=topic.difficulty,
                        estimated_hours=topic.estimated_hours,
                        subject_weight=subject.weight,
                    )
                )
        dynamic_exam_inputs.append(
            ExamPlanningInput(
                exam_id=exam.id,
                priority=plan.priority,
                exam_date=exam_date,
                topics=topic_inputs,
            )
        )

    dynamic_specs = generate_dynamic_day_plan(
        target_date=target_date,
        exams=dynamic_exam_inputs,
        available_study_hours=available_hours,
        travel_mode=in_travel,
        comeback_mode=comeback["active"],
        backlog_tasks=overdue_count,
        travel_daily_minutes=travel.daily_minutes,
    )
    daily_capacity = calculate_daily_capacity(available_hours, travel_mode=in_travel, comeback_mode=comeback["active"], travel_daily_minutes=travel.daily_minutes)
    backlog_extra_minutes = calculate_backlog_pressure(overdue_count, daily_capacity)
    carry_forward_missed_tasks(db, user_id, target_date, in_travel, max_extra_minutes=backlog_extra_minutes)
    created: list[GeneratedDailyTask] = []
    max_minutes = sum(spec.estimated_minutes for spec in dynamic_specs)
    if not max_minutes:
        max_minutes = 90 if in_travel else 160 if comeback["active"] else 220
    used_minutes = 0
    for spec in dynamic_specs:
        exam = exams_by_id.get(spec.exam_id)
        topic = topics_by_id.get(spec.topic_id)
        if not exam or not topic:
            continue
        task_type = StudyTaskType(spec.task_type)
        title = _task_title(exam, topic, task_type)
        if _bulk_reset_mode:
            if any(t.title == title and t.task_type == task_type for t in created):
                continue
        else:
            if db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date, GeneratedDailyTask.title == title, GeneratedDailyTask.task_type == task_type)):
                continue
        task = GeneratedDailyTask(
            user_id=user_id,
            exam_id=exam.id,
            topic_id=topic.id,
            task_date=target_date,
            title=title,
            task_type=task_type,
            estimated_minutes=spec.estimated_minutes,
            priority=max(1, min(10, round(spec.priority_score / 20))),
            generated_reason=spec.priority_reason,
        )
        db.add(task)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date).order_by(GeneratedDailyTask.priority.desc(), GeneratedDailyTask.id)).all()
        created.append(task)
        used_minutes += spec.estimated_minutes
        _ensure_calendar_event_for_task(db, user_id, task, len(created))

    for learning_task in _learning_task_candidates(db, user_id, target_date, len(created)):
        if used_minutes + learning_task["minutes"] > max_minutes:
            break
        if db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date, GeneratedDailyTask.title == learning_task["title"], GeneratedDailyTask.task_type == learning_task["task_type"])):
            continue
        task = GeneratedDailyTask(
            user_id=user_id,
            task_date=target_date,
            title=learning_task["title"],
            task_type=learning_task["task_type"],
            estimated_minutes=learning_task["minutes"],
            priority=learning_task["priority"],
            generated_reason=learning_task["reason"],
        )
        db.add(task)
        db.flush()
        created.append(task)
        used_minutes += learning_task["minutes"]
        _ensure_calendar_event_for_task(db, user_id, task, len(created))

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


def _learning_task_candidates(db: Session, user_id: int, target_date: date, existing_count: int) -> list[dict]:
    roadmaps = build_learning_roadmaps(db, user_id)
    candidates: list[dict] = []
    for track_key, label, task_type in (("backend", "Backend", StudyTaskType.PRACTICE), ("llm_agentic_ai", "LLM / Agentic AI", StudyTaskType.READING)):
        weak_modules = roadmaps[track_key]["weak_modules"]
        module = weak_modules[(target_date.toordinal() + existing_count) % max(len(weak_modules), 1)] if weak_modules else roadmaps[track_key]["modules"][0]["name"]
        candidates.append(
            {
                "title": f"{label}: {module} accountability block",
                "task_type": task_type,
                "minutes": 45,
                "priority": 4,
                "reason": f"Dynamic {label} roadmap block based on current weak modules and project readiness.",
            }
        )
    return candidates


def carry_forward_missed_tasks(db: Session, user_id: int, target_date: date, travel_enabled: bool, max_extra_minutes: int | None = None) -> None:
    if target_date <= PLANNER_START:
        return
    missed = db.scalars(
        select(GeneratedDailyTask).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < target_date,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE]),
        ).order_by(GeneratedDailyTask.task_date, GeneratedDailyTask.priority.desc()).limit(3)
    ).all()
    carried_minutes = 0
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
        if max_extra_minutes is not None and carried_minutes + minutes > max_extra_minutes:
            continue
        is_duplicate = False
        if _bulk_reset_mode:
            for obj in db.new:
                if isinstance(obj, GeneratedDailyTask) and obj.user_id == user_id and obj.task_date == target_date and obj.title == title:
                    is_duplicate = True
                    break
        else:
            if db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date, GeneratedDailyTask.title == title)):
                is_duplicate = True
        if not is_duplicate:
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
            carried_minutes += minutes
            _ensure_calendar_event_for_task(db, user_id, carried, 1)


def complete_generated_task(db: Session, user_id: int, task_id: int, status: TaskStatus, minutes_spent: int = 0, notes: str | None = None) -> GeneratedDailyTask | None:
    task = db.scalar(select(GeneratedDailyTask).where(GeneratedDailyTask.id == task_id, GeneratedDailyTask.user_id == user_id))
    if not task:
        return None
    task.status = status
    task.completed_at = datetime.utcnow() if status == TaskStatus.COMPLETED else None
    db.add(task)
    db.add(GeneratedTaskLog(user_id=user_id, task_id=task.id, status=status, minutes_spent=minutes_spent, notes=notes))
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
    overdue = db.scalar(
        select(func.count(GeneratedDailyTask.id)).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < target_date,
            GeneratedDailyTask.status != TaskStatus.COMPLETED,
        )
    ) or 0
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


def comeback_mode_summary(db: Session, user_id: int, target_date: date | None = None) -> dict:
    if planner_not_started(target_date):
        waiting = waiting_for_planner_start(target_date)
        return {
            "active": False,
            "date": waiting["today"],
            "backlog_tasks": 0,
            "weak_topic_count": 0,
            "daily_score_warning": False,
            "bad_days": 0,
            "missed_checkins": 0,
            "mock_score_drop": False,
            "seven_day_protocol": [],
            "recovery_plan": [],
            "warning": waiting["message"],
        }
    target_date = planner_date(target_date)
    overdue = db.scalar(
        select(func.count(GeneratedDailyTask.id)).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < target_date,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE]),
        )
    ) or 0
    topics = db.scalars(
        select(SyllabusTopic)
        .join(SyllabusSubject)
        .join(Exam)
        .where(Exam.active.is_(True))
        .options(selectinload(SyllabusTopic.subject))
    ).all()
    high_backlog = [topic for topic in topics if topic.progress_percent < 55 or topic.weak_score >= 65]
    recent_days = [target_date - timedelta(days=offset) for offset in range(0, 7)]
    recent_scores = [_accountability_score_for_day(db, user_id, day) for day in recent_days]
    bad_days = sum(1 for score in recent_scores[:3] if score < 70)
    missed_checkins = sum(1 for day in recent_days if not _checkin_completed(_daily_checkin_for_day(db, user_id, day), day))
    mock_drop = _mock_score_drop(db, user_id)
    active = overdue >= 5 or len(high_backlog) >= 8 or bad_days >= 3 or recent_scores[0] < 70 or missed_checkins >= 2 or mock_drop
    priority_topics = sorted(high_backlog, key=lambda topic: (-topic.subject.weight, -topic.weak_score, topic.progress_percent, -topic.difficulty))[:8]
    protocol = [
        "Day 1: clear only the highest-priority overdue block and submit the full check-in.",
        "Day 2: one weak-topic revision block plus one short practice set.",
        "Day 3: protect sleep and keep distractions below 45 minutes.",
        "Day 4: take or analyze one mock/PYQ set for the nearest exam.",
        "Day 5: backend or LLM weak-module block, capped at 45 minutes.",
        "Day 6: redistribute backlog and finish two small wins.",
        "Day 7: review score trend and choose aggressive or recovery mode for next week.",
    ]
    return {
        "active": active,
        "date": target_date.isoformat(),
        "backlog_tasks": overdue,
        "weak_topic_count": len(high_backlog),
        "daily_score_warning": recent_scores[0] < 70 or overdue >= 5,
        "bad_days": bad_days,
        "missed_checkins": missed_checkins,
        "mock_score_drop": mock_drop,
        "seven_day_protocol": protocol if active else [],
        "recovery_plan": [
            {
                "topic_id": topic.id,
                "topic": topic.name,
                "progress": round(topic.progress_percent, 1),
                "weak_score": round(topic.weak_score, 1),
                "action": "Revision plus one focused practice block",
            }
            for topic in priority_topics
        ],
        "warning": "Comeback mode is active. Keep tasks shorter, finish weak/high-weightage topics first, and complete every check-in." if active else None,
    }


def _accountability_score_for_day(db: Session, user_id: int, target_date: date) -> int:
    tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date)).all()
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    checkin = _daily_checkin_for_day(db, user_id, target_date)
    focus = max(_focus_minutes_for_day(db, user_id, target_date), _study_minutes_for_day(db, user_id, target_date))
    return _discipline_score(
        completed,
        len(tasks),
        focus,
        _sleep_hours_for_day(db, user_id, target_date),
        _distraction_minutes_for_day(db, user_id, target_date),
        _gym_done_for_day(db, user_id, target_date),
        not _checkin_completed(checkin, target_date),
    )


def _mock_score_drop(db: Session, user_id: int) -> bool:
    scores = db.scalars(select(MockScore).where(MockScore.user_id == user_id).order_by(MockScore.taken_on.desc(), MockScore.id.desc()).limit(2)).all()
    if len(scores) < 2:
        return False
    latest = scores[0].score / max(scores[0].max_score, 1)
    previous = scores[1].score / max(scores[1].max_score, 1)
    return latest < previous - 0.05


def _waiting_live_dashboard(db: Session, user_id: int) -> dict:
    ensure_exam_catalog(db, user_id)
    waiting = waiting_for_planner_start()
    exams, weak_topics = _realtime_exam_cards(db, PLANNER_START)
    next_exam = None
    if exams:
        nearest = min(exams, key=lambda exam: exam["days_left"])
        next_exam = {"name": nearest["name"], "exam_date": nearest["exam_date"], "days_left": nearest["days_left"]}
    planner_window = verify_planner_window(db, user_id)
    return {
        "planner_start_date": PLANNER_START.isoformat(),
        "planner_end_date": PLANNER_END.isoformat(),
        "planner_status": waiting,
        "today_tasks": [],
        "completed_count": 0,
        "pending_count": 0,
        "overdue_count": 0,
        "active_task": None,
        "current_streak": 0,
        "exam_readiness": [
            {
                "exam_id": exam["id"],
                "name": exam["name"],
                "exam_date": exam["exam_date"],
                "days_left": exam["days_left"],
                "syllabus_completion": exam["syllabus_completion"],
                "readiness_score": exam["readiness_score"],
            }
            for exam in exams
        ],
        "syllabus_completion": round(sum(exam["syllabus_completion"] for exam in exams) / max(len(exams), 1), 1),
        "focus_minutes_today": 0,
        "focus_minutes_week": 0,
        "calendar_events_today": [],
        "next_exam_countdown": next_exam,
        "weak_topics": weak_topics[:8],
        "recommended_next_action": waiting["message"],
        "productivity_score": 0,
        "habit_completion_rate": 0,
        "daily_checkin": None,
        "daily_checkin_completed": True,
        "accountability_warnings": [waiting["message"]],
        "travel_mode": False,
        "comeback_mode": comeback_mode_summary(db, user_id, date.fromisoformat(waiting["today"])),
        "planner_window": planner_window,
    }


def _waiting_realtime_dashboard(db: Session, user_id: int) -> dict:
    ensure_exam_catalog(db, user_id)
    waiting = waiting_for_planner_start()
    current = date.fromisoformat(waiting["today"])
    week_days = [current - timedelta(days=offset) for offset in range(6, -1, -1)]
    exams, weak_topics = _realtime_exam_cards(db, PLANNER_START)
    planner_window = verify_planner_window(db, user_id)
    empty_week = [
        {
            "date": day.isoformat(),
            "score": 0,
            "completed": 0,
            "total": 0,
            "completion": 0,
            "study_minutes": 0,
            "focus_minutes": 0,
            "sleep_hours": 0,
            "distraction_minutes": 0,
            "checkin_completed": True,
        }
        for day in week_days
    ]
    return {
        "today": {
            "date": current.isoformat(),
            "planner_start_date": PLANNER_START.isoformat(),
            "planner_end_date": PLANNER_END.isoformat(),
            "planner_status": waiting,
            "discipline_score": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "focus_minutes": 0,
            "gym_done": False,
            "sleep_hours": 0,
            "distraction_minutes": 0,
            "checkin_completed": True,
            "warnings": [waiting["message"]],
        },
        "weekly": {
            "average_score": 0,
            "study_minutes": [{"date": day["date"], "minutes": 0} for day in empty_week],
            "task_completion": [{"date": day["date"], "completion": 0, "completed": 0, "total": 0} for day in empty_week],
            "focus_minutes": [{"date": day["date"], "minutes": 0} for day in empty_week],
            "sleep_hours": [{"date": day["date"], "hours": 0, "score": 0} for day in empty_week],
            "distraction_minutes": [{"date": day["date"], "minutes": 0, "score": 0} for day in empty_week],
        },
        "exams": exams,
        "tasks": {"today": [], "overdue": [], "upcoming": []},
        "streak": {
            "current": 0,
            "best": 0,
            "calendar": [{"date": day["date"], "score": 0, "completed": False} for day in empty_week],
        },
        "recommendations": [waiting["message"]],
        "comeback": comeback_mode_summary(db, user_id, current),
        "planner_window": planner_window,
        "exam_war_room": build_exam_war_room(db, user_id),
        "learning": build_learning_roadmaps(db, user_id),
        "monthly_reality_check": build_monthly_reality_check(db, user_id, current),
        "accountability_coach": {
            "mode": "waiting",
            "questions": [],
            "suggested_missed_reason": "planner_locked_until_start",
            "tomorrow_intensity": "waiting",
        },
    }


def build_live_dashboard(db: Session, user_id: int) -> dict:
    if planner_not_started():
        return _waiting_live_dashboard(db, user_id)
    today = planner_date()
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
    exams = db.scalars(select(Exam).where(Exam.active.is_(True)).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics))).all()
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
    checkin_missing = not _checkin_completed(checkin, today)
    return {
        "planner_start_date": PLANNER_START.isoformat(),
        "planner_end_date": PLANNER_END.isoformat(),
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
        "daily_checkin_completed": not checkin_missing,
        "accountability_warnings": _realtime_warnings(log.productivity_score if log else 0, [], _sleep_hours_for_day(db, user_id, today), _distraction_minutes_for_day(db, user_id, today), checkin_missing),
        "travel_mode": travel_mode_active(get_travel_settings(db, user_id), today),
        "comeback_mode": comeback_mode_summary(db, user_id, today),
        "planner_window": verify_planner_window(db, user_id),
    }


def build_realtime_dashboard(db: Session, user_id: int, metrics_db: Session | None = None) -> dict:
    if planner_not_started():
        return _waiting_realtime_dashboard(db, user_id)
    today = planner_date()
    week_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    generate_daily_tasks(db, user_id, today)
    for day in week_days:
        update_productivity_log(db, user_id, day)
    db.commit()

    today_tasks = db.scalars(
        select(GeneratedDailyTask)
        .where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == today)
        .order_by(GeneratedDailyTask.priority.desc(), GeneratedDailyTask.id)
    ).all()
    overdue_tasks = db.scalars(
        select(GeneratedDailyTask)
        .where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < today,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE]),
        )
        .order_by(GeneratedDailyTask.task_date, GeneratedDailyTask.priority.desc())
        .limit(12)
    ).all()
    upcoming_tasks = db.scalars(
        select(GeneratedDailyTask)
        .where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date > today,
            GeneratedDailyTask.task_date <= today + timedelta(days=7),
        )
        .order_by(GeneratedDailyTask.task_date, GeneratedDailyTask.priority.desc())
        .limit(12)
    ).all()
    completed_tasks = sum(1 for task in today_tasks if task.status == TaskStatus.COMPLETED)
    total_tasks = len(today_tasks)
    checkin_today = _daily_checkin_for_day(db, user_id, today)
    checkin_missing = not _checkin_completed(checkin_today, today)
    focus_minutes_today = max(_focus_minutes_for_day(db, user_id, today), _study_minutes_for_day(db, user_id, today))
    sleep_hours_today = _sleep_hours_for_day(metrics_db, user_id, today)
    distraction_minutes_today = _distraction_minutes_for_day(metrics_db, user_id, today)
    gym_done = _gym_done_for_day(metrics_db, user_id, today)
    discipline_score = _discipline_score(completed_tasks, total_tasks, focus_minutes_today, sleep_hours_today, distraction_minutes_today, gym_done, checkin_missing)

    weekly = []
    for day in week_days:
        day_tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == day)).all()
        day_completed = sum(1 for task in day_tasks if task.status == TaskStatus.COMPLETED)
        day_checkin = _daily_checkin_for_day(db, user_id, day)
        day_focus = max(_focus_minutes_for_day(db, user_id, day), _study_minutes_for_day(db, user_id, day))
        day_sleep = _sleep_hours_for_day(metrics_db, user_id, day)
        day_distractions = _distraction_minutes_for_day(metrics_db, user_id, day)
        day_score = _discipline_score(day_completed, len(day_tasks), day_focus, day_sleep, day_distractions, _gym_done_for_day(metrics_db, user_id, day), not _checkin_completed(day_checkin, day))
        weekly.append(
            {
                "date": day.isoformat(),
                "score": day_score,
                "completed": day_completed,
                "total": len(day_tasks),
                "completion": round(day_completed / max(len(day_tasks), 1) * 100, 1),
                "study_minutes": day_focus,
                "focus_minutes": day_focus,
                "sleep_hours": day_sleep,
                "distraction_minutes": day_distractions,
                "checkin_completed": _checkin_completed(day_checkin, day),
            }
        )

    exams, weak_topics = _realtime_exam_cards(db, today)
    warnings = _realtime_warnings(discipline_score, overdue_tasks, sleep_hours_today, distraction_minutes_today, checkin_missing)
    recommendations = _realtime_recommendations(discipline_score, overdue_tasks, weak_topics, exams, sleep_hours_today, distraction_minutes_today)
    streak_calendar = _streak_calendar(weekly)
    planner_window = verify_planner_window(db, user_id)
    comeback = comeback_mode_summary(db, user_id, today)

    return {
        "today": {
            "date": today.isoformat(),
            "planner_start_date": PLANNER_START.isoformat(),
            "planner_end_date": PLANNER_END.isoformat(),
            "discipline_score": discipline_score,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "focus_minutes": focus_minutes_today,
            "gym_done": gym_done,
            "sleep_hours": sleep_hours_today,
            "distraction_minutes": distraction_minutes_today,
            "checkin_completed": not checkin_missing,
            "warnings": warnings,
        },
        "weekly": {
            "average_score": round(sum(day["score"] for day in weekly) / max(len(weekly), 1), 1),
            "study_minutes": [{"date": day["date"], "minutes": day["study_minutes"]} for day in weekly],
            "task_completion": [{"date": day["date"], "completion": day["completion"], "completed": day["completed"], "total": day["total"]} for day in weekly],
            "focus_minutes": [{"date": day["date"], "minutes": day["focus_minutes"]} for day in weekly],
            "sleep_hours": [{"date": day["date"], "hours": day["sleep_hours"], "score": day["score"]} for day in weekly],
            "distraction_minutes": [{"date": day["date"], "minutes": day["distraction_minutes"], "score": day["score"]} for day in weekly],
        },
        "exams": exams,
        "tasks": {
            "today": [_task_payload(db, task) for task in today_tasks],
            "overdue": [_task_payload(db, task) for task in overdue_tasks],
            "upcoming": [_task_payload(db, task) for task in upcoming_tasks],
        },
        "streak": {
            "current": _current_streak(db, user_id, today),
            "best": _best_streak(db, user_id, today),
            "calendar": streak_calendar,
        },
        "recommendations": recommendations,
        "comeback": comeback,
        "planner_window": planner_window,
        "exam_war_room": build_exam_war_room(db, user_id),
        "learning": build_learning_roadmaps(db, user_id),
        "monthly_reality_check": build_monthly_reality_check(db, user_id, today),
        "accountability_coach": build_accountability_coach(db, user_id, today),
    }


def _focus_minutes_for_day(db: Session, user_id: int, target_date: date) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_minutes), 0)).where(
                FocusSession.user_id == user_id,
                FocusSession.start_time >= datetime.combine(target_date, time.min),
                FocusSession.start_time <= datetime.combine(target_date, time.max),
            )
        )
        or 0
    )


def _sleep_hours_for_day(db: Session | None, user_id: int, target_date: date) -> float:
    if not db:
        return 0
    try:
        sleep_hours = round(float(db.scalar(select(func.coalesce(func.sum(SleepLog.hours), 0)).where(SleepLog.user_id == user_id, SleepLog.sleep_date == target_date)) or 0), 1)
        if sleep_hours:
            return sleep_hours
        checkin = _daily_checkin_for_day(db, user_id, target_date)
        return _sleep_hours_from_checkin(checkin)
    except SQLAlchemyError:
        db.rollback()
        return 0


def _distraction_minutes_for_day(db: Session | None, user_id: int, target_date: date) -> int:
    if not db:
        return 0
    try:
        tracked = int(db.scalar(select(func.coalesce(func.sum(DistractionLog.minutes), 0)).where(DistractionLog.user_id == user_id, DistractionLog.log_date == target_date)) or 0)
        checkin = _daily_checkin_for_day(db, user_id, target_date)
        return max(tracked, checkin.distraction_minutes if checkin else 0)
    except SQLAlchemyError:
        db.rollback()
        return 0


def _gym_done_for_day(db: Session | None, user_id: int, target_date: date) -> bool:
    if not db:
        return False
    try:
        gym_log_done = bool(db.scalar(select(func.count(GymLog.id)).where(GymLog.user_id == user_id, GymLog.log_date == target_date, GymLog.completed.is_(True))) or 0)
        checkin = _daily_checkin_for_day(db, user_id, target_date)
        return gym_log_done or bool(checkin and checkin.gym_completed)
    except SQLAlchemyError:
        db.rollback()
        return False


def _daily_checkin_for_day(db: Session | None, user_id: int, target_date: date) -> DailyCheckIn | None:
    if not db:
        return None
    return db.scalar(select(DailyCheckIn).where(DailyCheckIn.user_id == user_id, DailyCheckIn.log_date == target_date))


def _checkin_completed(checkin: DailyCheckIn | None, target_date: date) -> bool:
    if not checkin:
        return False
    required_values = [getattr(checkin, field, None) for field in CHECKIN_REQUIRED_FIELDS]
    has_required = all(value not in {None, ""} for value in required_values)
    if target_date.weekday() < 5:
        return has_required and checkin.gym_completed is not None
    return has_required


def _sleep_hours_from_checkin(checkin: DailyCheckIn | None) -> float:
    if not checkin or not checkin.wake_up_time or not checkin.sleep_time:
        return 0
    try:
        sleep_hour, sleep_minute = [int(part) for part in checkin.sleep_time.split(":")[:2]]
        wake_hour, wake_minute = [int(part) for part in checkin.wake_up_time.split(":")[:2]]
        sleep_minutes = sleep_hour * 60 + sleep_minute
        wake_minutes = wake_hour * 60 + wake_minute
        duration = wake_minutes - sleep_minutes
        if duration <= 0:
            duration += 24 * 60
        return round(duration / 60, 1)
    except (TypeError, ValueError):
        return 0


def _study_minutes_for_day(db: Session, user_id: int, target_date: date) -> int:
    checkin = _daily_checkin_for_day(db, user_id, target_date)
    if checkin and checkin.study_hours_completed:
        return int(checkin.study_hours_completed * 60)
    return _focus_minutes_for_day(db, user_id, target_date)


def _discipline_score(completed: int, total: int, focus_minutes: int, sleep_hours: float, distraction_minutes: int, gym_done: bool, checkin_missing: bool = False) -> int:
    completion_score = completed / max(total, 1) * 55
    focus_score = min(focus_minutes / 150, 1) * 25
    sleep_score = min(sleep_hours / 7, 1) * 10 if sleep_hours else 0
    gym_score = 5 if gym_done else 0
    distraction_penalty = min(distraction_minutes / 90, 1) * 15
    checkin_penalty = 15 if checkin_missing else 0
    return max(0, min(100, round(completion_score + focus_score + sleep_score + gym_score - distraction_penalty - checkin_penalty)))


def _realtime_exam_cards(db: Session, today: date) -> tuple[list[dict], list[dict]]:
    exams = db.scalars(select(Exam).where(Exam.active.is_(True)).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics))).all()
    cards = []
    weak_topics = []
    for exam in exams:
        topics = [topic for subject in exam.subjects for topic in subject.topics]
        completion = round(sum(topic.progress_percent for topic in topics) / max(len(topics), 1), 1)
        upcoming_dates = [item.exam_date for item in exam.dates if item.exam_date >= today]
        exam_date = min(upcoming_dates) if upcoming_dates else min((item.exam_date for item in exam.dates), default=today)
        days_left = max((exam_date - today).days, 0)
        readiness = round(min(100, completion * 0.72 + min(28, max(0, 120 - days_left) * 0.18)), 1)
        exam_weak_topics = [
            {"id": topic.id, "name": topic.name, "progress": round(topic.progress_percent, 1), "weak_score": round(topic.weak_score, 1), "exam": exam.name}
            for topic in sorted(topics, key=lambda item: (-item.weak_score, item.progress_percent, -item.difficulty))[:5]
            if topic.progress_percent < 90
        ]
        weak_topics.extend(exam_weak_topics)
        cards.append(
            {
                "id": exam.id,
                "name": exam.name,
                "exam_date": exam_date.isoformat(),
                "days_left": days_left,
                "syllabus_completion": completion,
                "readiness_score": readiness,
                "weak_topics": exam_weak_topics,
            }
        )
    return sorted(cards, key=lambda item: item["days_left"]), weak_topics


def _realtime_warnings(score: int, overdue_tasks: list[GeneratedDailyTask], sleep_hours: float, distraction_minutes: int, checkin_missing: bool) -> list[str]:
    warnings = []
    if checkin_missing:
        warnings.append("Daily check-in is missing: log sleep, study, gym, distractions, win, and failure.")
    if score < 70:
        warnings.append("Discipline score is below 70. Tomorrow will be adjusted toward recovery and higher completion.")
    if score < 50:
        warnings.append("Recovery mode recommended: discipline score is below 50.")
    if overdue_tasks:
        warnings.append(f"{len(overdue_tasks)} overdue task(s) need a lighter carry-forward plan.")
    if sleep_hours and sleep_hours < 6:
        warnings.append("Sleep is below the recovery threshold.")
    if distraction_minutes > DISTRACTION_LIMIT_MINUTES:
        warnings.append("Red distraction warning: phone/social/video time crossed the daily threshold.")
    return warnings


def _realtime_recommendations(score: int, overdue_tasks: list[GeneratedDailyTask], weak_topics: list[dict], exams: list[dict], sleep_hours: float, distraction_minutes: int) -> list[str]:
    recommendations = []
    if overdue_tasks:
        recommendations.append("Start with the highest-priority overdue block, capped at 45 minutes.")
    if weak_topics:
        recommendations.append(f"Schedule revision plus practice for {weak_topics[0]['name']}.")
    if exams and exams[0]["days_left"] <= 30:
        recommendations.append(f"Add one mock-test analysis block for {exams[0]['name']}.")
    if score < 60:
        recommendations.append("Use recovery mode today: fewer blocks, higher completion quality.")
    if sleep_hours and sleep_hours < 6:
        recommendations.append("Protect a sleep recovery window before adding more workload.")
    if distraction_minutes > 45:
        recommendations.append("Enable anti-distraction mode for the next focus session.")
    if not recommendations:
        recommendations.append("Keep the current plan: finish today's active block and log focus minutes.")
    return recommendations


def _streak_calendar(weekly: list[dict]) -> list[dict]:
    return [{"date": day["date"], "score": day["score"], "completed": day["completion"] >= 70 or day["score"] >= 70} for day in weekly]


def _current_streak(db: Session, user_id: int, today: date) -> int:
    streak = 0
    for offset in range(0, 30):
        day = today - timedelta(days=offset)
        tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == day)).all()
        completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        if tasks and completed / max(len(tasks), 1) >= 0.7:
            streak += 1
        elif offset == 0 and not tasks:
            continue
        else:
            break
    return streak


def _best_streak(db: Session, user_id: int, today: date) -> int:
    best = 0
    current = 0
    for offset in range(29, -1, -1):
        day = today - timedelta(days=offset)
        tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == day)).all()
        completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        if tasks and completed / max(len(tasks), 1) >= 0.7:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def build_life_os_weekly_review(db: Session, user_id: int, week_end: date | None = None) -> dict:
    if planner_not_started(week_end):
        waiting = waiting_for_planner_start(week_end)
        return {
            "week_start": waiting["today"],
            "week_end": waiting["today"],
            "summary": waiting["message"],
            "completed_tasks": 0,
            "missed_tasks": 0,
            "completion_rate": 0,
            "weak_topics": [],
            "next_week_plan": [],
            "recommended_action": waiting["message"],
        }
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
    missed = [task for task in tasks if task.status in {TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE, TaskStatus.SKIPPED} and PLANNER_START <= task.task_date < date.today()]
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
    if planner_not_started():
        waiting = waiting_for_planner_start()
        return [
            {
                "id": "planner_waiting",
                "type": "planner_waiting",
                "title": "Planner locked",
                "body": waiting["message"],
                "level": "GREEN",
                "created_at": datetime.utcnow().isoformat(),
            }
        ]
    today = planner_date()
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
    if dashboard["productivity_score"] < 60:
        notifications.append(
            {
                "id": "low_score_recovery",
                "type": "recovery",
                "title": "Recovery mode suggested",
                "body": "Productivity is below 60%. Use a lighter plan, clear overdue work first, and protect one deep-work block.",
                "level": "ORANGE" if dashboard["productivity_score"] >= 40 else "RED",
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
    today = planner_date()
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
    exams = {exam.id: exam.name for exam in db.scalars(select(Exam).where(Exam.active.is_(True))).all()}
    travel = get_travel_settings(db, user_id)
    return {
        "selected_exams": [
            {
                "exam_id": plan.exam_id,
                "exam_name": exams.get(plan.exam_id, "Exam"),
                "active": plan.active,
                "available_hours_per_day": plan.available_hours_per_day,
                "priority": plan.priority,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat(),
            }
            for plan in plans
        ],
        "travel_mode": {
            "enabled": travel.enabled,
            "start_date": travel.start_date.isoformat() if travel.start_date else None,
            "end_date": travel.end_date.isoformat() if travel.end_date else None,
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
    today = planner_date()
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
    target_date = planner_date(target_date)
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
    week_end = planner_date(week_end)
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


def build_exam_war_room(db: Session, user_id: int) -> list[dict]:
    today = planner_date()
    exams, _weak_topics = _realtime_exam_cards(db, today)
    war_room = []
    for exam in exams:
        mock_scores = db.scalars(select(MockScore).where(MockScore.user_id == user_id, MockScore.exam_id == exam["id"]).order_by(MockScore.taken_on.desc()).limit(3)).all()
        next_mock = today + timedelta(days=7 if exam["days_left"] > 30 else 3)
        syllabus_remaining = round(100 - exam["syllabus_completion"], 1)
        urgency = min(100, round((syllabus_remaining * 0.6) + max(0, 90 - exam["days_left"]) * 0.7 + len(exam["weak_topics"]) * 4, 1))
        war_room.append(
            {
                **exam,
                "syllabus_remaining": syllabus_remaining,
                "next_mock": min(next_mock, PLANNER_END).isoformat(),
                "urgency_score": urgency,
                "mock_trend": [
                    {
                        "date": score.taken_on.isoformat(),
                        "score_percent": round(score.score / max(score.max_score, 1) * 100, 1),
                    }
                    for score in reversed(mock_scores)
                ],
            }
        )
    return war_room


def build_learning_roadmaps(db: Session, user_id: int) -> dict:
    return {
        "backend": _learning_track(db, user_id, "backend", BACKEND_MODULES),
        "llm_agentic_ai": _learning_track(db, user_id, "llm_agentic_ai", LLM_MODULES),
    }


def _learning_track(db: Session, user_id: int, track: str, modules: list[str]) -> dict:
    life_tasks = db.scalars(select(LifeTask).where(LifeTask.user_id == user_id, LifeTask.title.ilike(f"%{track.replace('_', ' ')}%"))).all()
    generated = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.title.ilike(f"%{track.split('_')[0]}%"))).all()
    completed_titles = " ".join([task.title.lower() for task in life_tasks if task.status == TaskStatus.COMPLETED] + [task.title.lower() for task in generated if task.status == TaskStatus.COMPLETED])
    module_rows = []
    for index, module in enumerate(modules):
        mentions = completed_titles.count(module.lower())
        progress = min(100, mentions * 35)
        if not mentions and index < len(generated) % max(len(modules), 1):
            progress = 20
        module_rows.append(
            {
                "name": module,
                "progress": progress,
                "status": "ready" if progress >= 80 else "building" if progress >= 35 else "weak",
                "project": f"Ship one {module} proof project",
            }
        )
    completed = sum(item["progress"] for item in module_rows)
    readiness = round(completed / max(len(module_rows), 1), 1)
    return {
        "readiness": readiness,
        "completion": readiness,
        "modules": module_rows,
        "projects": [task.title for task in life_tasks[:5]],
        "weak_modules": [item["name"] for item in module_rows if item["status"] == "weak"][:5],
    }


def build_monthly_reality_check(db: Session, user_id: int, target_date: date | None = None) -> dict:
    today = planner_date(target_date)
    exams = build_exam_war_room(db, user_id)
    if not exams:
        return {"date": today.isoformat(), "exam_readiness": 0, "pace_enough": False, "projected_rank_readiness": "unknown", "backlog_danger": "unknown"}
    avg_readiness = round(sum(exam["readiness_score"] for exam in exams) / len(exams), 1)
    avg_remaining = round(sum(exam["syllabus_remaining"] for exam in exams) / len(exams), 1)
    nearest_days = min(exam["days_left"] for exam in exams)
    pace_enough = avg_readiness >= 65 or (nearest_days > 120 and avg_remaining < 55)
    danger = "red" if avg_remaining > 65 and nearest_days < 90 else "orange" if avg_remaining > 45 else "green"
    return {
        "date": today.isoformat(),
        "exam_readiness": avg_readiness,
        "pace_enough": pace_enough,
        "projected_rank_readiness": "competitive" if avg_readiness >= 75 else "borderline" if avg_readiness >= 55 else "not_ready",
        "backlog_danger": danger,
        "improvement_plan": [
            "Complete daily check-ins without gaps.",
            "Prioritize red weak topics before adding new syllabus.",
            "Take one mock or analysis block every week per active exam.",
        ],
    }


def build_accountability_coach(db: Session, user_id: int, target_date: date | None = None) -> dict:
    if planner_not_started(target_date):
        return {
            "mode": "waiting",
            "questions": [],
            "suggested_missed_reason": "planner_locked_until_start",
            "tomorrow_intensity": "waiting",
        }
    today = planner_date(target_date)
    overdue = db.scalars(
        select(GeneratedDailyTask)
        .where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date < today,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.OVERDUE, TaskStatus.SKIPPED]),
        )
        .order_by(GeneratedDailyTask.task_date.desc(), GeneratedDailyTask.priority.desc())
        .limit(5)
    ).all()
    score = _accountability_score_for_day(db, user_id, today)
    mode = "recovery" if score < 70 or overdue else "aggressive"
    return {
        "mode": mode,
        "questions": [
            "Why did you miss the highest-priority task?",
            "What blocked you: overload, distraction, emergency, travel, or intentional skip?",
            f"Should tomorrow be {mode} or do you want to override it?",
        ],
        "suggested_missed_reason": _suggest_missed_reason(db, user_id, today),
        "tomorrow_intensity": mode,
    }


def _suggest_missed_reason(db: Session, user_id: int, target_date: date) -> str:
    travel = travel_mode_active(get_travel_settings(db, user_id), target_date)
    if travel:
        return "travel"
    if _distraction_minutes_for_day(db, user_id, target_date) > DISTRACTION_LIMIT_MINUTES:
        return "distraction"
    tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target_date)).all()
    total_minutes = sum(task.estimated_minutes for task in tasks)
    if total_minutes > 300:
        return "overload"
    return "intentional skip"


def apply_emergency_mode(db: Session, user_id: int, target_date: date | None = None) -> dict:
    target = planner_date(target_date)
    tasks = db.scalars(select(GeneratedDailyTask).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date == target).order_by(GeneratedDailyTask.priority.desc(), GeneratedDailyTask.id)).all()
    kept = 0
    moved = 0
    for index, task in enumerate(tasks):
        if task.status == TaskStatus.COMPLETED:
            kept += 1
            continue
        if index < 2 or task.priority >= 8:
            task.estimated_minutes = min(task.estimated_minutes, 35)
            task.generated_reason = "Emergency mode: preserved as a momentum-critical task."
            kept += 1
        else:
            task.status = TaskStatus.SKIPPED
            task.generated_reason = "Emergency mode: moved out to protect momentum after a bad day."
            moved += 1
        db.add(task)
    db.commit()
    return {"date": target.isoformat(), "kept_tasks": kept, "moved_tasks": moved, "message": "Bad day mode applied. Finish only the preserved tasks and complete the check-in."}


def run_daily_accountability_cycle(db: Session, user_id: int, run_date: date | None = None) -> dict:
    if planner_not_started(run_date):
        waiting = waiting_for_planner_start(run_date)
        return {
            "today": waiting["today"],
            "tomorrow": PLANNER_START.isoformat(),
            "missed_checkin": False,
            "unfinished_marked_overdue": 0,
            "missed_reason": "planner_locked_until_start",
            "tomorrow_tasks": 0,
            "message": waiting["message"],
        }
    today = planner_date(run_date)
    tomorrow = next_planner_date(today)
    checkin = _daily_checkin_for_day(db, user_id, today)
    missed_checkin = not _checkin_completed(checkin, today)
    unfinished = db.scalars(
        select(GeneratedDailyTask).where(
            GeneratedDailyTask.user_id == user_id,
            GeneratedDailyTask.task_date >= PLANNER_START,
            GeneratedDailyTask.task_date <= today,
            GeneratedDailyTask.status.in_([TaskStatus.PENDING, TaskStatus.ACTIVE]),
        )
    ).all()
    reason = _suggest_missed_reason(db, user_id, today)
    for task in unfinished:
        task.status = TaskStatus.OVERDUE
        db.add(task)
        db.add(GeneratedTaskLog(user_id=user_id, task_id=task.id, status=TaskStatus.OVERDUE, minutes_spent=0, notes=f"missed_reason={reason}"))
    tomorrow_tasks = generate_daily_tasks(db, user_id, tomorrow, force=True)
    update_productivity_log(db, user_id, today)
    db.commit()
    return {
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "missed_checkin": missed_checkin,
        "unfinished_marked_overdue": len(unfinished),
        "missed_reason": reason,
        "tomorrow_tasks": len(tomorrow_tasks),
    }


def verify_planner_window(db: Session, user_id: int) -> dict:
    first_day = db.scalar(select(func.min(GeneratedDailyTask.task_date)).where(GeneratedDailyTask.user_id == user_id))
    last_day = db.scalar(select(func.max(GeneratedDailyTask.task_date)).where(GeneratedDailyTask.user_id == user_id))
    distinct_days = db.scalar(select(func.count(func.distinct(GeneratedDailyTask.task_date))).where(GeneratedDailyTask.user_id == user_id)) or 0
    total_tasks = db.scalar(select(func.count(GeneratedDailyTask.id)).where(GeneratedDailyTask.user_id == user_id)) or 0
    pre_start_tasks = db.scalar(select(func.count(GeneratedDailyTask.id)).where(GeneratedDailyTask.user_id == user_id, GeneratedDailyTask.task_date < PLANNER_START)) or 0
    duplicate_rows = db.execute(
        select(GeneratedDailyTask.task_date, GeneratedDailyTask.title, GeneratedDailyTask.task_type, func.count(GeneratedDailyTask.id))
        .where(GeneratedDailyTask.user_id == user_id)
        .group_by(GeneratedDailyTask.task_date, GeneratedDailyTask.title, GeneratedDailyTask.task_type)
        .having(func.count(GeneratedDailyTask.id) > 1)
        .limit(5)
    ).all()
    waiting = waiting_for_planner_start()
    active_valid = first_day == PLANNER_START and last_day == PLANNER_END and distinct_days == PLANNER_TOTAL_DAYS and not duplicate_rows and pre_start_tasks == 0
    waiting_valid = waiting["locked"] and pre_start_tasks == 0
    return {
        "planner_start_date": PLANNER_START.isoformat(),
        "planner_end_date": PLANNER_END.isoformat(),
        "status": waiting["status"],
        "locked": waiting["locked"],
        "days_until_start": waiting["days_until_start"],
        "message": waiting["message"],
        "expected_days": PLANNER_TOTAL_DAYS,
        "first_planner_day": first_day.isoformat() if first_day else None,
        "last_planner_day": last_day.isoformat() if last_day else None,
        "distinct_days": distinct_days,
        "total_tasks": total_tasks,
        "pre_start_task_count": pre_start_tasks,
        "missing_day_count": max(PLANNER_TOTAL_DAYS - distinct_days, 0),
        "duplicate_task_keys": len(duplicate_rows),
        "valid": waiting_valid or active_valid,
    }


def _task_mix(days_left: int, travel_enabled: bool, allow_mock_tests: bool, comeback_active: bool) -> list[StudyTaskType]:
    if travel_enabled:
        mix = [StudyTaskType.REVISION, StudyTaskType.FORMULA_REVIEW, StudyTaskType.READING]
        return mix + ([StudyTaskType.MOCK] if allow_mock_tests and days_left < 30 else [])
    if comeback_active:
        return [StudyTaskType.REVISION, StudyTaskType.PRACTICE, StudyTaskType.PYQ, StudyTaskType.ANALYSIS]
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


def _task_minutes(task_type: StudyTaskType, travel_enabled: bool, comeback_active: bool) -> int:
    if travel_enabled:
        return 25 if task_type != StudyTaskType.MOCK else 60
    if comeback_active:
        return {StudyTaskType.PYQ: 45, StudyTaskType.PRACTICE: 45, StudyTaskType.ANALYSIS: 30}.get(task_type, 35)
    return {StudyTaskType.MOCK: 120, StudyTaskType.ANALYSIS: 45, StudyTaskType.PYQ: 60, StudyTaskType.PRACTICE: 60}.get(task_type, 45)


def _task_reason(days_left: int, topic: SyllabusTopic, travel_enabled: bool, comeback_active: bool) -> str:
    if travel_enabled:
        return "Travel mode is on, so this is a lightweight task."
    if comeback_active:
        return f"Comeback mode is active: prioritizing weak/high-backlog topic {topic.name}."
    if days_left < 45:
        return f"Exam is near and {topic.name} still needs reinforcement."
    return f"Selected because progress is {topic.progress_percent:.0f}% and weak score is {topic.weak_score:.0f}."


def _ensure_calendar_event_for_task(db: Session, user_id: int, task: GeneratedDailyTask, order_index: int) -> None:
    if not _bulk_reset_mode:
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
