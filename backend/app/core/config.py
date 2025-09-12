from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # SQLite Database settings
    database_url: str = Field(default="sqlite+aiosqlite:///./avokat.db", alias="DATABASE_URL")
    
    # Neo4j Cloud Database settings
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    
    # Gemini API Key for Graphiti LLM
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    
    # API settings
    api_title: str = Field(default="Avokat AI API", alias="API_TITLE")
    api_version: str = Field(default="1.0.0", alias="API_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()