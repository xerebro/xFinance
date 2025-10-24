"""Application configuration utilities."""

from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings, Field
from starlette.responses import ORJSONResponse, Response


class Settings(BaseSettings):
    """Runtime configuration for the backend application."""

    api_prefix: str = Field("/api", description="Base path for all API routes")
    environment: Literal["dev", "prod", "test"] = Field("dev")

    database_url: str = Field(
        "postgresql+psycopg://postgres:postgres@localhost:5432/xfinance",
        description="SQLAlchemy connection string",
    )
    duckdb_path: str = Field("./storage/xfinance.duckdb", description="DuckDB file path")
    redis_url: str = Field("redis://localhost:6379/0", description="Redis cache URL")

    sec_user_agent: str = Field(
        "xFinance/0.1 (contact@example.com)",
        description="User-Agent header to send to the SEC",
    )

    default_response_class: type[Response] = ORJSONResponse

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance for FastAPI dependency injection."""

    return Settings()
