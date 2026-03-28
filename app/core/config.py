from functools import lru_cache
from typing import Literal

from pydantic import EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-this-in-development"


class Settings(BaseSettings):
    APP_NAME: str = "Backend Starter Template"
    APP_DESCRIPTION: str = (
        "Reusable FastAPI starter with auth, user management and operational defaults."
    )
    APP_VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api/v1"

    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    JWT_SECRET_KEY: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MP_ACCESS_TOKEN: str | None = None

    ALLOW_OPEN_REGISTRATION: bool = True
    AUTO_PROMOTE_FIRST_USER_TO_ADMIN: bool = True

    INITIAL_ADMIN_EMAIL: EmailStr | None = None
    INITIAL_ADMIN_PASSWORD: str | None = None
    INITIAL_ADMIN_FULL_NAME: str = "Initial Admin"

    DOCS_ENABLED: bool = True
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"
    METRICS_NAMESPACE: str = "starter"
    METRICS_SUBSYSTEM: str = "api"

    SENTRY_DSN: str | None = None
    SENTRY_SEND_DEFAULT_PII: bool = False
    SENTRY_ENABLE_LOGS: bool = False
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILE_SESSION_SAMPLE_RATE: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        env_prefix="SGI_",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return value
        raise TypeError("SGI_CORS_ORIGINS must be a comma separated string or list")

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        insecure_secret = self.JWT_SECRET_KEY == DEFAULT_JWT_SECRET
        if len(self.JWT_SECRET_KEY) < 32 and self.ENV == "prod":
            raise ValueError("SGI_JWT_SECRET_KEY must be at least 32 chars in prod")
        if self.ENV == "prod":
            if self.DEBUG:
                raise ValueError("SGI_DEBUG must be false in prod")
            if insecure_secret:
                raise ValueError("Set a strong SGI_JWT_SECRET_KEY in prod")
            if self.ALLOW_OPEN_REGISTRATION:
                raise ValueError("Disable SGI_ALLOW_OPEN_REGISTRATION in prod")
            if self.AUTO_PROMOTE_FIRST_USER_TO_ADMIN:
                raise ValueError("Disable SGI_AUTO_PROMOTE_FIRST_USER_TO_ADMIN in prod")

        if bool(self.INITIAL_ADMIN_EMAIL) != bool(self.INITIAL_ADMIN_PASSWORD):
            raise ValueError(
                "SGI_INITIAL_ADMIN_EMAIL and SGI_INITIAL_ADMIN_PASSWORD must be set together"
            )

        if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("SGI_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0")
        if self.REFRESH_TOKEN_EXPIRE_DAYS <= 0:
            raise ValueError("SGI_REFRESH_TOKEN_EXPIRE_DAYS must be greater than 0")
        if not 0 <= self.SENTRY_TRACES_SAMPLE_RATE <= 1:
            raise ValueError("SGI_SENTRY_TRACES_SAMPLE_RATE must be between 0 and 1")
        if not 0 <= self.SENTRY_PROFILE_SESSION_SAMPLE_RATE <= 1:
            raise ValueError(
                "SGI_SENTRY_PROFILE_SESSION_SAMPLE_RATE must be between 0 and 1"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
