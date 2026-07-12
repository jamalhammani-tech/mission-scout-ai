import uuid
from datetime import datetime

from memory_agent.enums import StatutCompte
from memory_agent.schemas.common import SchemaBase


class User(SchemaBase):
    id: uuid.UUID | None = None
    email: str
    nom: str
    statut_compte: StatutCompte = StatutCompte.ACTIF
    created_at: datetime | None = None
    updated_at: datetime | None = None
