"""Configuration settings for the Prime Anonymizer application."""

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database settings
    db_path: str = "/app/data/app.db"

    # Logging settings
    log_file_path: str = "/app/logs/app.log"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_level: str = "INFO"

    # Request limits
    max_request_size: int = 2 * 1024 * 1024  # 2MiB
    request_timeout: float = 30.0  # seconds

    # Presidio settings
    default_entities: List[str] = [
        "PERSON",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "CREDIT_CARD",
        "IBAN",
        "US_SSN",
        "LOCATION",
        "DATE_TIME",
        "IP_ADDRESS",
        "URL"
    ]

    # spaCy model
    spacy_model: str = "en_core_web_lg"

    class Config:
        env_file = ".env"
        env_prefix = "ANONYMIZER_"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


def ensure_directories() -> None:
    """Ensure required directories exist."""
    settings = get_settings()

    # Create data directory
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create logs directory
    Path(settings.log_file_path).parent.mkdir(parents=True, exist_ok=True)