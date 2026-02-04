"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database (SQLite for development, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./grocery_mvp.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    admin_api_key: str = "dev-admin-key"
    access_token_expire_days: int = 7

    # Firebase
    firebase_project_id: str = "grocery-mvp-db07d"
    firebase_credentials_path: Optional[str] = None

    # App Settings
    app_env: str = "development"
    debug: bool = True
    app_name: str = "Danish Grocery MVP"
    app_url: str = "http://localhost:8000"

    # Business Settings
    delivery_fee: float = 29.00
    currency: str = "DKK"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
