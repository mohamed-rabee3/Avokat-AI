from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./avokat.db"
    
    # API settings
    api_title: str = "Avokat AI API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()