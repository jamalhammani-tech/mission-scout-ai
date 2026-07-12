import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.enums import ActeurType
from memory_agent.models.base import Base, UUIDPk


class AuditEventModel(Base, UUIDPk):
    """Agrégat AuditEvent (docs/domain-model.md §5, §9) — immuable, append-only.

    Aucune colonne `updated_at` : un événement ne se modifie jamais après création.
    """

    __tablename__ = "audit_events"

    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    type_evenement: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entite_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entite_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    acteur_type: Mapped[ActeurType] = mapped_column(SAEnum(ActeurType, native_enum=False, length=20), nullable=False)
    acteur_identifiant: Mapped[str] = mapped_column(String(150), nullable=False)

    proprietaire_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_audit_events_entite", "entite_type", "entite_id"),)
