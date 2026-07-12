import uuid
from datetime import datetime
from typing import Any

from memory_agent.repositories.interfaces import AuditEventRepository
from memory_agent.schemas.audit import AuditEvent
from memory_agent.schemas.common import Acteur


class AuditService:
    """Cas d'usage transverses de traçabilité (docs/domain-model.md §12, §9).

    En lecture seule pour les appelants : l'écriture est un effet de bord des autres
    services (voir `services/_audit.py`), pas une action explicitement déclenchée ici —
    `enregistrer` reste exposée pour un usage direct si besoin (ex. script d'administration).
    """

    def __init__(self, audit_repo: AuditEventRepository) -> None:
        self._audit = audit_repo

    def enregistrer(
        self,
        *,
        type_evenement: str,
        entite_type: str,
        entite_id: uuid.UUID,
        acteur: Acteur,
        proprietaire_user_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return self._audit.enregistrer(
            AuditEvent(
                type_evenement=type_evenement,
                entite_type=entite_type,
                entite_id=entite_id,
                acteur=acteur,
                proprietaire_user_id=proprietaire_user_id,
                details=details,
            )
        )

    def consulter_historique_par_entite(self, entite_type: str, entite_id: uuid.UUID) -> list[AuditEvent]:
        return self._audit.par_entite(entite_type, entite_id)

    def consulter_historique_par_utilisateur(
        self, user_id: uuid.UUID, *, depuis: datetime | None = None, jusqua: datetime | None = None
    ) -> list[AuditEvent]:
        return self._audit.par_proprietaire(user_id, depuis, jusqua)

    def consulter_par_acteur(self, acteur: Acteur) -> list[AuditEvent]:
        return self._audit.par_acteur(acteur)
