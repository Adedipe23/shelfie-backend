from typing import Literal, Optional

from pydantic import ConfigDict, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Integrated Supermarket Management System (ISMS)"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Backend API for the Integrated Supermarket Management System"

    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    ENV_MODE: Literal["development", "testing", "production"] = "development"
    SQLITE_DATABASE_URI: str = "sqlite+aiosqlite:///./isms.db"
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        values = info.data  # This is the correct way in Pydantic v2
        if values.get("ENV_MODE") == "production":
            if not all(
                [
                    values.get("POSTGRES_SERVER"),
                    values.get("POSTGRES_USER"),
                    values.get("POSTGRES_PASSWORD"),
                    values.get("POSTGRES_DB"),
                ]
            ):
                raise ValueError(
                    "In production mode, PostgreSQL connection details must be provided"
                )
            # Build PostgreSQL connection string manually since Pydantic v2 changed the API
            return f"postgresql+asyncpg://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_SERVER']}/{values['POSTGRES_DB'] or ''}"
        return values["SQLITE_DATABASE_URI"]

    # Security settings
    SECRET_KEY: str = "development_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Logging settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Performance settings
    WORKERS: int = 4
    MAX_CONNECTIONS: int = 100
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 30

    # Security settings
    SECURE_HEADERS: bool = False
    HTTPS_ONLY: bool = False

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # Monitoring
    HEALTH_CHECK_ENABLED: bool = True
    METRICS_ENABLED: bool = False

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Allow extra environment variables (e.g., from Dokploy)
    )


from functools import lru_cache


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
