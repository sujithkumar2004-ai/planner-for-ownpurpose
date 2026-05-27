"""Create Life OS MySQL tables

Revision ID: 20260518_0001
Revises:
Create Date: 2026-05-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20260518_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS goalstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS examdatestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS studytasktype CASCADE")

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exams_code", "exams", ["code"], unique=True)
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "COMPLETED", "ABANDONED", name="goalstatus"), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])
    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("frequency", sa.String(length=50), nullable=False),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("longest_streak", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_habits_user_id", "habits", ["user_id"])
    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=True),
        sa.Column("focus_score", sa.Integer(), nullable=True),
        sa.Column("productivity_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_user_checkin_date"),
    )
    op.create_index("ix_daily_checkins_user_id", "daily_checkins", ["user_id"])
    op.create_index("ix_daily_checkins_log_date", "daily_checkins", ["log_date"])
    op.create_table(
        "productivity_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("completed_tasks", sa.Integer(), nullable=False),
        sa.Column("pending_tasks", sa.Integer(), nullable=False),
        sa.Column("overdue_tasks", sa.Integer(), nullable=False),
        sa.Column("focus_minutes", sa.Integer(), nullable=False),
        sa.Column("productivity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_user_productivity_date"),
    )
    op.create_index("ix_productivity_logs_user_id", "productivity_logs", ["user_id"])
    op.create_index("ix_productivity_logs_log_date", "productivity_logs", ["log_date"])
    op.create_table(
        "travel_mode_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("allow_mock_tests", sa.Boolean(), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_travel_mode_settings_user_id", "travel_mode_settings", ["user_id"], unique=True)
    op.create_table(
        "exam_dates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(length=160), nullable=True),
        sa.Column("status", sa.Enum("OFFICIAL", "TENTATIVE", "MANUAL_OVERRIDE", name="examdatestatus"), nullable=False),
        sa.Column("manually_overridden", sa.Boolean(), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "label", name="uq_exam_date_label"),
    )
    op.create_index("ix_exam_dates_exam_id", "exam_dates", ["exam_id"])
    op.create_index("ix_exam_dates_exam_date", "exam_dates", ["exam_date"])
    op.create_table(
        "syllabus_subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "name", name="uq_exam_subject_name"),
    )
    op.create_index("ix_syllabus_subjects_exam_id", "syllabus_subjects", ["exam_id"])
    op.create_table(
        "milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_milestones_goal_id", "milestones", ["goal_id"])
    op.create_table(
        "habit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("habit_id", sa.Integer(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["habit_id"], ["habits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),
    )
    op.create_index("ix_habit_logs_habit_id", "habit_logs", ["habit_id"])
    op.create_index("ix_habit_logs_log_date", "habit_logs", ["log_date"])
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("available_hours_per_day", sa.Float(), nullable=False),
        sa.Column("revision_intensity", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exam_id", name="uq_user_exam_study_plan"),
    )
    op.create_index("ix_study_plans_user_id", "study_plans", ["user_id"])
    op.create_index("ix_study_plans_exam_id", "study_plans", ["exam_id"])
    op.create_table(
        "syllabus_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=220), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("estimated_hours", sa.Float(), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False),
        sa.Column("weak_score", sa.Float(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["syllabus_subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id", "name", name="uq_subject_topic_name"),
    )
    op.create_index("ix_syllabus_topics_subject_id", "syllabus_topics", ["subject_id"])
    op.create_table(
        "life_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("milestone_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "ACTIVE", "COMPLETED", "SKIPPED", "OVERDUE", name="taskstatus"), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("actual_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["milestone_id"], ["milestones.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_life_tasks_user_id", "life_tasks", ["user_id"])
    op.create_index("ix_life_tasks_goal_id", "life_tasks", ["goal_id"])
    op.create_index("ix_life_tasks_milestone_id", "life_tasks", ["milestone_id"])
    op.create_table(
        "generated_daily_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("task_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.Enum("CONCEPT", "PRACTICE", "REVISION", "MOCK", "PYQ", "FORMULA_REVIEW", "READING", "ANALYSIS", name="studytasktype"), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "ACTIVE", "COMPLETED", "SKIPPED", "OVERDUE", name="taskstatus"), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("generated_reason", sa.Text(), nullable=True),
        sa.Column("carried_from_task_id", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["syllabus_topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["carried_from_task_id"], ["generated_daily_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "task_date", "title", "task_type", name="uq_user_generated_task"),
    )
    op.create_index("ix_generated_daily_tasks_user_id", "generated_daily_tasks", ["user_id"])
    op.create_index("ix_generated_daily_tasks_task_date", "generated_daily_tasks", ["task_date"])
    op.create_index("ix_generated_daily_tasks_exam_id", "generated_daily_tasks", ["exam_id"])
    op.create_index("ix_generated_daily_tasks_topic_id", "generated_daily_tasks", ["topic_id"])
    op.create_table(
        "focus_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["life_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_focus_sessions_user_id", "focus_sessions", ["user_id"])
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("generated_task_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["generated_task_id"], ["generated_daily_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])
    op.create_index("ix_calendar_events_generated_task_id", "calendar_events", ["generated_task_id"])
    op.create_index("ix_calendar_events_start_at", "calendar_events", ["start_at"])
    op.create_index("ix_calendar_events_end_at", "calendar_events", ["end_at"])


def downgrade() -> None:
    for table in [
        "calendar_events",
        "focus_sessions",
        "generated_daily_tasks",
        "life_tasks",
        "syllabus_topics",
        "study_plans",
        "habit_logs",
        "milestones",
        "syllabus_subjects",
        "exam_dates",
        "travel_mode_settings",
        "productivity_logs",
        "daily_checkins",
        "habits",
        "goals",
        "exams",
    ]:
        op.drop_table(table)
