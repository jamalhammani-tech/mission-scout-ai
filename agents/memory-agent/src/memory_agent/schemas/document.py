import uuid
from datetime import datetime

from memory_agent.enums import TypeDocument
from memory_agent.schemas.common import SchemaBase, Source, Tag


class Document(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    mission_id: uuid.UUID | None = None
    previous_version_id: uuid.UUID | None = None
    type: TypeDocument
    version_label: str | None = None
    reference_fichier: str
    source: Source
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
