import uuid

import pytest

from memory_agent.enums import StatutCompte
from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import Acteur
from memory_agent.services.user_service import UserService
from tests.helpers import require_id


@pytest.fixture
def service(user_repo: SqlAlchemyUserRepository, audit_repo: SqlAlchemyAuditEventRepository) -> UserService:
    return UserService(user_repo, audit_repo)


def test_creer_user(service: UserService, audit_repo: SqlAlchemyAuditEventRepository, acteur: Acteur) -> None:
    user = service.creer_user(email="jamal@example.com", nom="Jamal", acteur=acteur)

    assert user.id is not None
    assert user.statut_compte == StatutCompte.ACTIF

    historique = audit_repo.par_entite("User", require_id(user))
    assert [e.type_evenement for e in historique] == ["UserCréé"]


def test_creer_user_email_deja_utilise_leve_duplicate(service: UserService, acteur: Acteur) -> None:
    service.creer_user(email="jamal@example.com", nom="Jamal", acteur=acteur)

    with pytest.raises(DuplicateEntityError):
        service.creer_user(email="jamal@example.com", nom="Autre", acteur=acteur)


def test_consulter_user_absent_leve_not_found(service: UserService) -> None:
    with pytest.raises(EntityNotFoundError):
        service.consulter_user(uuid.uuid4())


def test_desactiver_user(
    service: UserService, audit_repo: SqlAlchemyAuditEventRepository, acteur: Acteur
) -> None:
    user = service.creer_user(email="jamal@example.com", nom="Jamal", acteur=acteur)

    desactive = service.desactiver_user(require_id(user), acteur=acteur)

    assert desactive.statut_compte == StatutCompte.DESACTIVE
    types_evenements = [e.type_evenement for e in audit_repo.par_entite("User", require_id(user))]
    assert types_evenements == ["UserCréé", "UserDésactivé"]
