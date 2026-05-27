from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import DisciplineStatus, ExamDateStatus, GoalStatus, StudyTaskType, TaskCategory, TaskStatus, WarningLevel


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
    wake_up_time: str | None = None
    sleep_time: str | None = None
    study_hours_completed: float = 0.0
    gym_completed: bool = False
    distraction_minutes: int = 0
    mood_score: int | None = None
    energy_score: int | None = None
    focus_score: int | None = None
    productivity_score: int | None = None
    todays_win: str | None = None
    todays_failure: str | None = None
    notes: str | None = None


class DailyCheckInOut(BaseModel):
    id: int
    log_date: date
    wake_up_time: str | None
    sleep_time: str | None
    study_hours_completed: float
    gym_completed: bool
    distraction_minutes: int
    mood_score: int | None
    energy_score: int | None
    focus_score: int | None
    productivity_score: int | None
    todays_win: str | None
    todays_failure: str | None
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


class ExamDateOut(BaseModel):
    id: int
    exam_date: date
    label: str
    source_url: str | None
    source_name: str | None
    status: ExamDateStatus
    manually_overridden: bool
    refreshed_at: datetime | None

    model_config = {"from_attributes": True}


class SyllabusTopicOut(BaseModel):
    id: int
    name: str
    difficulty: int
    estimated_hours: float
    progress_percent: float
    weak_score: float
    source_ref: str | None

    model_config = {"from_attributes": True}


class SyllabusSubjectOut(BaseModel):
    id: int
    name: str
    weight: float
    topics: list[SyllabusTopicOut] = []

    model_config = {"from_attributes": True}


class BackendExamOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    active: bool
    dates: list[ExamDateOut] = []
    subjects: list[SyllabusSubjectOut] = []

    model_config = {"from_attributes": True}


class ExamDateOverride(BaseModel):
    exam_date: date
    label: str = "Main exam"
    source_name: str | None = "Manual override"


class StudyPlanCreate(BaseModel):
    exam_id: int
    active: bool = True
    available_hours_per_day: float = Field(default=4.0, ge=0.5, le=12)
    priority: int = Field(default=3, ge=1, le=5)
    start_date: date = date(2026, 6, 1)
    end_date: date = date(2027, 6, 1)


class GeneratedTaskOut(BaseModel):
    id: int
    exam_id: int | None
    exam_name: str | None = None
    topic_id: int | None
    topic_name: str | None = None
    task_date: date
    title: str
    task_type: str
    status: str
    estimated_minutes: int
    priority: int
    generated_reason: str | None

    model_config = {"from_attributes": True}


class GeneratedTaskUpdate(BaseModel):
    status: TaskStatus
    minutes_spent: int = Field(default=0, ge=0, le=720)
    notes: str | None = None


class CalendarEventCreate(BaseModel):
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    event_type: str = "manual"


class CalendarEventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    completed: bool | None = None


class CalendarEventOut(BaseModel):
    id: int
    generated_task_id: int | None
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    event_type: str
    completed: bool

    model_config = {"from_attributes": True}


class TravelModeOut(BaseModel):
    enabled: bool
    start_date: date | None
    end_date: date | None
    allow_mock_tests: bool
    daily_minutes: int
    notes: str | None

    model_config = {"from_attributes": True}


class TravelModeUpdate(BaseModel):
    enabled: bool
    start_date: date | None = None
    end_date: date | None = None
    allow_mock_tests: bool = False
    daily_minutes: int = Field(default=90, ge=15, le=360)
    notes: str | None = None


class SyllabusTopicUpdate(BaseModel):
    progress_percent: float | None = Field(default=None, ge=0, le=100)
    weak_score: float | None = Field(default=None, ge=0, le=100)


class MockScoreCreate(BaseModel):
    exam_id: int
    taken_on: date
    score: float = Field(ge=0)
    max_score: float = Field(default=100, gt=0)
    analysis: str | None = None
    weak_topics: dict = {}
