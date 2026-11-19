from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Keitaro Wrapper"
    environment: Literal["development", "test", "e2e", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://keitaro:keitaro@localhost:5432/keitaro"

    keitaro_base_url: str = "http://localhost:8001/admin_api/v1"
    keitaro_api_key: str = "dev-api-key"
    keitaro_timeout_seconds: float = Field(default=15.0, gt=0, le=120)

    # Defaults used by the campaign creator when the user does not pick them explicitly.
    default_domain_id: int | None = None
    default_campaign_group_id: int | None = None
    default_traffic_source_id: int | None = None

    geo_redirect_url: str = "https://google.com"

    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173"

    @field_validator("keitaro_base_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator(
        "default_domain_id",
        "default_campaign_group_id",
        "default_traffic_source_id",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
