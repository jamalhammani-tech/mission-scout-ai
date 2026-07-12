"""Helper interne partagé par les services pour émettre un AuditEvent (docs/domain-model.md §9).

Chaque cas d'usage qui modifie un agrégat en émet un — voir docs/adr/0003 et 0004.
"""

import uuid
from typing import Any

from memory_agent.repositories.interfaces import AuditEventRepository
from memory_agent.schemas.audit import AuditEvent
from memory_agent.schemas.common import Acteur


def enregistrer_evenement(
    audit_repo: AuditEventRepository,
    *,
    type_evenement: str,
    entite_type: str,
    entite_id: uuid.UUID,
    acteur: Acteur,
    proprietaire_user_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    audit_repo.enregistrer(
        AuditEvent(
            type_evenement=type_evenement,
            entite_type=entite_type,
            entite_id=entite_id,
            acteur=acteur,
            proprietaire_user_id=proprietaire_user_id,
            details=details,
        )
    )
