from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://finalplanner:finalplanner@localhost:5432/finalplanner"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
