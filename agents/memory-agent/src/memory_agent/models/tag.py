import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.enums import TaggableEntityType
from memory_agent.models.base import Base, UUIDPk


class TagModel(Base, UUIDPk):
    """Référentiel de tags (VO Tag) — un couple (libellé, catégorie) est unique et réutilisable."""

    __tablename__ = "tags"

    libelle: Mapped[str] = mapped_column(String(100), nullable=False)
    categorie: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (UniqueConstraint("libelle", "categorie", name="uq_tag_libelle_categorie"),)


class EntityTagModel(Base, UUIDPk):
    """Association polymorphe entre un Tag et l'une des entités taguables (docs/domain-model.md §7)."""

    __tablename__ = "entity_tags"

    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[TaggableEntityType] = mapped_column(
        SAEnum(TaggableEntityType, native_enum=False, length=30), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("tag_id", "entity_type", "entity_id", name="uq_entity_tag_unique"),
        Index("ix_entity_tags_entity", "entity_type", "entity_id"),
    )
