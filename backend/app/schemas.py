from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import DisciplineStatus, TaskCategory, WarningLevel, GoalStatus, TaskStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TaskCreate(BaseModel):
    task_date: date
    title: str
    category: TaskCategory
    start_time: str
    end_time: str
    notes: str | None = None


class TaskOut(BaseModel):
    id: int
    task_date: date
    title: str
    category: TaskCategory
    start_time: str
    end_time: str
    completed: bool
    mandatory: bool = True
    locked: bool = False
    notes: str | None

    model_config = {"from_attributes": True}


class ExamTopicCreate(BaseModel):
    exam_id: int
    name: str
    planned_units: int = 10
    completed_units: int = 0


class ExamTopicUpdate(BaseModel):
    name: str | None = None
    planned_units: int | None = None
    completed_units: int | None = None


class ExamTopicOut(BaseModel):
    id: int
    name: str
    planned_units: int
    completed_units: int
    backlog_percent: float

    model_config = {"from_attributes": True}


class ExamOut(BaseModel):
    id: int
    name: str
    exam_date: date
    target_score: str | None
    topics: list[ExamTopicOut] = []

    model_config = {"from_attributes": True}


class MockTestCreate(BaseModel):
    exam_id: int
    taken_on: date
    score: float
    analysis: str | None = None


class GymRoutineOut(BaseModel):
    id: int
    weekday: int
    day_name: str
    focus: str
    exercises: str

    model_config = {"from_attributes": True}


class GymLogCreate(BaseModel):
    log_date: date
    exercise_name: str
    sets: int = 0
    reps: int = 0
    weight: float = 0
    duration: int = 0
    completed: bool = False
    notes: str | None = None


class TravelBreakCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str | None = None


class SleepLogCreate(BaseModel):
    sleep_date: date
    sleep_start: datetime | None = None
    sleep_end: datetime | None = None
    hours: float
    quality: int = Field(default=3, ge=1, le=5)
    notes: str | None = None


class DistractionLogCreate(BaseModel):
    log_date: date
    source: str = "manual"
    minutes: int = Field(default=0, ge=0)
    notes: str | None = None


class DisciplineScoreOut(BaseModel):
    score_date: date
    score: int
    status: DisciplineStatus
    breakdown: dict
    travel_mode: bool
    recovery_mode: bool
    warning_level: WarningLevel

    model_config = {"from_attributes": True}


class WeeklyReviewOut(BaseModel):
    week_start: date
    week_end: date
    weekly_score: float
    best_day: str | None
    worst_day: str | None
    missed_blocks: dict
    next_week_focus: dict
    correction_day: bool

    model_config = {"from_attributes": True}


class WarningOut(BaseModel):
    id: int
    rule_code: str
    level: WarningLevel
    message: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: str
    level: WarningLevel
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    target_date: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: date | None = None
    status: GoalStatus | None = None


class GoalOut(BaseModel):
    id: int
    title: str
    description: str | None
    target_date: date | None
    status: GoalStatus
    progress_percent: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MilestoneCreate(BaseModel):
    goal_id: int
    title: str
    target_date: date | None = None


class MilestoneUpdate(BaseModel):
    title: str | None = None
    target_date: date | None = None
    completed: bool | None = None


class MilestoneOut(BaseModel):
    id: int
    goal_id: int
    title: str
    target_date: date | None
    completed: bool

    model_config = {"from_attributes": True}


class LifeTaskCreate(BaseModel):
    goal_id: int | None = None
    milestone_id: int | None = None
    title: str
    due_date: date | None = None
    estimated_minutes: int | None = None


class LifeTaskUpdate(BaseModel):
    title: str | None = None
    status: TaskStatus | None = None
    due_date: date | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None


class LifeTaskOut(BaseModel):
    id: int
    goal_id: int | None
    milestone_id: int | None
    title: str
    status: TaskStatus
    due_date: date | None
    estimated_minutes: int | None
    actual_minutes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HabitCreate(BaseModel):
    title: str
    frequency: str = "daily"


class HabitOut(BaseModel):
    id: int
    title: str
    frequency: str
    current_streak: int
    longest_streak: int

    model_config = {"from_attributes": True}


class HabitLogCreate(BaseModel):
    habit_id: int
    log_date: date
    completed: bool = True


class DailyCheckInCreate(BaseModel):
    log_date: date
    mood_score: int | None = None
    focus_score: int | None = None
    productivity_score: int | None = None
    notes: str | None = None


class DailyCheckInOut(BaseModel):
    id: int
    log_date: date
    mood_score: int | None
    focus_score: int | None
    productivity_score: int | None
    notes: str | None

    model_config = {"from_attributes": True}


class FocusSessionCreate(BaseModel):
    task_id: int | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: int


class FocusSessionOut(BaseModel):
    id: int
    task_id: int | None
    start_time: datetime
    end_time: datetime | None
    duration_minutes: int

    model_config = {"from_attributes": True}
