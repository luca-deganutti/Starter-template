from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sistema Interno - Distribuidora de Ropa"
    API_V1_PREFIX: str = "/api/v1"

    ENV: str = "dev"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ropa_db"

    JWT_SECRET_KEY: str = "change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="SGI_",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
