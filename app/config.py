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

    # Presidio settings - ALL supported entity types
    default_entities: List[str] = [
        # Global entities
        "PERSON",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "CREDIT_CARD",
        "CRYPTO",
        "DATE_TIME",
        "IBAN_CODE",
        "IP_ADDRESS",
        "LOCATION",
        "NRP",
        "MEDICAL_LICENSE",
        "URL",
        # US entities
        "US_BANK_NUMBER",
        "US_DRIVER_LICENSE",
        "US_ITIN",
        "US_PASSPORT",
        "US_SSN",
        # UK entities
        "UK_NHS",
        "UK_NINO",
        # Australia entities
        "AU_ABN",
        "AU_ACN",
        "AU_TFN",
        "AU_MEDICARE",
        # Singapore entities
        "SG_NRIC_FIN",
        "SG_UEN",
        # Spain entities
        "ES_NIF",
        "ES_NIE",
        # Italy entities
        "IT_FISCAL_CODE",
        "IT_DRIVER_LICENSE",
        "IT_VAT_CODE",
        "IT_PASSPORT",
        "IT_IDENTITY_CARD",
        # Poland entities
        "PL_PESEL",
        # India entities
        "IN_PAN",
        "IN_AADHAAR",
        "IN_VEHICLE_REGISTRATION",
        "IN_VOTER",
        "IN_PASSPORT",
        # Finland entities
        "FI_PERSONAL_IDENTITY_CODE",
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