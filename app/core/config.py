from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Add additional settings as needed. Keep secrets out of VCS; use a .env file
    for local development.
    """

    environment: str = "development"
    openai_api_key: str | None = None
    # Database & auth placeholders
    database_url: str | None = None  # e.g. postgresql+psycopg://user:pass@host:5432/db
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
