from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from memory_agent.enums import CategorieSkill
from memory_agent.models import Base
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.company import Company
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from memory_agent.settings import TEST_DATABASE_URL


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


@pytest.fixture
def user(session: Session) -> User:
    return SqlAlchemyUserRepository(session).sauvegarder(User(email="jamal@example.com", nom="Jamal"))


@pytest.fixture
def skill(session: Session) -> Skill:
    return SqlAlchemySkillRepository(session).sauvegarder(
        Skill(nom="React", categorie=CategorieSkill.FRAMEWORK, aliases=["ReactJS"])
    )


@pytest.fixture
def company(session: Session) -> Company:
    return SqlAlchemyCompanyRepository(session).sauvegarder(Company(nom="Acme Corp", secteur="finance"))
