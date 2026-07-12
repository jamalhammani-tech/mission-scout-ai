"""Logging structuré, configuration centralisée (docs/adr/0003-developer-experience-quality.md).

`print()` est interdit dans ce projet (appliqué par la règle ruff T20) : tout affichage
passe par `logging.getLogger(__name__)`, configuré une fois via `configure_logging()`.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Literal

from memory_agent.settings import get_settings

_STANDARD_LOG_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message"}


class JsonFormatter(logging.Formatter):
    """Une ligne JSON par entrée de log — facilement parsable par un agrégateur de logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_ATTRS and not key.startswith("_")
        }
        if extra:
            payload["extra"] = extra

        return json.dumps(payload, default=str, ensure_ascii=False)


_CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(
    level: str | None = None,
    format_: Literal["json", "console"] | None = None,
) -> None:
    """Point d'entrée unique de configuration du logging pour le process (CLI, tests, futur backend)."""
    settings = get_settings()
    resolved_level = level or settings.resolved_log_level
    resolved_format = format_ or settings.resolved_log_format

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if resolved_format == "json" else logging.Formatter(_CONSOLE_FORMAT))

    root = logging.getLogger()
    root.setLevel(resolved_level)
    root.handlers.clear()
    root.addHandler(handler)
