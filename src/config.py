from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings"""

    # API Settings
    API_V0_STR: str = "/v0"
    PROJECT_NAME: str = "Shop Backend API"

    # SearchAPI Settings
    SEARCHAPI_API_KEY: str = Field(..., env="SEARCHAPI_API_KEY")

    # AgentQL Settings
    AGENTQL_API_KEY: str = Field(..., env="AGENTQL_API_KEY")

    # Spider API Settings
    SPIDER_API_KEY: str = Field(..., env="SPIDER_API_KEY")

    # Oxylabs Settings
    OXYLABS_USERNAME: str = Field(..., env="OXYLABS_USERNAME")
    OXYLABS_PROXY_USERNAME: str = Field(..., env="OXYLABS_PROXY_USERNAME")
    OXYLABS_PASSWORD: str = Field(..., env="OXYLABS_PASSWORD")

    # Logfire Settings
    LOGFIRE_TOKEN: str = Field(..., env="LOGFIRE_TOKEN")

    # Bright Data Settings
    BRIGHT_DATA_TOKEN: str = Field(..., env="BRIGHT_DATA_TOKEN")
    BRIGHT_DATA_USERNAME: str = Field(..., env="BRIGHT_DATA_USERNAME")
    BRIGHT_DATA_PASSWORD: str = Field(..., env="BRIGHT_DATA_PASSWORD")

    # Gemini Settings
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    # Scraping Settings
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    ENABLE_CACHE: bool = True

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra fields in .env file
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
