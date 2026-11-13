"""Application settings loaded from environment variables or backend/.env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", ".env"),
        extra="ignore",
    )

    app_name: str = "SmartWait"
    database_url: str = "postgresql+psycopg2://postgres:smartwait@localhost:5432/smartwait"
    jwt_secret_key: str = "dev-only-secret-change-me-please-use-32-plus-characters"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
