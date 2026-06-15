from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_api_key: str = Field(default="change-me-local-api-key", alias="APP_API_KEY")
    fmcsa_api_key: str = Field(default="replace-with-real-fmcsa-key", alias="FMCSA_API_KEY")
    fmcsa_base_url: str = Field(default="https://mobile.fmcsa.dot.gov/qc/services", alias="FMCSA_BASE_URL")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/carrier_sales",
        alias="DATABASE_URL",
    )
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    negotiation_max_rounds: int = Field(default=3, alias="NEGOTIATION_MAX_ROUNDS")
    default_max_rate_premium_percent: float = Field(default=8, alias="DEFAULT_MAX_RATE_PREMIUM_PERCENT")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
