"""Dynamic exam planner fields

Revision ID: 20260526_0002
Revises: 20260518_0001
Create Date: 2026-05-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20260526_0002"
down_revision = "20260518_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("study_plans", sa.Column("priority", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("study_plans", sa.Column("start_date", sa.Date(), nullable=False, server_default="2026-06-01"))
    op.add_column("study_plans", sa.Column("end_date", sa.Date(), nullable=False, server_default="2027-06-01"))
    op.add_column("travel_mode_settings", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("travel_mode_settings", sa.Column("end_date", sa.Date(), nullable=True))

    op.create_table(
        "mock_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("taken_on", sa.Date(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("weak_topics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mock_scores_user_id", "mock_scores", ["user_id"])
    op.create_index("ix_mock_scores_exam_id", "mock_scores", ["exam_id"])
    op.create_index("ix_mock_scores_taken_on", "mock_scores", ["taken_on"])

    op.create_table(
        "generated_task_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("minutes_spent", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["generated_daily_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_task_logs_user_id", "generated_task_logs", ["user_id"])
    op.create_index("ix_generated_task_logs_task_id", "generated_task_logs", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_generated_task_logs_task_id", table_name="generated_task_logs")
    op.drop_index("ix_generated_task_logs_user_id", table_name="generated_task_logs")
    op.drop_table("generated_task_logs")
    op.drop_index("ix_mock_scores_taken_on", table_name="mock_scores")
    op.drop_index("ix_mock_scores_exam_id", table_name="mock_scores")
    op.drop_index("ix_mock_scores_user_id", table_name="mock_scores")
    op.drop_table("mock_scores")
    op.drop_column("travel_mode_settings", "end_date")
    op.drop_column("travel_mode_settings", "start_date")
    op.drop_column("study_plans", "end_date")
    op.drop_column("study_plans", "start_date")
    op.drop_column("study_plans", "priority")
