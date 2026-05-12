from pydantic import model_validator
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
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str | None = None

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        """
        Assembles DATABASE_URL from components.
        This ensures that environment overrides (like DB_HOST and DB_PORT in Docker)
        always take precedence over a pre-defined DATABASE_URL string in .env.
        """
        self.DATABASE_URL = (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@" f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self

    # Brute Force Protection (QA13)
    MAX_FAILED_ATTEMPTS: int
    LOCKOUT_DURATION_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
