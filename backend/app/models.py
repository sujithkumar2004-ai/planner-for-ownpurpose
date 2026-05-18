from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskCategory(str, Enum):
    EXAM_FOUNDATION = "exam_foundation"
    BACKEND = "backend"
    LLM_AGENTIC_AI = "llm_agentic_ai"
    GYM = "gym"
    EXAM_ROTATION = "exam_rotation"
    REVISION = "revision"
    JOURNAL = "journal"
    TRAVEL_LIGHT = "travel_light"


class WarningLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


class DisciplineStatus(str, Enum):
    ELITE = "Elite"
    ON_TRACK = "On Track"
    WARNING = "Warning"
    CRITICAL = "Critical"


class NotificationType(str, Enum):
    WARNING = "warning"
    RECOVERY = "recovery"
    WEEKLY_REVIEW = "weekly_review"
    EMAIL = "email"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_date: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[TaskCategory] = mapped_column(SAEnum(TaskCategory))
    start_time: Mapped[str] = mapped_column(String(20))
    end_time: Mapped[str] = mapped_column(String(20))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "task_date", "title", name="uq_user_task_date_title"),)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("daily_tasks.id", ondelete="CASCADE"))
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExamTrack(Base):
    __tablename__ = "exam_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    exam_date: Mapped[date]
    target_score: Mapped[str | None] = mapped_column(String(80), nullable=True)
    topics: Mapped[list["ExamTopic"]] = relationship(back_populates="exam", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_exam_name"),)


class ExamTopic(Base):
    __tablename__ = "exam_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exam_tracks.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    planned_units: Mapped[int] = mapped_column(Integer, default=10)
    completed_units: Mapped[int] = mapped_column(Integer, default=0)
    backlog_percent: Mapped[float] = mapped_column(Float, default=0)
    exam: Mapped[ExamTrack] = relationship(back_populates="topics")


class MockTest(Base):
    __tablename__ = "mock_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exam_tracks.id", ondelete="CASCADE"))
    taken_on: Mapped[date]
    score: Mapped[float]
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(80))
    session_date: Mapped[date]
    duration_minutes: Mapped[int]
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class GymRoutine(Base):
    __tablename__ = "gym_routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)
    day_name: Mapped[str] = mapped_column(String(20))
    focus: Mapped[str] = mapped_column(String(160))
    exercises: Mapped[str] = mapped_column(Text)


class GymLog(Base):
    __tablename__ = "gym_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date]
    exercise_name: Mapped[str] = mapped_column(String(160))
    sets: Mapped[int] = mapped_column(Integer, default=0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[float] = mapped_column(Float, default=0)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class TravelBreak(Base):
    __tablename__ = "travel_breaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date]
    end_date: Mapped[date]
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WarningRule(Base):
    __tablename__ = "warning_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    level: Mapped[WarningLevel] = mapped_column(SAEnum(WarningLevel))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rule_code: Mapped[str] = mapped_column(String(80))
    level: Mapped[WarningLevel] = mapped_column(SAEnum(WarningLevel))
    message: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    entry_date: Mapped[date]
    content: Mapped[str] = mapped_column(Text)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    track: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="planned")
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    snapshot_date: Mapped[date]
    daily_completion: Mapped[float] = mapped_column(Float, default=0)
    weekly_score: Mapped[float] = mapped_column(Float, default=0)
    gym_weekdays_completed: Mapped[int] = mapped_column(Integer, default=0)
    revision_streak: Mapped[int] = mapped_column(Integer, default=0)


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    sleep_date: Mapped[date] = mapped_column(Date, index=True)
    sleep_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sleep_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hours: Mapped[float] = mapped_column(Float, default=0)
    quality: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "sleep_date", name="uq_user_sleep_date"),)


class DistractionLog(Base):
    __tablename__ = "distraction_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(120), default="manual")
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DisciplineScore(Base):
    __tablename__ = "discipline_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    score_date: Mapped[date] = mapped_column(Date, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[DisciplineStatus] = mapped_column(SAEnum(DisciplineStatus), default=DisciplineStatus.CRITICAL)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    travel_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_level: Mapped[WarningLevel] = mapped_column(SAEnum(WarningLevel), default=WarningLevel.GREEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "score_date", name="uq_user_score_date"),)


class RecoveryMode(Base):
    __tablename__ = "recovery_modes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recovery_date: Mapped[date] = mapped_column(Date, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str] = mapped_column(Text)
    priority_plan: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "recovery_date", name="uq_user_recovery_date"),)


class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date, index=True)
    weekly_score: Mapped[float] = mapped_column(Float, default=0)
    best_day: Mapped[str | None] = mapped_column(String(40), nullable=True)
    worst_day: Mapped[str | None] = mapped_column(String(40), nullable=True)
    missed_blocks: Mapped[dict] = mapped_column(JSON, default=dict)
    next_week_focus: Mapped[dict] = mapped_column(JSON, default=dict)
    correction_day: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_user_week_start"),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(180))
    body: Mapped[str] = mapped_column(Text)
    level: Mapped[WarningLevel] = mapped_column(SAEnum(WarningLevel), default=WarningLevel.GREEN)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    email_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_email_time: Mapped[str] = mapped_column(String(10), default="23:30")
    weekly_email_time: Mapped[str] = mapped_column(String(10), default="21:00")
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Kolkata")
    theme: Mapped[str] = mapped_column(String(20), default="system")
    daily_min_score: Mapped[int] = mapped_column(Integer, default=70)
    weekly_min_score: Mapped[int] = mapped_column(Integer, default=75)
    distraction_limit_minutes: Mapped[int] = mapped_column(Integer, default=0)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(SAEnum(GoalStatus), default=GoalStatus.ACTIVE)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    milestones: Mapped[list["Milestone"]] = relationship(back_populates="goal", cascade="all, delete-orphan")
    tasks: Mapped[list["LifeTask"]] = relationship(back_populates="goal")


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    goal: Mapped[Goal] = relationship(back_populates="milestones")
    tasks: Mapped[list["LifeTask"]] = relationship(back_populates="milestone")


class LifeTask(Base):
    __tablename__ = "life_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True)
    milestone_id: Mapped[int | None] = mapped_column(ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    goal: Mapped[Goal | None] = relationship(back_populates="tasks")
    milestone: Mapped[Milestone | None] = relationship(back_populates="tasks")


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    frequency: Mapped[str] = mapped_column(String(50), default="daily")
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),)


class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    focus_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    productivity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_user_checkin_date"),)


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("life_tasks.id", ondelete="SET NULL"), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
