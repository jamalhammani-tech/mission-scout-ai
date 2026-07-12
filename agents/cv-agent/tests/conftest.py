from collections.abc import Iterator

import pytest
from memory_agent.models import Base
from memory_agent.settings import TEST_DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()
