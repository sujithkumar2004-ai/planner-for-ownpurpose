from datetime import date, datetime, timedelta
from enum import Enum
import json
import os
import sys
import argparse
import logging

from sqlalchemy import func, select, delete, update, inspect
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    User, DailyTask, TaskLog, TravelBreak,
    DisciplineScore, WeeklyReview, RecoveryMode, AnalyticsSnapshot,
    GeneratedDailyTask, GeneratedTaskLog, CalendarEvent,
    MockTest, SyllabusTopic, StudyPlan
)
from app.life_os import ensure_exam_catalog, generate_daily_tasks, verify_planner_window

logger = logging.getLogger(__name__)

PLANNER_START_DATE = date(2026, 6, 1)
PLANNER_END_DATE = date(2027, 6, 1)
CONFIRMATION_TEXT = "RESET_PLANNER_2026"
BACKUP_ROW_LIMIT = 500

DB_DELETE_TARGETS = [
    (TaskLog, "task_logs", None),
    (DailyTask, "daily_tasks", None),
    (MockTest, "mock_tests", None),
    (TravelBreak, "travel_breaks", None),
    (DisciplineScore, "discipline_scores", None),
    (WeeklyReview, "weekly_reviews", None),
    (RecoveryMode, "recovery_modes", None),
    (AnalyticsSnapshot, "analytics_snapshots", None),
]

LIFE_DELETE_TARGETS = [
    (CalendarEvent, "calendar_events", CalendarEvent.generated_task_id.isnot(None)),
    (GeneratedTaskLog, "generated_task_logs", None),
    (GeneratedDailyTask, "generated_daily_tasks", None),
]

SKIPPED_SAFE_FILTER_TARGETS = {
    "notifications": "No planner source/category/type value exists; table intentionally left untouched.",
    "warnings": "No planner source/category/type column exists; table intentionally left untouched.",
}


def serialize_row(row):
    d = {}
    for column in row.__table__.columns:
        val = getattr(row, column.name)
        if isinstance(val, (date, datetime)):
            d[column.name] = val.isoformat()
        elif isinstance(val, Enum):
            d[column.name] = val.value
        else:
            d[column.name] = val
    return d


def _row_count(session: Session, model, where_clause=None) -> int:
    stmt = select(func.count()).select_from(model)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    return session.scalar(stmt) or 0


def _backup_table(session: Session, model, name: str, db_source: str, where_clause=None) -> dict:
    count = _row_count(session, model, where_clause)
    table_backup = {
        "count": count,
        "rows_exported": 0,
        "rows": [],
        "row_export_skipped": count > BACKUP_ROW_LIMIT,
    }
    if count <= BACKUP_ROW_LIMIT:
        stmt = select(model)
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        rows = session.scalars(stmt).all()
        table_backup["rows"] = [serialize_row(row) for row in rows]
        table_backup["rows_exported"] = len(rows)
    return {
        "metadata": {
            "table_name": name,
            "count": count,
            "db_source": db_source,
            "rows_exported": table_backup["rows_exported"],
            "row_export_skipped": table_backup["row_export_skipped"],
        },
        "table": table_backup,
    }


def perform_backup(db: Session, life_db: Session, db_tables: list, life_tables: list, admin_email: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backups_dir = os.path.join(backend_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    backup_path = os.path.join(backups_dir, f"backup_{timestamp}.json")

    backup_data = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "admin_user": admin_email,
            "target_tables": []
        },
        "tables": {}
    }

    for model, name, where_clause in DB_DELETE_TARGETS:
        if name in db_tables:
            table_backup = _backup_table(db, model, name, "db", where_clause)
            backup_data["tables"][name] = table_backup["table"]
            backup_data["metadata"]["target_tables"].append(table_backup["metadata"])

    for model, name, where_clause in LIFE_DELETE_TARGETS:
        if name in life_tables:
            table_backup = _backup_table(life_db, model, name, "life_db", where_clause)
            backup_data["tables"][name] = table_backup["table"]
            backup_data["metadata"]["target_tables"].append(table_backup["metadata"])

    if "syllabus_topics" in life_tables:
        table_backup = _backup_table(life_db, SyllabusTopic, "syllabus_topics", "life_db")
        backup_data["tables"]["syllabus_topics"] = table_backup["table"]
        backup_data["metadata"]["target_tables"].append(table_backup["metadata"])

    if "study_plans" in life_tables:
        table_backup = _backup_table(life_db, StudyPlan, "study_plans", "life_db")
        backup_data["tables"]["study_plans"] = table_backup["table"]
        backup_data["metadata"]["target_tables"].append(table_backup["metadata"])

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    logger.warning("Reset backup saved successfully to %s", backup_path)
    return backup_path


