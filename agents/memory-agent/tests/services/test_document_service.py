import uuid

import pytest

from memory_agent.enums import SourceType, TypeDocument
from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.document import SqlAlchemyDocumentRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.schemas.common import Acteur, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.mission import Mission
from memory_agent.schemas.user import User
from memory_agent.services.document_service import DocumentService
from tests.helpers import require_id


@pytest.fixture
def service(
    document_repo: SqlAlchemyDocumentRepository,
    mission_repo: SqlAlchemyMissionRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> DocumentService:
    return DocumentService(document_repo, mission_repo, audit_repo)


@pytest.fixture
def mission(mission_repo: SqlAlchemyMissionRepository, user: User, company: Company) -> Mission:
    return mission_repo.sauvegarder(
        Mission(
            user_id=require_id(user),
            company_id=require_id(company),
            titre="Mission DevOps",
            source=Source(type=SourceType.LINKEDIN),
        )
    )


def test_enregistrer_document_mission_inconnue_leve_not_found(
    service: DocumentService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.enregistrer_document(
            user_id=require_id(user),
            type=TypeDocument.CV,
            reference_fichier="data/cv.pdf",
            source=Source(type=SourceType.GENERATION_AGENT),
            mission_id=uuid.uuid4(),
            acteur=acteur,
        )


def test_enregistrer_document_version_precedente_inconnue_leve_not_found(
    service: DocumentService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.enregistrer_document(
            user_id=require_id(user),
            type=TypeDocument.CV,
            reference_fichier="data/cv.pdf",
            source=Source(type=SourceType.GENERATION_AGENT),
            previous_version_id=uuid.uuid4(),
            acteur=acteur,
        )


def test_enregistrer_document_et_consulter_par_mission(
    service: DocumentService, user: User, mission: Mission, acteur: Acteur
) -> None:
    document = service.enregistrer_document(
        user_id=require_id(user),
        type=TypeDocument.CV,
        reference_fichier="data/cv-v1.pdf",
        source=Source(type=SourceType.GENERATION_AGENT, agent_responsable="cv-agent"),
        mission_id=require_id(mission),
        acteur=acteur,
    )
    assert document.id in [d.id for d in service.consulter_par_mission(require_id(mission))]


def test_nouvelle_version_reference_la_precedente(
    service: DocumentService, user: User, mission: Mission, acteur: Acteur
) -> None:
    v1 = service.enregistrer_document(
        user_id=require_id(user),
        type=TypeDocument.CV,
        reference_fichier="data/cv-v1.pdf",
        source=Source(type=SourceType.GENERATION_AGENT),
        mission_id=require_id(mission),
        acteur=acteur,
    )
    v2 = service.enregistrer_document(
        user_id=require_id(user),
        type=TypeDocument.CV,
        reference_fichier="data/cv-v2.pdf",
        source=Source(type=SourceType.GENERATION_AGENT),
        mission_id=require_id(mission),
        previous_version_id=require_id(v1),
        acteur=acteur,
    )
    assert v2.previous_version_id == require_id(v1)
