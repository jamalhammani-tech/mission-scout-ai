import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.enums import SourceType, TypeDocument
from memory_agent.models.base import Base, Timestamped, UUIDPk


class DocumentModel(Base, UUIDPk, Timestamped):
    """Agrégat Document (docs/domain-model.md §5) — rattaché à un User propriétaire.

    Chaque ligne représente une version concrète d'un document ; `previous_version_id`
    chaîne les versions successives d'un même document logique (VO Version).
    """

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mission_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("missions.id"), nullable=True)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)

    type: Mapped[TypeDocument] = mapped_column(SAEnum(TypeDocument, native_enum=False, length=30), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_fichier: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Source (VO, docs/domain-model.md §8)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType, native_enum=False, length=30), nullable=False)
    source_reference_externe: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_agent_responsable: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_importe_le: Mapped[datetime | None] = mapped_column(nullable=True)
