import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_agent.enums import StatutCandidature, StatutEntretien
from memory_agent.models.base import Base, Timestamped, UUIDPk


class CandidatureModel(Base, UUIDPk, Timestamped):
    """Agrégat Candidature (docs/domain-model.md §5) — rattachée à un User propriétaire."""

    __tablename__ = "candidatures"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)

    statut: Mapped[StatutCandidature] = mapped_column(
        SAEnum(StatutCandidature, native_enum=False, length=30),
        nullable=False,
        default=StatutCandidature.REPEREE,
    )

    entretiens: Mapped[list["EntretienModel"]] = relationship(cascade="all, delete-orphan")
    statut_historique: Mapped[list["CandidatureStatutHistoriqueModel"]] = relationship(cascade="all, delete-orphan")
    contacts: Mapped[list["CandidatureContactModel"]] = relationship(cascade="all, delete-orphan")


class EntretienModel(Base, UUIDPk, Timestamped):
    __tablename__ = "entretiens"

    candidature_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False)
    statut: Mapped[StatutEntretien] = mapped_column(
        SAEnum(StatutEntretien, native_enum=False, length=20), nullable=False, default=StatutEntretien.PLANIFIE
    )
    type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_prevue: Mapped[datetime | None] = mapped_column(nullable=True)
    date_realisee: Mapped[datetime | None] = mapped_column(nullable=True)
    preparation: Mapped[str | None] = mapped_column(String(8000), nullable=True)
    compte_rendu: Mapped[str | None] = mapped_column(String(8000), nullable=True)


class CandidatureStatutHistoriqueModel(Base, UUIDPk):
    """VO HistoriqueStatut : liste horodatée des transitions de statut."""

    __tablename__ = "candidature_statut_historique"

    candidature_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False)
    statut_precedent: Mapped[StatutCandidature | None] = mapped_column(
        SAEnum(StatutCandidature, native_enum=False, length=30), nullable=True
    )
    statut_nouveau: Mapped[StatutCandidature] = mapped_column(
        SAEnum(StatutCandidature, native_enum=False, length=30), nullable=False
    )
    horodatage: Mapped[datetime] = mapped_column(nullable=False)
    motif: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class CandidatureContactModel(Base, UUIDPk):
    __tablename__ = "candidature_contacts"

    candidature_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contacts.id"), nullable=False)

    __table_args__ = (UniqueConstraint("candidature_id", "contact_id", name="uq_candidature_contact"),)
