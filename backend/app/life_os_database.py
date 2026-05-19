from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


life_os_database_url = get_settings().life_os_sqlalchemy_database_url
life_os_engine = create_engine(life_os_database_url, pool_pre_ping=True, pool_recycle=280)
LifeOSSessionLocal = sessionmaker(bind=life_os_engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_life_os_db() -> Generator[Session, None, None]:
    db = LifeOSSessionLocal()
    try:
        yield db
    finally:
        db.close()
