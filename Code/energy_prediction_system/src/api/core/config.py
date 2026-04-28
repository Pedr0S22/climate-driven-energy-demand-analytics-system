from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Climate-Driven Energy Demand Analytics System"
    API_V1_STR: str = "/api"

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Database Settings
    DATABASE_URL: str

    # Brute Force Protection (QA13)
    MAX_FAILED_ATTEMPTS: int
    LOCKOUT_DURATION_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
