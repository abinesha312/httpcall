"""Configuration management for httpcall."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_API_KEY_SID: str
    TWILIO_API_KEY_SECRET: str
    TWILIO_TWIML_APP_SID: str
    TWILIO_FROM_NUMBER: str
    PUBLIC_BASE_URL: str


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
