from datetime import date, timedelta

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import get_settings
from app.database import get_db
from app.email import send_daily_missed_task_email, send_weekly_summary_email
from app.models import DailyTask, DistractionLog, ExamTopic, ExamTrack, GymLog, GymRoutine, MockTest, Notification, Project, SleepLog, TaskCategory, TaskLog, TravelBreak, User, Warning, Goal, Milestone, LifeTask, Habit, HabitLog, DailyCheckIn, FocusSession, GoalStatus, TaskStatus
from app.schemas import (
    GoalCreate, GoalUpdate, GoalOut,
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
    NotificationOut,
    SleepLogCreate,
    TaskCreate,
    TaskOut,
    Token,
    TravelBreakCreate,
    UserCreate,
    WarningOut,
    WeeklyReviewOut,
)
from app.seed import FIXED_SCHEDULE, seed_user_defaults
from app.services import build_weekly_review, calculate_daily_discipline_score, completion_for_date, daily_recovery_plan, generate_warnings


settings = get_settings()
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(title="FinalPlanner Life OS API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/distractions/log", status_code=status.HTTP_201_CREATED)
def create_distraction_log(payload: DistractionLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    log = DistractionLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


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
def get_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.target_date)).all()

@app.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = Goal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal

@app.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, payload: GoalUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal

@app.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return None

@app.get("/milestones", response_model=list[MilestoneOut])
def get_milestones(goal_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Milestone).join(Goal).where(Goal.user_id == current_user.id)
    if goal_id:
        stmt = stmt.where(Milestone.goal_id == goal_id)
    return db.scalars(stmt.order_by(Milestone.target_date)).all()

@app.post("/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(payload: MilestoneCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.scalar(select(Goal).where(Goal.id == payload.goal_id, Goal.user_id == current_user.id))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    milestone = Milestone(**payload.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

@app.patch("/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(milestone_id: int, payload: MilestoneUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    milestone = db.scalar(select(Milestone).join(Goal).where(Milestone.id == milestone_id, Goal.user_id == current_user.id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(milestone, field, value)
    db.commit()
    db.refresh(milestone)
    return milestone

@app.get("/life-tasks", response_model=list[LifeTaskOut])
def get_life_tasks(date: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(LifeTask).where(LifeTask.user_id == current_user.id)
    if date:
        stmt = stmt.where(LifeTask.due_date == date)
    return db.scalars(stmt.order_by(LifeTask.due_date, LifeTask.id)).all()

@app.post("/life-tasks", response_model=LifeTaskOut, status_code=status.HTTP_201_CREATED)
def create_life_task(payload: LifeTaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = LifeTask(user_id=current_user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.patch("/life-tasks/{task_id}", response_model=LifeTaskOut)
def update_life_task(task_id: int, payload: LifeTaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(LifeTask).where(LifeTask.id == task_id, LifeTask.user_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/life-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_life_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(LifeTask).where(LifeTask.id == task_id, LifeTask.user_id == current_user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None

@app.get("/habits", response_model=list[HabitOut])
def get_habits(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Habit).where(Habit.user_id == current_user.id).order_by(Habit.id)).all()

@app.post("/habits", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(payload: HabitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit

@app.post("/habits/{habit_id}/log", status_code=status.HTTP_201_CREATED)
def log_habit(habit_id: int, payload: HabitLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = db.scalar(select(Habit).where(Habit.id == habit_id, Habit.user_id == current_user.id))
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    existing = db.scalar(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.log_date == payload.log_date))
    if existing:
        existing.completed = payload.completed
    else:
        db.add(HabitLog(habit_id=habit_id, log_date=payload.log_date, completed=payload.completed))
    
    # Update streaks naively
    if payload.completed:
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    else:
        habit.current_streak = 0

    db.commit()
    return {"message": "Habit logged"}

@app.get("/dashboard/live")
def dashboard_live(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    
    # Life Tasks
    tasks = db.scalars(select(LifeTask).where(LifeTask.user_id == current_user.id, LifeTask.due_date == today)).all()
    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    total_tasks = len(tasks)
    today_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Focus Sessions
    sessions = db.scalars(select(FocusSession).where(FocusSession.user_id == current_user.id)).all()
    today_focus = sum(s.duration_minutes for s in sessions if s.start_time.date() == today)
    
    # Habits
    habits = db.scalars(select(Habit).where(Habit.user_id == current_user.id)).all()
    habit_logs = db.scalars(select(HabitLog).join(Habit).where(Habit.user_id == current_user.id, HabitLog.log_date == today, HabitLog.completed.is_(True))).all()
    habit_completion_rate = (len(habit_logs) / len(habits) * 100) if habits else 0

    # Weekly Progress
    week_start = today - timedelta(days=today.weekday())
    weekly_tasks = db.scalars(select(LifeTask).where(LifeTask.user_id == current_user.id, LifeTask.due_date >= week_start, LifeTask.due_date <= today)).all()
    weekly_completed = sum(1 for t in weekly_tasks if t.status == TaskStatus.COMPLETED)
    weekly_total = len(weekly_tasks)
    weekly_progress = (weekly_completed / weekly_total * 100) if weekly_total > 0 else 0

    return {
        "today_progress": round(today_progress, 1),
        "weekly_progress": round(weekly_progress, 1),
        "streak_count": sum(h.current_streak for h in habits),
        "productivity_score": round((today_progress + habit_completion_rate) / 2, 1),
        "focus_minutes": today_focus,
        "habit_completion_rate": round(habit_completion_rate, 1)
    }
