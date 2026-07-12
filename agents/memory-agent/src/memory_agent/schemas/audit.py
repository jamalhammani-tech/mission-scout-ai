import uuid
from datetime import datetime
from typing import Any

from memory_agent.schemas.common import Acteur, SchemaBase


class AuditEvent(SchemaBase):
    id: uuid.UUID | None = None
    horodatage: datetime | None = None
    type_evenement: str
    entite_type: str
    entite_id: uuid.UUID
    acteur: Acteur
    proprietaire_user_id: uuid.UUID | None = None
    details: dict[str, Any] | None = None
