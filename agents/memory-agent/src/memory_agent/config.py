import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parents[1]

# Correspond au service `postgres` de docker-compose.yml (à la racine du repo).
DEFAULT_POSTGRES_URL = "postgresql+psycopg://memory_agent:memory_agent@localhost:5432/memory_agent"

# Réservé aux tests unitaires (docs/adr/0002-postgresql-docker-compose.md) — ne pas utiliser
# comme fallback silencieux pour le dev/prod, uniquement pour construire un engine explicite en test.
TEST_DATABASE_URL = "sqlite:///:memory:"


@lru_cache
def get_database_url() -> str:
    load_dotenv(REPO_ROOT / "config" / ".env")
    return os.getenv("DATABASE_URL", DEFAULT_POSTGRES_URL)
