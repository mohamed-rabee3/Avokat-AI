from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # SQLite Database settings
    database_url: str = "sqlite+aiosqlite:///./avokat.db"
    
    # Neo4j Aura Cloud Database settings
    neo4j_uri: str = "neo4j+s://xxxxxxxx.databases.neo4j.io"  # Default fallback
    neo4j_username: str = "neo4j"  # Default fallback
    neo4j_password: str = ""  # Default fallback
    neo4j_database: str = "neo4j"
    
    # API settings
    api_title: str = "Avokat AI API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()