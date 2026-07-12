import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_agent.enums import NiveauCompetence, SourceType, StatutQualification
from memory_agent.models.base import Base, Timestamped, UUIDPk


class MissionModel(Base, UUIDPk, Timestamped):
    """Agrégat Mission (docs/domain-model.md §5) — rattachée à un User propriétaire."""

    __tablename__ = "missions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)

    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(8000), nullable=True)

    tjm_min: Mapped[float | None] = mapped_column(nullable=True)
    tjm_max: Mapped[float | None] = mapped_column(nullable=True)
    tjm_devise: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    tjm_unite: Mapped[str] = mapped_column(String(10), nullable=False, default="jour")

    statut_qualification: Mapped[StatutQualification] = mapped_column(
        SAEnum(StatutQualification, native_enum=False, length=20),
        nullable=False,
        default=StatutQualification.NON_QUALIFIEE,
    )
    score_qualification: Mapped[float | None] = mapped_column(nullable=True)
    motif_qualification: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Source (VO, docs/domain-model.md §8)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType, native_enum=False, length=30), nullable=False)
    source_reference_externe: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_agent_responsable: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_importe_le: Mapped[datetime | None] = mapped_column(nullable=True)

    competences_requises: Mapped[list["MissionCompetenceRequiseModel"]] = relationship(
        cascade="all, delete-orphan"
    )
    contacts: Mapped[list["MissionContactModel"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "uq_mission_user_reference_externe",
            "user_id",
            "source_reference_externe",
            unique=True,
            sqlite_where=text("source_reference_externe IS NOT NULL"),
            postgresql_where=text("source_reference_externe IS NOT NULL"),
        ),
    )


class MissionCompetenceRequiseModel(Base, UUIDPk):
    """VO CompétenceRequise : SkillId + niveau requis + obligatoire/souhaitée."""

    __tablename__ = "mission_competences_requises"

    mission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), nullable=False)
    niveau_requis: Mapped[NiveauCompetence | None] = mapped_column(
        SAEnum(NiveauCompetence, native_enum=False, length=20), nullable=True
    )
    obligatoire: Mapped[bool] = mapped_column(nullable=False, default=True)

    __table_args__ = (UniqueConstraint("mission_id", "skill_id", name="uq_mission_competence"),)


class MissionContactModel(Base, UUIDPk):
    """Mission -- source 0..n --> Contact (docs/domain-model.md §2)."""

    __tablename__ = "mission_contacts"

    mission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contacts.id"), nullable=False)

    __table_args__ = (UniqueConstraint("mission_id", "contact_id", name="uq_mission_contact"),)
