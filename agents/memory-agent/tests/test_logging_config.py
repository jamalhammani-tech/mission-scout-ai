import json
import logging

import pytest

from memory_agent.logging_config import JsonFormatter, configure_logging


def _make_record(msg: str, args: tuple[object, ...] = ()) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=None,
    )


def test_json_formatter_produces_valid_json() -> None:
    payload = json.loads(JsonFormatter().format(_make_record("hello %s", ("world",))))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_json_formatter_inclut_les_champs_extra() -> None:
    record = _make_record("event")
    record.user_id = "abc-123"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["extra"] == {"user_id": "abc-123"}


def test_configure_logging_json(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", format_="json")
    logging.getLogger("memory_agent.test").info("ping")

    captured = capsys.readouterr()
    payload = json.loads(captured.err.strip().splitlines()[-1])
    assert payload["message"] == "ping"


def test_configure_logging_console(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", format_="console")
    logging.getLogger("memory_agent.test").info("ping console")

    captured = capsys.readouterr()
    assert "ping console" in captured.err


def test_configure_logging_filtre_par_niveau(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="WARNING", format_="console")
    logging.getLogger("memory_agent.test").info("ne doit pas apparaître")

    captured = capsys.readouterr()
    assert captured.err == ""