def reset_planner_data(db: Session, life_db: Session, admin_email: str) -> dict:
    if os.getenv("RESET_PLANNER_CONFIRM") != "true":
        raise ValueError("RESET_PLANNER_CONFIRM environment variable must be set to 'true'")

    db_inspector = inspect(db.get_bind())
    db_tables = db_inspector.get_table_names()

    life_db_inspector = inspect(life_db.get_bind())
    life_tables = life_db_inspector.get_table_names()

    # Clear the static catalog cache and enable bulk reset mode
    from app import life_os
    life_os.clear_life_os_caches()
    life_os._bulk_reset_mode = True

    # Perform backup of tables before we reset them
    backup_file = perform_backup(db, life_db, db_tables, life_tables, admin_email)

    results = {
        "status": "success",
        "backup_file": backup_file,
        "deleted_counts": {},
        "updated_counts": {},
        "skipped_tables": SKIPPED_SAFE_FILTER_TARGETS.copy(),
        "regenerated_users": [],
        "planner_window": {}
    }

    try:
        for model, name, where_clause in DB_DELETE_TARGETS:
            if name in db_tables:
                stmt = delete(model)
                if where_clause is not None:
                    stmt = stmt.where(where_clause)
                res = db.execute(stmt)
                results["deleted_counts"][name] = res.rowcount

        for model, name, where_clause in LIFE_DELETE_TARGETS:
            if name in life_tables:
                stmt = delete(model)
                if where_clause is not None:
                    stmt = stmt.where(where_clause)
                res = life_db.execute(stmt)
                results["deleted_counts"][name] = res.rowcount

        if "syllabus_topics" in life_tables:
            values = {"progress_percent": 0.0, "weak_score": 50.0}
            if "status" in [column["name"] for column in life_db_inspector.get_columns("syllabus_topics")]:
                values["status"] = "not_started"
            res = life_db.execute(update(SyllabusTopic).values(**values))
            results["updated_counts"]["syllabus_topics"] = res.rowcount

        if "study_plans" in life_tables:
            res = life_db.execute(update(StudyPlan).values(start_date=PLANNER_START_DATE, end_date=PLANNER_END_DATE))
            results["updated_counts"]["study_plans"] = res.rowcount

        db.commit()
        if life_db is not db:
            life_db.commit()

        users = db.scalars(select(User)).all()

        for user in users:
            ensure_exam_catalog(life_db, user.id)
            current_date = PLANNER_START_DATE
            days_count = 0
            while current_date <= PLANNER_END_DATE:
                generate_daily_tasks(life_db, user.id, current_date, force=False)
                current_date += timedelta(days=1)
                days_count += 1
            verification = verify_planner_window(life_db, user.id)

            results["regenerated_users"].append({
                "user_id": user.id,
                "email": user.email,
                "days_generated": days_count,
                "first_planner_day": verification["first_planner_day"],
                "last_planner_day": verification["last_planner_day"],
                "distinct_days": verification["distinct_days"],
                "valid_window": verification["valid"],
            })
            results["planner_window"][str(user.id)] = verification

    except Exception as e:
        db.rollback()
        if life_db is not db:
            life_db.rollback()
        raise e
    finally:
        life_os._bulk_reset_mode = False

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset FinalPlanner data safely and restart planner.")
    parser.add_argument("--confirm", required=True, help=f"Confirmation string {CONFIRMATION_TEXT}")
    args = parser.parse_args()

    if args.confirm != CONFIRMATION_TEXT:
        print(f"Error: Confirmation phrase must be exact: '{CONFIRMATION_TEXT}'")
        sys.exit(1)

    if os.getenv("RESET_PLANNER_CONFIRM") != "true":
        print("Error: RESET_PLANNER_CONFIRM environment variable must be set to 'true'")
        sys.exit(1)

    print("Initializing safe reset...")
    settings = get_settings()
    direct_url = settings.direct_url or settings.database_url
    life_direct_url = settings.life_os_direct_url or settings.life_os_database_url
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(direct_url, pool_pre_ping=True)
    life_engine = engine if life_direct_url == direct_url else create_engine(life_direct_url, pool_pre_ping=True)
    DirectSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    LifeDirectSession = DirectSession if life_engine is engine else sessionmaker(bind=life_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = DirectSession()
    life_db = db if life_engine is engine else LifeDirectSession()

    try:
        results = reset_planner_data(db, life_db, admin_email=settings.admin_email)
        print("Planner reset completed successfully!")
        print(f"Backup file: {results['backup_file']}")
        print("Deleted record counts:")
        for tbl, count in results["deleted_counts"].items():
            print(f"  - {tbl}: {count}")
        print("Updated record counts:")
        for tbl, count in results["updated_counts"].items():
            print(f"  - {tbl}: {count}")
        print("Skipped tables:")
        for tbl, reason in results["skipped_tables"].items():
            print(f"  - {tbl}: {reason}")
        print("Regenerated users:")
        for u in results["regenerated_users"]:
            print(f"  - User {u['user_id']} ({u['email']}): {u['days_generated']} days")
    except Exception as e:
        print(f"Error during reset execution: {e}")
        sys.exit(1)
    finally:
        if life_db is not db:
            life_db.close()
        db.close()
        if life_engine is not engine:
            life_engine.dispose()
        engine.dispose()
