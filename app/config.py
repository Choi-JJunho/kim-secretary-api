"""Application configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Slack Configuration
    slack_webhook_url: str

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Security (Optional)
    api_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
