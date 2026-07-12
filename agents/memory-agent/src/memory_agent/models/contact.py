import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.enums import SourceType
from memory_agent.models.base import Base, Timestamped, UUIDPk


class ContactModel(Base, UUIDPk, Timestamped):
    """Agrégat Contact (docs/domain-model.md §5) — rattaché à un User propriétaire."""

    __tablename__ = "contacts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"), nullable=True)

    nom: Mapped[str] = mapped_column(String(255), nullable=False)

    # ContactInfo (VO)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    url_linkedin: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Source (VO, docs/domain-model.md §8)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType, native_enum=False, length=30), nullable=False)
    source_reference_externe: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_agent_responsable: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_importe_le: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index(
            "uq_contact_user_email",
            "user_id",
            "email",
            unique=True,
            sqlite_where=text("email IS NOT NULL"),
            postgresql_where=text("email IS NOT NULL"),
        ),
        Index(
            "uq_contact_user_url_linkedin",
            "user_id",
            "url_linkedin",
            unique=True,
            sqlite_where=text("url_linkedin IS NOT NULL"),
            postgresql_where=text("url_linkedin IS NOT NULL"),
        ),
        Index(
            "uq_contact_user_reference_externe",
            "user_id",
            "source_reference_externe",
            unique=True,
            sqlite_where=text("source_reference_externe IS NOT NULL"),
            postgresql_where=text("source_reference_externe IS NOT NULL"),
        ),
    )
