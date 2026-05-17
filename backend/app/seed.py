from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyTask, ExamTopic, ExamTrack, GymRoutine, Project, TaskCategory, User, UserSettings, WarningLevel, WarningRule


FIXED_SCHEDULE = [
    ("Exam Common Foundation", TaskCategory.EXAM_FOUNDATION, "07:00", "09:30"),
    ("Backend Engineering", TaskCategory.BACKEND, "10:00", "13:00"),
    ("LLM / Agentic AI", TaskCategory.LLM_AGENTIC_AI, "14:00", "17:00"),
    ("Gym", TaskCategory.GYM, "17:30", "18:30"),
    ("Specialized Exam Rotation", TaskCategory.EXAM_ROTATION, "18:30", "20:30"),
    ("Revision / Light Study", TaskCategory.REVISION, "21:15", "22:45"),
    ("Planning / Journal", TaskCategory.JOURNAL, "22:45", "23:15"),
]

EXAMS = {
    "CAT 2026": ("2026-11-29", ["VARC", "LRDI", "Quant"]),
    "GATE DA": (
        "2026-02-08",
        ["probability/statistics", "linear algebra", "calculus/optimization", "programming/DSA", "DBMS/warehousing", "ML", "AI"],
    ),
    "GATE Mechanical": (
        "2026-02-08",
        ["engineering mathematics", "applied mechanics/design", "fluids/thermal", "materials/manufacturing/industrial"],
    ),
    "IIT JAM Maths": (
        "2026-02-15",
        ["real analysis", "multivariable calculus", "differential equations", "linear algebra", "algebra/groups"],
    ),
    "IIT JAM Physics": (
        "2026-02-15",
        ["mathematical methods", "mechanics", "optics/waves", "electricity/magnetism", "thermodynamics", "modern physics", "solid state/electronics"],
    ),
}

GYM_ROUTINES = [
    (0, "Monday", "Push day - chest, shoulders, triceps", "Bench press, incline dumbbell press, shoulder press, lateral raise, triceps pushdown"),
    (1, "Tuesday", "Pull day - back, biceps", "Lat pulldown, seated row, one-arm row, face pull, barbell curl"),
    (2, "Wednesday", "Legs + core", "Squat, leg press, Romanian deadlift, calf raise, plank"),
    (3, "Thursday", "Upper body mixed", "Push-ups, rows, shoulder press, pulldowns, arms superset"),
    (4, "Friday", "Full body + conditioning", "Deadlift pattern, kettlebell swings, sled/cardio intervals, farmer carry"),
]

WARNING_RULES = [
    ("missed_backend_2_days", "Missed backend block 2 days continuously", WarningLevel.ORANGE),
    ("missed_llm_2_days", "Missed LLM block 2 days continuously", WarningLevel.ORANGE),
    ("no_gym_3_weekdays", "No gym completion for 3 weekdays", WarningLevel.ORANGE),
    ("no_mock_14_days", "No mock test for 14 days", WarningLevel.RED),
    ("no_revision_5_days", "No revision for 5 days", WarningLevel.ORANGE),
    ("topic_backlog_25", "Exam topic backlog above 25%", WarningLevel.RED),
    ("travel_over_14", "Travel break exceeds 14 days", WarningLevel.RED),
    ("second_travel_attempt", "Second travel break attempt", WarningLevel.RED),
    ("daily_below_60", "Daily completion below 60%", WarningLevel.YELLOW),
    ("weekly_below_70", "Weekly score below 70%", WarningLevel.ORANGE),
    ("low_sleep_3_days", "Sleep below 6 hours for 3 days", WarningLevel.RED),
    ("recovery_mode", "Daily score below 50 for 2 consecutive days", WarningLevel.RED),
    ("mandatory_block_missed", "A non-negotiable Monk Mode block was missed", WarningLevel.RED),
]

BACKEND_ROADMAP = ["FastAPI", "Express.js", "SQL", "PostgreSQL", "MySQL", "SQLAlchemy", "Sequelize", "JWT auth", "Redis", "Docker", "Queues", "System Design", "API Design", "Deployment", "Monitoring"]
LLM_ROADMAP = ["Prompt Engineering", "RAG", "Embeddings", "Vector DB", "LangChain", "LangGraph", "Agents", "Tool Calling", "Memory", "Evaluation", "Observability", "Ollama", "OpenAI APIs", "Multi-agent systems"]


def seed_user_defaults(db: Session, user: User) -> None:
    today = date.today()
    if not db.scalar(select(DailyTask).where(DailyTask.user_id == user.id)):
        for offset in range(30):
            day = today + timedelta(days=offset)
            for title, category, start_time, end_time in FIXED_SCHEDULE:
                db.add(DailyTask(user_id=user.id, task_date=day, title=title, category=category, start_time=start_time, end_time=end_time))

    if not db.scalar(select(ExamTrack).where(ExamTrack.user_id == user.id)):
        for name, (exam_date, topics) in EXAMS.items():
            exam = ExamTrack(user_id=user.id, name=name, exam_date=date.fromisoformat(exam_date), target_score="High percentile / qualifying rank")
            db.add(exam)
            db.flush()
            for topic in topics:
                db.add(ExamTopic(user_id=user.id, exam_id=exam.id, name=topic, planned_units=10, completed_units=0, backlog_percent=100))

    if not db.scalar(select(GymRoutine).where(GymRoutine.user_id == user.id)):
        for weekday, day_name, focus, exercises in GYM_ROUTINES:
            db.add(GymRoutine(user_id=user.id, weekday=weekday, day_name=day_name, focus=focus, exercises=exercises))

    if not db.scalar(select(WarningRule).where(WarningRule.user_id == user.id)):
        for code, description, level in WARNING_RULES:
            db.add(WarningRule(user_id=user.id, code=code, description=description, level=level))

    if not db.scalar(select(Project).where(Project.user_id == user.id)):
        for index, name in enumerate(BACKEND_ROADMAP):
            db.add(Project(user_id=user.id, name=name, track="backend", order_index=index))
        for index, name in enumerate(LLM_ROADMAP):
            db.add(Project(user_id=user.id, name=name, track="llm_agentic_ai", order_index=index))

    if not db.scalar(select(UserSettings).where(UserSettings.user_id == user.id)):
        db.add(UserSettings(user_id=user.id))

    db.commit()
