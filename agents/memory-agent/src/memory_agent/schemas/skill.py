import uuid
from datetime import datetime

from memory_agent.enums import CategorieSkill
from memory_agent.schemas.common import SchemaBase


class Skill(SchemaBase):
    id: uuid.UUID | None = None
    nom: str
    categorie: CategorieSkill = CategorieSkill.AUTRE
    aliases: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
