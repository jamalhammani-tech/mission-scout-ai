import uuid
from datetime import datetime

from memory_agent.schemas.common import SchemaBase


class Company(SchemaBase):
    id: uuid.UUID | None = None
    nom: str
    secteur: str | None = None
    taille: str | None = None
    site_web: str | None = None
    ville: str | None = None
    pays: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
