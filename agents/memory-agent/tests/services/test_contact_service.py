import uuid

import pytest

from memory_agent.enums import SourceType
from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.schemas.common import Acteur, ContactInfo, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.user import User
from memory_agent.services.contact_service import ContactService
from tests.helpers import require_id


@pytest.fixture
def service(
    contact_repo: SqlAlchemyContactRepository,
    company_repo: SqlAlchemyCompanyRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> ContactService:
    return ContactService(contact_repo, company_repo, audit_repo)


def test_ajouter_contact_company_inconnue_leve_not_found(
    service: ContactService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.ajouter_contact(
            user_id=require_id(user),
            nom="Recruteur X",
            contact_info=ContactInfo(email="r@acme.com"),
            source=Source(type=SourceType.LINKEDIN),
            company_id=uuid.uuid4(),
            acteur=acteur,
        )


def test_ajouter_contact_email_en_double_leve_duplicate(
    service: ContactService, user: User, acteur: Acteur
) -> None:
    contact_info = ContactInfo(email="r@acme.com")
    service.ajouter_contact(
        user_id=require_id(user),
        nom="Recruteur X",
        contact_info=contact_info,
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    with pytest.raises(DuplicateEntityError):
        service.ajouter_contact(
            user_id=require_id(user),
            nom="Recruteur Y",
            contact_info=contact_info,
            source=Source(type=SourceType.LINKEDIN),
            acteur=acteur,
        )


def test_ajouter_contact(service: ContactService, user: User, company: Company, acteur: Acteur) -> None:
    contact = service.ajouter_contact(
        user_id=require_id(user),
        nom="Recruteur X",
        contact_info=ContactInfo(email="r@acme.com"),
        source=Source(type=SourceType.LINKEDIN),
        company_id=require_id(company),
        acteur=acteur,
    )
    assert contact.id is not None
    assert contact.id in [c.id for c in service.consulter_par_company(require_id(company))]


def test_mettre_a_jour_contact_absent_leve_not_found(service: ContactService, acteur: Acteur) -> None:
    with pytest.raises(EntityNotFoundError):
        service.mettre_a_jour_contact(uuid.uuid4(), nom="Nouveau nom", acteur=acteur)


def test_mettre_a_jour_contact(service: ContactService, user: User, acteur: Acteur) -> None:
    contact = service.ajouter_contact(
        user_id=require_id(user),
        nom="Recruteur X",
        contact_info=ContactInfo(email="r@acme.com"),
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    updated = service.mettre_a_jour_contact(require_id(contact), nom="Recruteur X (senior)", acteur=acteur)
    assert updated.nom == "Recruteur X (senior)"


def test_consulter_plusieurs(service: ContactService, user: User, acteur: Acteur) -> None:
    c1 = service.ajouter_contact(
        user_id=require_id(user),
        nom="A",
        contact_info=ContactInfo(email="a@acme.com"),
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    c2 = service.ajouter_contact(
        user_id=require_id(user),
        nom="B",
        contact_info=ContactInfo(email="b@acme.com"),
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    resultats = service.consulter_plusieurs([require_id(c1), require_id(c2)])
    assert {c.id for c in resultats} == {c1.id, c2.id}
