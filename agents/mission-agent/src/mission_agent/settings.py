from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parents[1]


class MissionAgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / "config" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"
    mission_agent_user_email: str | None = None


@lru_cache
def get_settings() -> MissionAgentSettings:
    return MissionAgentSettings()
