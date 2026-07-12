from memory_agent.enums import ActeurType
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.schemas.common import Acteur
from memory_agent.schemas.user import User
from memory_agent.services.audit_service import AuditService
from tests.helpers import require_id


def _service(audit_repo: SqlAlchemyAuditEventRepository) -> AuditService:
    return AuditService(audit_repo)


def test_enregistrer_et_consulter_par_entite(audit_repo: SqlAlchemyAuditEventRepository, user: User) -> None:
    service = _service(audit_repo)
    user_id = require_id(user)
    acteur = Acteur(type=ActeurType.AGENT, identifiant="mission-agent")

    event = service.enregistrer(
        type_evenement="MissionDécouverte",
        entite_type="Mission",
        entite_id=user_id,
        acteur=acteur,
        proprietaire_user_id=user_id,
        details={"source": "linkedin"},
    )

    assert event.id is not None
    historique = service.consulter_historique_par_entite("Mission", user_id)
    assert event.id in [e.id for e in historique]


def test_consulter_historique_par_utilisateur(audit_repo: SqlAlchemyAuditEventRepository, user: User) -> None:
    service = _service(audit_repo)
    user_id = require_id(user)
    acteur = Acteur(type=ActeurType.UTILISATEUR, identifiant=str(user_id))

    service.enregistrer(
        type_evenement="UserCréé",
        entite_type="User",
        entite_id=user_id,
        acteur=acteur,
        proprietaire_user_id=user_id,
    )

    historique = service.consulter_historique_par_utilisateur(user_id)
    assert len(historique) == 1


def test_consulter_par_acteur(audit_repo: SqlAlchemyAuditEventRepository, user: User) -> None:
    service = _service(audit_repo)
    user_id = require_id(user)
    acteur = Acteur(type=ActeurType.AGENT, identifiant="mission-agent")

    service.enregistrer(
        type_evenement="MissionDécouverte", entite_type="Mission", entite_id=user_id, acteur=acteur
    )

    resultats = service.consulter_par_acteur(acteur)
    assert len(resultats) == 1
