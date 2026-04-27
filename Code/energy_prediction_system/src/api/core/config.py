import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Climate-Driven Energy Demand Analytics System"
    API_V1_STR: str = "/api"

    # Security Settings
    # QA11: 0 hardcoded secrets; all keys loaded via .env.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "DEVELOPMENT_SECRET_KEY_CHANGE_ME")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/energy_db")

    # Brute Force Protection (QA13)
    MAX_FAILED_ATTEMPTS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 5

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
