"""Paramètres centralisés (docs/adr/0003-developer-experience-quality.md).

Une seule source de vérité pour la configuration du Memory Agent, résolue à partir
des variables d'environnement (voir config/.env.example) et sensible à l'environnement
d'exécution (`development` / `test` / `production`).
"""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parents[1]

DEFAULT_POSTGRES_URL = "postgresql+psycopg://memory_agent:memory_agent@localhost:5432/memory_agent"

# Réservé aux tests unitaires (docs/adr/0002-postgresql-docker-compose.md) : n'est utilisé
# que lorsque `environment=test` et qu'aucun DATABASE_URL explicite n'est fourni.
TEST_DATABASE_URL = "sqlite:///:memory:"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / "config" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.DEVELOPMENT
    database_url: str | None = None
    log_level: str | None = None
    log_format: Literal["json", "console"] | None = None

    @model_validator(mode="after")
    def _require_explicit_database_url_in_production(self) -> "Settings":
        if self.environment is Environment.PRODUCTION and not self.database_url:
            raise ValueError("DATABASE_URL doit être défini explicitement quand environment=production.")
        return self

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.environment is Environment.TEST:
            return TEST_DATABASE_URL
        return DEFAULT_POSTGRES_URL

    @property
    def resolved_log_level(self) -> str:
        if self.log_level:
            return self.log_level
        return "DEBUG" if self.environment is Environment.DEVELOPMENT else "INFO"

    @property
    def resolved_log_format(self) -> Literal["json", "console"]:
        if self.log_format:
            return self.log_format
        return "console" if self.environment is Environment.DEVELOPMENT else "json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
