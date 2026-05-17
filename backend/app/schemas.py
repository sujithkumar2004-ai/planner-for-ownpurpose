from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import DisciplineStatus, TaskCategory, WarningLevel


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
