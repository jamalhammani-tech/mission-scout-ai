import uuid
from datetime import datetime

from memory_agent.schemas.common import ContactInfo, SchemaBase, Source, Tag


class Contact(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    company_id: uuid.UUID | None = None
    nom: str
    contact_info: ContactInfo = ContactInfo()
    source: Source
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
