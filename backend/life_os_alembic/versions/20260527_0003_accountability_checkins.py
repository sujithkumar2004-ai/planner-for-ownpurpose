"""Accountability check-in fields

Revision ID: 20260527_0003
Revises: 20260526_0002
Create Date: 2026-05-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20260527_0003"
down_revision = "20260526_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("daily_checkins", sa.Column("wake_up_time", sa.String(length=20), nullable=True))
    op.add_column("daily_checkins", sa.Column("sleep_time", sa.String(length=20), nullable=True))
    op.add_column("daily_checkins", sa.Column("study_hours_completed", sa.Float(), nullable=False, server_default="0"))
    op.add_column("daily_checkins", sa.Column("gym_completed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("daily_checkins", sa.Column("distraction_minutes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("daily_checkins", sa.Column("energy_score", sa.Integer(), nullable=True))
    op.add_column("daily_checkins", sa.Column("todays_win", sa.Text(), nullable=True))
    op.add_column("daily_checkins", sa.Column("todays_failure", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_checkins", "todays_failure")
    op.drop_column("daily_checkins", "todays_win")
    op.drop_column("daily_checkins", "energy_score")
    op.drop_column("daily_checkins", "distraction_minutes")
    op.drop_column("daily_checkins", "gym_completed")
    op.drop_column("daily_checkins", "study_hours_completed")
    op.drop_column("daily_checkins", "sleep_time")
    op.drop_column("daily_checkins", "wake_up_time")
