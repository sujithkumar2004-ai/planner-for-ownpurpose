from datetime import date, datetime, timedelta
import logging
import os

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import get_settings
from app.database import get_db
from app.life_os_database import get_life_os_db
from app.email import send_daily_missed_task_email, send_weekly_summary_email
from app.life_os import (
    build_life_os_analytics,
    build_life_os_notifications,
    build_life_os_settings,
    build_life_os_weekly_review,
    build_live_dashboard,
    build_realtime_dashboard,
    build_monitoring_daily,
    build_monitoring_overview,
    build_monitoring_weekly,
    complete_generated_task,
    comeback_mode_summary,
    ensure_exam_catalog,
    generate_daily_tasks,
    get_travel_settings,
    refresh_exam_dates,
    task_payload,
    update_productivity_log,
)
from app.models import CalendarEvent, DailyTask, DistractionLog, Exam, ExamDate, ExamDateStatus, ExamTopic, ExamTrack, GeneratedDailyTask, GymLog, GymRoutine, MockScore, MockTest, Notification, Project, SleepLog, StudyPlan, SyllabusSubject, SyllabusTopic, TaskCategory, TaskLog, TravelBreak, TravelModeSettings, User, Warning, Goal, Milestone, LifeTask, Habit, HabitLog, DailyCheckIn, FocusSession, GoalStatus, TaskStatus
from app.schemas import (
    BackendExamOut,
    CalendarEventCreate,
    CalendarEventOut,
    CalendarEventUpdate,
    ExamDateOverride,
    GoalCreate, GoalUpdate, GoalOut,
    GeneratedTaskOut,
    GeneratedTaskUpdate,
    MilestoneCreate, MilestoneUpdate, MilestoneOut,
    LifeTaskCreate, LifeTaskUpdate, LifeTaskOut,
    HabitCreate, HabitOut, HabitLogCreate,
    DailyCheckInCreate, DailyCheckInOut,
    FocusSessionCreate, FocusSessionOut,
    DisciplineScoreOut,
    DistractionLogCreate,
    ExamOut,
    ExamTopicCreate,
    ExamTopicUpdate,
    GymLogCreate,
    GymRoutineOut,
    LoginRequest,
    MockTestCreate,
    MockScoreCreate,
    NotificationOut,
    SleepLogCreate,
    TaskCreate,
    TaskOut,
    Token,
    TravelModeOut,
    TravelModeUpdate,
    SyllabusTopicUpdate,
    StudyPlanCreate,
    TravelBreakCreate,
    UserCreate,
    WarningOut,
    WeeklyReviewOut,
)
from app.seed import FIXED_SCHEDULE, seed_user_defaults
from app.services import build_weekly_review, calculate_daily_discipline_score, completion_for_date, daily_recovery_plan, generate_warnings


settings = get_settings()
logger = logging.getLogger(__name__)
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

logger.warning(
    "Startup config ENV=%s CORS_ORIGINS=%s FRONTEND_ORIGINS=%s",
    os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT_NAME") or "unset",
    settings.cors_origin_list,
    [origin for origin in settings.cors_origin_list if "vercel.app" in origin],
)

app = FastAPI(title="FinalPlanner Life OS API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin:
        logger.warning("Request origin path=%s method=%s origin=%s", request.url.path, request.method, origin)
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, name=payload.name, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    seed_user_defaults(db, user)
    return Token(access_token=create_access_token(str(user.id)))


@app.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    if payload.email != settings.admin_email or payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        user = User(email=settings.admin_email, name="Admin", hashed_password=hash_password(settings.admin_password))
        db.add(user)
        db.commit()
        db.refresh(user)
    seed_user_defaults(db, user)
    return Token(access_token=create_access_token(str(user.id)))


@app.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    today = date.today()
    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == current_user.id, DailyTask.task_date == today)).all()
    exams = db.scalars(select(ExamTrack).where(ExamTrack.user_id == current_user.id).options(selectinload(ExamTrack.topics))).all()
    warnings = db.scalars(select(Warning).where(Warning.user_id == current_user.id, Warning.active.is_(True))).all()
    projects = db.scalars(select(Project).where(Project.user_id == current_user.id).order_by(Project.track, Project.order_index)).all()
    return {
        "name": current_user.name,
        "daily_completion": completion_for_date(db, current_user.id, today),
        "monk_mode": DisciplineScoreOut.model_validate(calculate_daily_discipline_score(db, current_user.id, today)).model_dump(mode="json"),
        "tasks": [TaskOut.model_validate(task).model_dump(mode="json") for task in tasks],
        "exams": [
            {
                "id": exam.id,
                "name": exam.name,
                "exam_date": exam.exam_date.isoformat(),
                "days_left": max((exam.exam_date - today).days, 0),
                "progress": round(sum(topic.completed_units for topic in exam.topics) / max(sum(topic.planned_units for topic in exam.topics), 1) * 100, 2),
            }
            for exam in exams
        ],
        "warnings": [WarningOut.model_validate(warning).model_dump(mode="json") for warning in warnings],
        "roadmap": [{"name": project.name, "track": project.track, "status": project.status} for project in projects],
    }


