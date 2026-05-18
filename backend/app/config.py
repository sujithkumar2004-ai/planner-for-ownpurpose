from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://finalplanner:finalplanner@localhost:5432/finalplanner"
    direct_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    resend_api_key: str = ""
    email_from: str = "FinalPlanner <alerts@finalplanner.local>"
    email_to: str = "skpersonal04@gmail.com"
    sentry_dsn: str = ""
    timezone: str = "Asia/Kolkata"
    run_production_seed: bool = False
    production_seed_email: str = ""
    production_seed_name: str = "Sujith"
    production_seed_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        return normalize_sqlalchemy_url(self.database_url)

    @property
    def migration_database_url(self) -> str:
        return normalize_sqlalchemy_url(self.direct_url or self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_sqlalchemy_url(url: str) -> str:
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "pgbouncer"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
