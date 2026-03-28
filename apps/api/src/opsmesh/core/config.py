from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "OpsMesh"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://opsmesh:opsmesh@localhost:5432/opsmesh"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Auth
    secret_key: str = "change-me-in-production"


settings = Settings()
