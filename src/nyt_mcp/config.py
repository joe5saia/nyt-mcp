"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """NYT MCP server configuration.

    Values are loaded from a `.env` file at the project root and can be
    overridden by real environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = ""
    """NYT developer API key (loaded from API_KEY env var or .env file)."""

    api_base_url: str = "https://api.nytimes.com/svc"
    """Base URL for all NYT API endpoints."""

    request_timeout: float = 30.0
    """HTTP request timeout in seconds."""