@app.get("/daily-plan", response_model=list[TaskOut])
def daily_plan(date: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DailyTask]:
    target_date = date or __import__("datetime").date.today()
    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == current_user.id, DailyTask.task_date == target_date).order_by(DailyTask.start_time)).all()
    if not tasks:
        for title, category, start_time, end_time in FIXED_SCHEDULE:
            db.add(DailyTask(user_id=current_user.id, task_date=target_date, title=title, category=category, start_time=start_time, end_time=end_time))
        db.commit()
        tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == current_user.id, DailyTask.task_date == target_date).order_by(DailyTask.start_time)).all()
    return tasks


@app.get("/exams/catalog", response_model=list[BackendExamOut])
def exams_catalog(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[Exam]:
    ensure_exam_catalog(life_db, current_user.id)
    return life_db.scalars(select(Exam).where(Exam.active.is_(True)).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics)).order_by(Exam.id)).all()


@app.post("/exams/refresh-dates")
def refresh_dates(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    refreshed = refresh_exam_dates(life_db)
    return {"refreshed": len(refreshed), "dates": [{"exam_id": item.exam_id, "exam_date": item.exam_date.isoformat(), "status": item.status.value} for item in refreshed]}


@app.patch("/exams/{exam_id}/date", response_model=BackendExamOut)
def override_exam_date(exam_id: int, payload: ExamDateOverride, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> Exam:
    ensure_exam_catalog(life_db, current_user.id)
    exam = life_db.scalar(select(Exam).where(Exam.id == exam_id))
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam_date = life_db.scalar(select(ExamDate).where(ExamDate.exam_id == exam.id, ExamDate.label == payload.label)) or ExamDate(exam_id=exam.id, label=payload.label)
    exam_date.exam_date = payload.exam_date
    exam_date.status = ExamDateStatus.MANUAL_OVERRIDE
    exam_date.manually_overridden = True
    exam_date.source_name = payload.source_name
    exam_date.refreshed_at = datetime.utcnow()
    life_db.add(exam_date)
    life_db.commit()
    return life_db.scalar(select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.dates), selectinload(Exam.subjects).selectinload(SyllabusSubject.topics)))


