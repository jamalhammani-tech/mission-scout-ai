import pytest
from sqlalchemy.orm import Session

from memory_agent.enums import ActeurType
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.candidature import SqlAlchemyCandidatureRepository
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.repositories.document import SqlAlchemyDocumentRepository
from memory_agent.repositories.linkedin import (
    SqlAlchemyLinkedInConversationRepository,
    SqlAlchemyLinkedInPostRepository,
    SqlAlchemyLinkedInProfileRepository,
)
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import Acteur


@pytest.fixture
def acteur() -> Acteur:
    return Acteur(type=ActeurType.UTILISATEUR, identifiant="test-acteur")


@pytest.fixture
def user_repo(session: Session) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


@pytest.fixture
def profile_repo(session: Session) -> SqlAlchemyProfileRepository:
    return SqlAlchemyProfileRepository(session)


@pytest.fixture
def skill_repo(session: Session) -> SqlAlchemySkillRepository:
    return SqlAlchemySkillRepository(session)


@pytest.fixture
def company_repo(session: Session) -> SqlAlchemyCompanyRepository:
    return SqlAlchemyCompanyRepository(session)


@pytest.fixture
def mission_repo(session: Session) -> SqlAlchemyMissionRepository:
    return SqlAlchemyMissionRepository(session)


@pytest.fixture
def candidature_repo(session: Session) -> SqlAlchemyCandidatureRepository:
    return SqlAlchemyCandidatureRepository(session)


@pytest.fixture
def contact_repo(session: Session) -> SqlAlchemyContactRepository:
    return SqlAlchemyContactRepository(session)


@pytest.fixture
def document_repo(session: Session) -> SqlAlchemyDocumentRepository:
    return SqlAlchemyDocumentRepository(session)


@pytest.fixture
def linkedin_profile_repo(session: Session) -> SqlAlchemyLinkedInProfileRepository:
    return SqlAlchemyLinkedInProfileRepository(session)


@pytest.fixture
def linkedin_post_repo(session: Session) -> SqlAlchemyLinkedInPostRepository:
    return SqlAlchemyLinkedInPostRepository(session)


@pytest.fixture
def linkedin_conversation_repo(session: Session) -> SqlAlchemyLinkedInConversationRepository:
    return SqlAlchemyLinkedInConversationRepository(session)


@pytest.fixture
def audit_repo(session: Session) -> SqlAlchemyAuditEventRepository:
    return SqlAlchemyAuditEventRepository(session)
