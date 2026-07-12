import pytest

from memory_agent.settings import DEFAULT_POSTGRES_URL, TEST_DATABASE_URL, Environment, Settings


def test_defaults_to_development() -> None:
    settings = Settings()
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.resolved_database_url == DEFAULT_POSTGRES_URL
    assert settings.resolved_log_level == "DEBUG"
    assert settings.resolved_log_format == "console"


def test_environment_test_utilise_sqlite_en_memoire() -> None:
    settings = Settings(environment=Environment.TEST)
    assert settings.resolved_database_url == TEST_DATABASE_URL
    assert settings.resolved_log_level == "INFO"
    assert settings.resolved_log_format == "json"


def test_database_url_explicite_prend_le_pas_sur_le_defaut() -> None:
    settings = Settings(environment=Environment.TEST, database_url="sqlite:////tmp/custom.db")
    assert settings.resolved_database_url == "sqlite:////tmp/custom.db"


def test_production_exige_un_database_url_explicite() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(environment=Environment.PRODUCTION)


def test_production_avec_database_url_est_valide() -> None:
    settings = Settings(environment=Environment.PRODUCTION, database_url="postgresql+psycopg://prod/db")
    assert settings.resolved_database_url == "postgresql+psycopg://prod/db"
    assert settings.resolved_log_format == "json"


def test_log_level_et_format_explicites_prevalent() -> None:
    settings = Settings(log_level="WARNING", log_format="json")
    assert settings.resolved_log_level == "WARNING"
    assert settings.resolved_log_format == "json"
