from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base
from app import models  # noqa: F401


config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.life_os_migration_database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
LIFE_OS_TABLES = {
    "exams",
    "exam_dates",
    "syllabus_subjects",
    "syllabus_topics",
    "study_plans",
    "generated_daily_tasks",
    "calendar_events",
    "goals",
    "milestones",
    "life_tasks",
    "habits",
    "habit_logs",
    "focus_sessions",
    "travel_mode_settings",
    "daily_checkins",
    "productivity_logs",
}


def include_name(name, type_, parent_names):
    if type_ == "table":
        return name in LIFE_OS_TABLES
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.life_os_migration_database_url,
        target_metadata=target_metadata,
        include_name=include_name,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
