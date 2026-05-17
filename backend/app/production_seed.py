from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal
from app.models import User
from app.seed import seed_user_defaults


def seed_production_user() -> None:
    settings = get_settings()
    if not settings.run_production_seed:
        return
    email = settings.production_seed_email or settings.email_to
    if not settings.production_seed_password:
        raise RuntimeError("PRODUCTION_SEED_PASSWORD must be set when RUN_PRODUCTION_SEED=true")
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, name=settings.production_seed_name, hashed_password=hash_password(settings.production_seed_password))
            db.add(user)
            db.commit()
            db.refresh(user)
        seed_user_defaults(db, user)
    finally:
        db.close()


if __name__ == "__main__":
    seed_production_user()
