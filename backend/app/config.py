"""
Application Configuration Module
================================
Environment-based settings supporting Neo4j, API host/port, and authentication tokens.
Ensures sensitive credentials are never logged or exposed in representation strings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Neo4j Graph Database
    NEO4J_URI: str = Field(default="neo4j+s://your-instance-id.databases.neo4j.io")
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="your-secure-password")
    NEO4J_DATABASE: str = Field(default="neo4j")

    # API Configuration
    API_BASE_URL: str = Field(default="http://localhost:8000")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # Security & Demo Authorization
    DEMO_SEED_TOKEN: str = Field(
        default="hospital-academic-demo-key-2026",
        description="Authorization token required for executing the synthetic data seeder"
    )

    # CORS
    CORS_ORIGINS: str = Field(default="*")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def is_neo4j_configured(self) -> bool:
        """Checks if real credentials have been provided instead of template defaults."""
        return bool(
            self.NEO4J_URI
            and not self.NEO4J_URI.startswith("neo4j+s://your-instance")
            and self.NEO4J_PASSWORD
            and self.NEO4J_PASSWORD != "your-secure-password"
        )

    def __repr__(self) -> str:
        # Prevent secret exposure in logs/prints
        return (
            f"<Settings env={self.ENVIRONMENT} host={self.API_HOST}:{self.API_PORT} "
            f"neo4j_configured={self.is_neo4j_configured()}>"
        )


settings = Settings()