@app.get("/study-plans")
def study_plans(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    ensure_exam_catalog(life_db, current_user.id)
    plans = life_db.scalars(select(StudyPlan).where(StudyPlan.user_id == current_user.id)).all()
    exams_by_id = {exam.id: exam for exam in life_db.scalars(select(Exam).where(Exam.active.is_(True))).all()}
    return [
        {
            "id": plan.id,
            "exam_id": plan.exam_id,
            "exam_name": exams_by_id[plan.exam_id].name,
            "active": plan.active,
            "available_hours_per_day": plan.available_hours_per_day,
            "priority": plan.priority,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat(),
        }
        for plan in plans
        if plan.exam_id in exams_by_id
    ]


@app.post("/study-plans")
def upsert_study_plan(payload: StudyPlanCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    ensure_exam_catalog(life_db, current_user.id)
    exam = life_db.scalar(select(Exam).where(Exam.id == payload.exam_id, Exam.active.is_(True)))
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    plan = life_db.scalar(select(StudyPlan).where(StudyPlan.user_id == current_user.id, StudyPlan.exam_id == payload.exam_id)) or StudyPlan(user_id=current_user.id, exam_id=payload.exam_id)
    plan.active = payload.active
    plan.available_hours_per_day = payload.available_hours_per_day
    plan.priority = payload.priority
    plan.start_date = payload.start_date
    plan.end_date = payload.end_date
    life_db.add(plan)
    life_db.commit()
    life_db.refresh(plan)
    return {"id": plan.id, "exam_id": plan.exam_id, "active": plan.active, "available_hours_per_day": plan.available_hours_per_day, "priority": plan.priority, "start_date": plan.start_date.isoformat(), "end_date": plan.end_date.isoformat()}


@app.get("/generated-daily-tasks", response_model=list[GeneratedTaskOut])
def generated_tasks(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    return [task_payload(life_db, task) for task in generate_daily_tasks(life_db, current_user.id, date)]


@app.post("/generated-daily-tasks/generate", response_model=list[GeneratedTaskOut])
def regenerate_tasks(date: date | None = None, force: bool = False, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    return [task_payload(life_db, task) for task in generate_daily_tasks(life_db, current_user.id, date, force=force)]


@app.patch("/generated-daily-tasks/{task_id}", response_model=GeneratedTaskOut)
def update_generated_task(task_id: int, payload: GeneratedTaskUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    task = complete_generated_task(life_db, current_user.id, task_id, payload.status, payload.minutes_spent, payload.notes)
    if not task:
        raise HTTPException(status_code=404, detail="Generated task not found")
    return task_payload(life_db, task)


@app.get("/calendar-events", response_model=list[CalendarEventOut])
def calendar_events(start: datetime | None = None, end: datetime | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[CalendarEvent]:
    generate_daily_tasks(life_db, current_user.id, (start or datetime.utcnow()).date())
    stmt = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)
    if start:
        stmt = stmt.where(CalendarEvent.end_at >= start)
    if end:
        stmt = stmt.where(CalendarEvent.start_at <= end)
    return life_db.scalars(stmt.order_by(CalendarEvent.start_at)).all()


@app.post("/calendar-events", response_model=CalendarEventOut, status_code=status.HTTP_201_CREATED)
def create_calendar_event(payload: CalendarEventCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> CalendarEvent:
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    event = CalendarEvent(user_id=current_user.id, **payload.model_dump())
    life_db.add(event)
    life_db.commit()
    life_db.refresh(event)
    return event


@app.patch("/calendar-events/{event_id}", response_model=CalendarEventOut)
def update_calendar_event(event_id: int, payload: CalendarEventUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> CalendarEvent:
    event = life_db.scalar(select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id))
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    if event.end_at <= event.start_at:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    life_db.commit()
    life_db.refresh(event)
    return event


@app.delete("/calendar-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(event_id: int, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    event = life_db.scalar(select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id))
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    life_db.delete(event)
    life_db.commit()
    return None


@app.get("/travel-mode", response_model=TravelModeOut)
def travel_mode(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> TravelModeSettings:
    return get_travel_settings(life_db, current_user.id)


@app.patch("/travel-mode", response_model=TravelModeOut)
def update_travel_mode(payload: TravelModeUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> TravelModeSettings:
    if payload.enabled and payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="Travel end date must be on or after start date")
    settings_travel = get_travel_settings(life_db, current_user.id)
    settings_travel.enabled = payload.enabled
    settings_travel.start_date = payload.start_date
    settings_travel.end_date = payload.end_date
    settings_travel.allow_mock_tests = payload.allow_mock_tests
    settings_travel.daily_minutes = payload.daily_minutes
    settings_travel.notes = payload.notes
    life_db.add(settings_travel)
    life_db.commit()
    life_db.refresh(settings_travel)
    from app.life_os import _travel_settings_cache
    _travel_settings_cache.pop(current_user.id, None)
    generate_daily_tasks(life_db, current_user.id, date.today(), force=True)
    return settings_travel


@app.patch("/syllabus-topics/{topic_id}")
def update_syllabus_topic(topic_id: int, payload: SyllabusTopicUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    ensure_exam_catalog(life_db, current_user.id)
    topic = life_db.scalar(select(SyllabusTopic).where(SyllabusTopic.id == topic_id))
    if not topic:
        raise HTTPException(status_code=404, detail="Syllabus topic not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    life_db.commit()
    life_db.refresh(topic)
    return {"id": topic.id, "progress_percent": topic.progress_percent, "weak_score": topic.weak_score}


@app.get("/comeback-mode")
def comeback_mode(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    ensure_exam_catalog(life_db, current_user.id)
    return comeback_mode_summary(life_db, current_user.id, date)


@app.post("/mock-scores", status_code=status.HTTP_201_CREATED)
def create_mock_score(payload: MockScoreCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    ensure_exam_catalog(life_db, current_user.id)
    if not life_db.scalar(select(Exam).where(Exam.id == payload.exam_id, Exam.active.is_(True))):
        raise HTTPException(status_code=404, detail="Exam not found")
    mock = MockScore(user_id=current_user.id, **payload.model_dump())
    life_db.add(mock)
    life_db.commit()
    life_db.refresh(mock)
    return {"id": mock.id}


@app.get("/mock-scores")
def mock_scores(exam_id: int | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    stmt = select(MockScore).where(MockScore.user_id == current_user.id)
    if exam_id:
        stmt = stmt.where(MockScore.exam_id == exam_id)
    rows = life_db.scalars(stmt.order_by(MockScore.taken_on.desc(), MockScore.id.desc())).all()
    exams = {exam.id: exam.name for exam in life_db.scalars(select(Exam).where(Exam.active.is_(True))).all()}
    return [{"id": row.id, "exam_id": row.exam_id, "exam_name": exams.get(row.exam_id), "taken_on": row.taken_on.isoformat(), "score": row.score, "max_score": row.max_score, "analysis": row.analysis, "weak_topics": row.weak_topics} for row in rows]


@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DailyTask:
    task = DailyTask(user_id=current_user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, completed: bool = True, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DailyTask:
    task = db.scalar(select(DailyTask).where(DailyTask.id == task_id, DailyTask.user_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = completed
    db.add(TaskLog(user_id=current_user.id, task_id=task.id, notes="Completed" if completed else "Marked incomplete"))
    db.commit()
    db.refresh(task)
    return task


@app.get("/exams", response_model=list[ExamOut])
def exams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ExamTrack]:
    return db.scalars(select(ExamTrack).where(ExamTrack.user_id == current_user.id).options(selectinload(ExamTrack.topics))).all()


@app.post("/exam-topics", status_code=status.HTTP_201_CREATED)
def create_exam_topic(payload: ExamTopicCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    exam = db.scalar(select(ExamTrack).where(ExamTrack.id == payload.exam_id, ExamTrack.user_id == current_user.id))
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    backlog = max(0, 100 - (payload.completed_units / max(payload.planned_units, 1) * 100))
    topic = ExamTopic(user_id=current_user.id, backlog_percent=backlog, **payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"id": topic.id, "backlog_percent": topic.backlog_percent}


@app.patch("/exam-topics/{topic_id}")
def update_exam_topic(topic_id: int, payload: ExamTopicUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    topic = db.scalar(select(ExamTopic).where(ExamTopic.id == topic_id, ExamTopic.user_id == current_user.id))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    topic.backlog_percent = max(0, 100 - (topic.completed_units / max(topic.planned_units, 1) * 100))
    db.commit()
    db.refresh(topic)
    return {"id": topic.id, "backlog_percent": topic.backlog_percent}


@app.post("/mock-tests", status_code=status.HTTP_201_CREATED)
def create_mock_test(payload: MockTestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    mock = MockTest(user_id=current_user.id, **payload.model_dump())
    db.add(mock)
    db.commit()
    db.refresh(mock)
    return {"id": mock.id}


@app.get("/gym/routine", response_model=list[GymRoutineOut])
def gym_routine(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[GymRoutine]:
    return db.scalars(select(GymRoutine).where(GymRoutine.user_id == current_user.id).order_by(GymRoutine.weekday)).all()


@app.post("/gym/log", status_code=status.HTTP_201_CREATED)
def gym_log(payload: GymLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    log = GymLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


@app.post("/travel-break", status_code=status.HTTP_201_CREATED)
def travel_break(payload: TravelBreakCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(TravelBreak).where(TravelBreak.user_id == current_user.id))
    if existing:
        generate_warnings(db, current_user.id)
        raise HTTPException(status_code=409, detail="Only one travel break is allowed")
    duration = (payload.end_date - payload.start_date).days + 1
    if duration > 14:
        raise HTTPException(status_code=400, detail="Travel break cannot exceed 14 continuous days")
    if duration < 1:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")
    travel = TravelBreak(user_id=current_user.id, **payload.model_dump())
    db.add(travel)
    day = payload.start_date
    while day <= payload.end_date:
        db.add(DailyTask(user_id=current_user.id, task_date=day, title="Formula Revision", category=TaskCategory.TRAVEL_LIGHT, start_time="08:00", end_time="08:30"))
        db.add(DailyTask(user_id=current_user.id, task_date=day, title="Reading / Vocab", category=TaskCategory.TRAVEL_LIGHT, start_time="20:00", end_time="20:30"))
        db.add(DailyTask(user_id=current_user.id, task_date=day, title="Travel Journal", category=TaskCategory.JOURNAL, start_time="22:00", end_time="22:20"))
        db.add(DailyTask(user_id=current_user.id, task_date=day, title="Walking", category=TaskCategory.TRAVEL_LIGHT, start_time="18:00", end_time="18:30"))
        day += timedelta(days=1)
    db.commit()
    db.refresh(travel)
    return {"id": travel.id, "message": "Travel mode enabled with light revision, reading, and journal tasks."}


@app.get("/warnings", response_model=list[WarningOut])
def warnings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Warning]:
    return db.scalars(select(Warning).where(Warning.user_id == current_user.id, Warning.active.is_(True)).order_by(Warning.created_at.desc())).all()


@app.post("/warnings/generate", response_model=list[WarningOut])
def warnings_generate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Warning]:
    return generate_warnings(db, current_user.id)


@app.get("/monk-mode/daily-score", response_model=DisciplineScoreOut)
def monk_mode_daily_score(date: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return calculate_daily_discipline_score(db, current_user.id, date or __import__("datetime").date.today())


@app.get("/monk-mode/recovery-plan")
def monk_mode_recovery_plan(date: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return daily_recovery_plan(db, current_user.id, date or __import__("datetime").date.today())


@app.get("/weekly-review", response_model=WeeklyReviewOut)
def weekly_review(date: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_weekly_review(db, current_user.id, date or __import__("datetime").date.today())


@app.post("/sleep/log", status_code=status.HTTP_201_CREATED)
def create_sleep_log(payload: SleepLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(SleepLog).where(SleepLog.user_id == current_user.id, SleepLog.sleep_date == payload.sleep_date))
    log = existing or SleepLog(user_id=current_user.id, sleep_date=payload.sleep_date)
    for field, value in payload.model_dump(exclude={"sleep_date"}).items():
        setattr(log, field, value)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


@app.get("/sleep/logs")
@app.get("/api/sleep/logs")
def sleep_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    logs = db.scalars(select(SleepLog).where(SleepLog.user_id == current_user.id).order_by(SleepLog.sleep_date.desc())).all()
    return [
        {
            "id": log.id,
            "sleep_date": log.sleep_date.isoformat(),
            "sleep_start": log.sleep_start.isoformat() if log.sleep_start else None,
            "sleep_end": log.sleep_end.isoformat() if log.sleep_end else None,
            "hours": log.hours,
            "quality": log.quality,
            "notes": log.notes,
        }
        for log in logs
    ]


@app.post("/distractions/log", status_code=status.HTTP_201_CREATED)
def create_distraction_log(payload: DistractionLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    log = DistractionLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


@app.get("/distractions/logs")
@app.get("/api/distractions/logs")
def distraction_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    logs = db.scalars(select(DistractionLog).where(DistractionLog.user_id == current_user.id).order_by(DistractionLog.log_date.desc(), DistractionLog.id.desc())).all()
    return [
        {
            "id": log.id,
            "log_date": log.log_date.isoformat(),
            "source": log.source,
            "minutes": log.minutes,
            "notes": log.notes,
        }
        for log in logs
    ]


@app.get("/notifications", response_model=list[NotificationOut])
def notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Notification]:
    return db.scalars(select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())).all()


@app.post("/email/daily-alert")
def trigger_daily_email(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {"sent": send_daily_missed_task_email(db, current_user, date.today())}


@app.post("/email/weekly-summary")
def trigger_weekly_email(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {"sent": send_weekly_summary_email(db, current_user, date.today())}


@app.get("/analytics")
def analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    today = date.today()
    daily = [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "completion": completion_for_date(db, current_user.id, today - timedelta(days=offset)),
            "discipline_score": calculate_daily_discipline_score(db, current_user.id, today - timedelta(days=offset)).score,
        }
        for offset in range(6, -1, -1)
    ]
    exams = db.scalars(select(ExamTrack).where(ExamTrack.user_id == current_user.id).options(selectinload(ExamTrack.topics))).all()
    return {
        "weekly_completion": daily,
        "weekly_score": round(sum(item["discipline_score"] for item in daily) / 7, 2),
        "exam_backlog": [
            {
                "exam": exam.name,
                "backlog": round(sum(topic.backlog_percent for topic in exam.topics) / max(len(exam.topics), 1), 2),
            }
            for exam in exams
        ],
    }


@app.get("/export/json")
def export_json(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {
        "dashboard": dashboard(current_user, db),
        "analytics": analytics(current_user, db),
        "weekly_review": WeeklyReviewOut.model_validate(build_weekly_review(db, current_user.id, date.today())).model_dump(mode="json"),
    }


@app.get("/export/csv")
def export_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    rows = ["date,title,category,completed"]
    tasks = db.scalars(select(DailyTask).where(DailyTask.user_id == current_user.id).order_by(DailyTask.task_date, DailyTask.start_time)).all()
    for task in tasks:
        rows.append(f"{task.task_date},{task.title},{task.category.value},{task.completed}")
    return Response("\n".join(rows), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=finalplanner-tasks.csv"})


@app.get("/export/pdf")
def export_pdf(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    review = build_weekly_review(db, current_user.id, date.today())
    text = f"FinalPlanner Weekly Report | Score: {review.weekly_score} | Best: {review.best_day} | Worst: {review.worst_day}"
    stream = f"BT /F1 12 Tf 72 720 Td ({text.replace('(', '[').replace(')', ']')}) Tj ET"
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "trailer << /Root 1 0 R /Size 6 >>\nstartxref\n0\n%%EOF"
    )
    return Response(pdf.encode("utf-8"), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=finalplanner-report.pdf"})


# --- NEW LIFE OS ROUTES ---

@app.get("/goals", response_model=list[GoalOut])
def get_goals(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return life_db.scalars(select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.target_date)).all()

@app.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    goal = Goal(user_id=current_user.id, **payload.model_dump())
    life_db.add(goal)
    life_db.commit()
    life_db.refresh(goal)
    return goal

@app.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, payload: GoalUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    goal = life_db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    life_db.commit()
    life_db.refresh(goal)
    return goal

@app.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    goal = life_db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    life_db.delete(goal)
    life_db.commit()
    return None

@app.get("/milestones", response_model=list[MilestoneOut])
def get_milestones(goal_id: int | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    stmt = select(Milestone).join(Goal).where(Goal.user_id == current_user.id)
    if goal_id:
        stmt = stmt.where(Milestone.goal_id == goal_id)
    return life_db.scalars(stmt.order_by(Milestone.target_date)).all()

@app.post("/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(payload: MilestoneCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    goal = life_db.scalar(select(Goal).where(Goal.id == payload.goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    milestone = Milestone(**payload.model_dump())
    life_db.add(milestone)
    life_db.commit()
    life_db.refresh(milestone)
    return milestone

@app.patch("/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(milestone_id: int, payload: MilestoneUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    milestone = life_db.scalar(select(Milestone).join(Goal).where(Milestone.id == milestone_id, Goal.user_id == current_user.id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(milestone, field, value)
    life_db.commit()
    life_db.refresh(milestone)
    return milestone

@app.get("/life-tasks", response_model=list[LifeTaskOut])
def get_life_tasks(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    stmt = select(LifeTask).where(LifeTask.user_id == current_user.id)
    if date:
        stmt = stmt.where(LifeTask.due_date == date)
    return life_db.scalars(stmt.order_by(LifeTask.due_date, LifeTask.id)).all()

@app.post("/life-tasks", response_model=LifeTaskOut, status_code=status.HTTP_201_CREATED)
def create_life_task(payload: LifeTaskCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    task = LifeTask(user_id=current_user.id, **payload.model_dump())
    life_db.add(task)
    life_db.commit()
    life_db.refresh(task)
    return task

@app.patch("/life-tasks/{task_id}", response_model=LifeTaskOut)
def update_life_task(task_id: int, payload: LifeTaskUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    task = life_db.scalar(select(LifeTask).where(LifeTask.id == task_id, LifeTask.user_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    life_db.commit()
    life_db.refresh(task)
    return task

@app.delete("/life-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_life_task(task_id: int, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    task = life_db.scalar(select(LifeTask).where(LifeTask.id == task_id, LifeTask.user_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    life_db.delete(task)
    life_db.commit()
    return None

@app.get("/habits", response_model=list[HabitOut])
def get_habits(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return life_db.scalars(select(Habit).where(Habit.user_id == current_user.id).order_by(Habit.id)).all()

@app.post("/habits", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(payload: HabitCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    life_db.add(habit)
    life_db.commit()
    life_db.refresh(habit)
    return habit

@app.post("/habits/{habit_id}/log", status_code=status.HTTP_201_CREATED)
def log_habit(habit_id: int, payload: HabitLogCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    habit = life_db.scalar(select(Habit).where(Habit.id == habit_id, Habit.user_id == current_user.id))
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    existing = life_db.scalar(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.log_date == payload.log_date))
    if existing:
        existing.completed = payload.completed
    else:
        life_db.add(HabitLog(habit_id=habit_id, log_date=payload.log_date, completed=payload.completed))
    
    # Update streaks naively
    if payload.completed:
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    else:
        habit.current_streak = 0

    life_db.commit()
    return {"message": "Habit logged"}


@app.post("/daily-checkins", response_model=DailyCheckInOut, status_code=status.HTTP_201_CREATED)
def upsert_daily_checkin(payload: DailyCheckInCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> DailyCheckIn:
    checkin = life_db.scalar(select(DailyCheckIn).where(DailyCheckIn.user_id == current_user.id, DailyCheckIn.log_date == payload.log_date)) or DailyCheckIn(user_id=current_user.id, log_date=payload.log_date)
    for field, value in payload.model_dump(exclude={"log_date"}).items():
        setattr(checkin, field, value)
    life_db.add(checkin)
    life_db.commit()
    life_db.refresh(checkin)
    return checkin


@app.get("/daily-checkins", response_model=list[DailyCheckInOut])
def get_daily_checkins(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[DailyCheckIn]:
    return life_db.scalars(select(DailyCheckIn).where(DailyCheckIn.user_id == current_user.id).order_by(DailyCheckIn.log_date.desc())).all()


@app.post("/focus-sessions", response_model=FocusSessionOut, status_code=status.HTTP_201_CREATED)
def create_focus_session(payload: FocusSessionCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> FocusSession:
    session = FocusSession(user_id=current_user.id, **payload.model_dump())
    life_db.add(session)
    update_productivity_log(life_db, current_user.id, payload.start_time.date())
    life_db.commit()
    life_db.refresh(session)
    return session


@app.get("/focus-sessions", response_model=list[FocusSessionOut])
def get_focus_sessions(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[FocusSession]:
    return life_db.scalars(select(FocusSession).where(FocusSession.user_id == current_user.id).order_by(FocusSession.start_time.desc())).all()

@app.get("/dashboard/live")
def dashboard_live(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return build_live_dashboard(life_db, current_user.id)


@app.get("/dashboard/realtime")
def dashboard_realtime(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), life_db: Session = Depends(get_life_os_db)) -> dict:
    try:
        return build_realtime_dashboard(life_db, current_user.id, db)
    except HTTPException:
        raise
    except Exception as exc:
        life_db.rollback()
        db.rollback()
        logger.exception("Realtime dashboard failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=500, detail="Realtime dashboard failed to load safely") from exc


@app.get("/weekly-review/live")
def weekly_review_live(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_life_os_weekly_review(life_db, current_user.id, date)


@app.get("/notifications/live")
def notifications_live(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    return build_life_os_notifications(life_db, current_user.id)


@app.get("/analytics/live")
def analytics_live(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_life_os_analytics(life_db, current_user.id)


@app.get("/settings/life-os")
def life_os_settings(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_life_os_settings(life_db, current_user.id)


@app.get("/monitoring/overview")
@app.get("/api/monitoring/overview")
def monitoring_overview(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_monitoring_overview(life_db, current_user.id)


@app.get("/monitoring/daily")
@app.get("/api/monitoring/daily")
def monitoring_daily(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_monitoring_daily(life_db, current_user.id, date)


@app.get("/monitoring/weekly")
@app.get("/api/monitoring/weekly")
def monitoring_weekly(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_monitoring_weekly(life_db, current_user.id, date)


@app.get("/api/tasks", response_model=list[GeneratedTaskOut])
def api_tasks(date: date | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    return generated_tasks(date, current_user, life_db)


@app.post("/api/tasks", response_model=list[GeneratedTaskOut])
def api_generate_tasks(date: date | None = None, force: bool = False, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[dict]:
    return regenerate_tasks(date, force, current_user, life_db)


@app.patch("/api/tasks/{task_id}", response_model=GeneratedTaskOut)
def api_update_task(task_id: int, payload: GeneratedTaskUpdate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return update_generated_task(task_id, payload, current_user, life_db)


@app.get("/api/habits", response_model=list[HabitOut])
def api_habits(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return get_habits(current_user, life_db)


@app.post("/api/habits", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def api_create_habit(payload: HabitCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return create_habit(payload, current_user, life_db)


@app.patch("/api/habits/{habit_id}/log", status_code=status.HTTP_201_CREATED)
def api_log_habit(habit_id: int, payload: HabitLogCreate, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return log_habit(habit_id, payload, current_user, life_db)


@app.get("/api/goals", response_model=list[GoalOut])
def api_goals(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)):
    return get_goals(current_user, life_db)


@app.get("/api/calendar/events", response_model=list[CalendarEventOut])
def api_calendar_events(start: datetime | None = None, end: datetime | None = None, current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> list[CalendarEvent]:
    return calendar_events(start, end, current_user, life_db)


@app.get("/api/analytics/productivity")
def api_productivity_analytics(current_user: User = Depends(get_current_user), life_db: Session = Depends(get_life_os_db)) -> dict:
    return build_life_os_analytics(life_db, current_user.id)


from pydantic import BaseModel

class ResetPlannerPayload(BaseModel):
    confirmation_text: str


planner_reset_jobs = {}


def save_job_status(job_id: str, data: dict):
    planner_reset_jobs[job_id] = data
    try:
        import redis
        import json
        r = redis.from_url(settings.redis_url)
        r.set(f"reset_job:{job_id}", json.dumps(data), ex=86400)
    except Exception:
        pass


def get_job_status(job_id: str) -> dict | None:
    try:
        import redis
        import json
        r = redis.from_url(settings.redis_url)
        data = r.get(f"reset_job:{job_id}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    return planner_reset_jobs.get(job_id)


def run_reset_job(job_id: str, admin_email: str):
    try:
        # Clear caches before starting
        from app.life_os import clear_life_os_caches
        clear_life_os_caches()

        # Connect to direct database URLs for bulk reset/regeneration work.
        direct_url = settings.direct_url or settings.database_url
        life_direct_url = settings.life_os_direct_url or settings.life_os_database_url
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(direct_url, pool_pre_ping=True)
        life_engine = engine if life_direct_url == direct_url else create_engine(life_direct_url, pool_pre_ping=True)
        DirectSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        LifeDirectSession = DirectSession if life_engine is engine else sessionmaker(bind=life_engine, autoflush=False, autocommit=False, expire_on_commit=False)
        direct_db = DirectSession()
        life_direct_db = direct_db if life_engine is engine else LifeDirectSession()
        try:
            from app.reset_planner import reset_planner_data
            res = reset_planner_data(direct_db, life_direct_db, admin_email=admin_email)
            save_job_status(job_id, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "result": res,
                "error": None
            })
        finally:
            if life_direct_db is not direct_db:
                life_direct_db.close()
            direct_db.close()
            if life_engine is not engine:
                life_engine.dispose()
            engine.dispose()
    except Exception as exc:
        logger.exception(f"Background planner reset failed for job {job_id}")
        save_job_status(job_id, {
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": str(exc)
        })


@app.post("/admin/reset-planner")
def admin_reset_planner(
    payload: ResetPlannerPayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict:
    if current_user.email != settings.admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required"
        )
    if os.getenv("RESET_PLANNER_CONFIRM") != "true":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RESET_PLANNER_CONFIRM environment variable must be set to 'true'"
        )
    from app.reset_planner import CONFIRMATION_TEXT
    if payload.confirmation_text != CONFIRMATION_TEXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation text. Must be '{CONFIRMATION_TEXT}'"
        )

    import uuid
    job_id = str(uuid.uuid4())
    job_data = {
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None
    }
    save_job_status(job_id, job_data)
    background_tasks.add_task(run_reset_job, job_id, current_user.email)
    return {"job_id": job_id, "status": "running"}


@app.get("/admin/reset-planner/status/{job_id}")
def admin_reset_planner_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> dict:
    if current_user.email != settings.admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required"
        )
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job
