import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parents[1]
DEFAULT_SQLITE_PATH = REPO_ROOT / "data" / "memory-agent.db"


@lru_cache
def get_database_url() -> str:
    load_dotenv(REPO_ROOT / "config" / ".env")
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
