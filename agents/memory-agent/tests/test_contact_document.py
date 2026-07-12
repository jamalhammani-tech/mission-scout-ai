from sqlalchemy.orm import Session

from memory_agent.enums import SourceType, TypeDocument
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.repositories.document import SqlAlchemyDocumentRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.schemas.common import ContactInfo, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.contact import Contact
from memory_agent.schemas.document import Document
from memory_agent.schemas.mission import Mission
from memory_agent.schemas.user import User
from tests.helpers import require_id


def test_contact_roundtrip_et_dedup(session: Session, user: User, company: Company) -> None:
    repo = SqlAlchemyContactRepository(session)
    user_id = require_id(user)
    company_id = require_id(company)

    saved = repo.sauvegarder(
        Contact(
            user_id=user_id,
            company_id=company_id,
            nom="Recruteur X",
            contact_info=ContactInfo(email="recruteur@acme.com"),
            source=Source(type=SourceType.LINKEDIN, reference_externe="li-conv-1"),
        )
    )

    par_email = repo.par_email(user_id, "recruteur@acme.com")
    assert par_email is not None
    assert par_email.id == saved.id

    par_ref = repo.par_reference_externe(user_id, "li-conv-1")
    assert par_ref is not None
    assert par_ref.id == saved.id

    assert saved.id in [c.id for c in repo.par_company(company_id)]


def test_document_par_mission_et_candidature(session: Session, user: User, company: Company) -> None:
    mission = SqlAlchemyMissionRepository(session).sauvegarder(
        Mission(
            user_id=require_id(user),
            company_id=require_id(company),
            titre="Mission DevOps",
            source=Source(type=SourceType.LINKEDIN),
        )
    )
    mission_id = require_id(mission)

    repo = SqlAlchemyDocumentRepository(session)
    saved = repo.sauvegarder(
        Document(
            user_id=require_id(user),
            mission_id=mission_id,
            type=TypeDocument.CV,
            version_label="v1",
            reference_fichier="data/cv/jamal-v1.pdf",
            source=Source(type=SourceType.GENERATION_AGENT, agent_responsable="cv-agent"),
        )
    )

    par_mission = repo.par_mission(mission_id)
    assert saved.id in [d.id for d in par_mission]

    par_proprietaire = repo.par_proprietaire(require_id(user))
    assert saved.id in [d.id for d in par_proprietaire]
