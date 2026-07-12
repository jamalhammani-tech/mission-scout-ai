import uuid

import pytest

from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.schemas.common import Acteur
from memory_agent.services.company_service import CompanyService
from tests.helpers import require_id


@pytest.fixture
def service(
    company_repo: SqlAlchemyCompanyRepository, audit_repo: SqlAlchemyAuditEventRepository
) -> CompanyService:
    return CompanyService(company_repo, audit_repo)


def test_referencer_ou_reutiliser_dedupe_par_nom(service: CompanyService, acteur: Acteur) -> None:
    premiere = service.referencer_ou_reutiliser(nom="Acme Corp", secteur="finance", acteur=acteur)
    seconde = service.referencer_ou_reutiliser(nom="Acme Corp", acteur=acteur)
    assert seconde.id == premiere.id


def test_mettre_a_jour_absent_leve_not_found(service: CompanyService, acteur: Acteur) -> None:
    with pytest.raises(EntityNotFoundError):
        service.mettre_a_jour(uuid.uuid4(), secteur="tech", acteur=acteur)


def test_mettre_a_jour(service: CompanyService, acteur: Acteur) -> None:
    company = service.referencer_ou_reutiliser(nom="Acme Corp", acteur=acteur)
    updated = service.mettre_a_jour(require_id(company), secteur="tech", ville="Paris", acteur=acteur)
    assert updated.secteur == "tech"
    assert updated.ville == "Paris"
