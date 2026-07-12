from sqlalchemy.orm import Session

from memory_agent.enums import ActeurType
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.schemas.audit import AuditEvent
from memory_agent.schemas.common import Acteur
from memory_agent.schemas.user import User
from tests.helpers import require_id


def test_audit_event_est_immuable_et_retrouvable(session: Session, user: User) -> None:
    repo = SqlAlchemyAuditEventRepository(session)
    user_id = require_id(user)
    candidature_id = user_id  # peu importe l'entité réelle pour ce test de traçabilité

    event = repo.enregistrer(
        AuditEvent(
            type_evenement="StatutCandidatureChangé",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=Acteur(type=ActeurType.UTILISATEUR, identifiant=str(user_id)),
            proprietaire_user_id=user_id,
            details={"ancien": "postulee", "nouveau": "refusee"},
        )
    )

    assert event.id is not None
    assert event.horodatage is not None

    par_entite = repo.par_entite("Candidature", candidature_id)
    assert event.id in [e.id for e in par_entite]

    par_proprietaire = repo.par_proprietaire(user_id)
    assert event.id in [e.id for e in par_proprietaire]

    par_acteur = repo.par_acteur(Acteur(type=ActeurType.UTILISATEUR, identifiant=str(user_id)))
    assert event.id in [e.id for e in par_acteur]


def test_audit_repository_expose_uniquement_enregistrer(session: Session) -> None:
    repo = SqlAlchemyAuditEventRepository(session)
    assert not hasattr(repo, "supprimer")
    assert not hasattr(repo, "mettre_a_jour")
