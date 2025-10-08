"""
Application Configuration
Loads settings from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "CyclSales Dashboard API"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # GHL OAuth
    GHL_CLIENT_ID: str
    GHL_CLIENT_SECRET: str
    GHL_APP_ID: str
    GHL_REDIRECT_URI: str

    # GHL API
    GHL_API_BASE_URL: str = "https://services.leadconnectorhq.com"
    GHL_API_VERSION: str = "2021-07-28"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    ALLOWED_HOSTS: List[str] = ["*"]  # Set to specific domains in production
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10 MB
    RATE_LIMIT_PER_MINUTE: int = 100

    # Webhook Security (optional)
    GHL_WEBHOOK_SECRET: str = ""  # For webhook signature verification

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
