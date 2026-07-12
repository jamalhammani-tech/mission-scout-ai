import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_agent.enums import NiveauCompetence, RemotePreference, TypeCritereSkill
from memory_agent.models.base import Base, Timestamped, UUIDPk


class ProfileModel(Base, UUIDPk, Timestamped):
    """Agrégat Profil (docs/domain-model.md §5) — un par User."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    titre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    # PréférencesDeMission (VO)
    tjm_min: Mapped[float | None] = mapped_column(nullable=True)
    tjm_max: Mapped[float | None] = mapped_column(nullable=True)
    tjm_devise: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    tjm_unite: Mapped[str] = mapped_column(String(10), nullable=False, default="jour")
    remote_preference: Mapped[RemotePreference | None] = mapped_column(
        SAEnum(RemotePreference, native_enum=False, length=10), nullable=True
    )
    ville_base: Mapped[str | None] = mapped_column(String(150), nullable=True)
    perimetre_deplacement_km: Mapped[int | None] = mapped_column(nullable=True)
    disponibilite_debut: Mapped[datetime | None] = mapped_column(nullable=True)
    disponibilite_fin: Mapped[datetime | None] = mapped_column(nullable=True)

    # CritèresDeQualification (VO)
    criteres_tjm_min: Mapped[float | None] = mapped_column(nullable=True)
    criteres_remote_requis: Mapped[bool | None] = mapped_column(nullable=True)
    criteres_types_contrat_acceptes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    criteres_secteurs_exclus: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    experiences: Mapped[list["ExperienceModel"]] = relationship(cascade="all, delete-orphan")
    competences: Mapped[list["ProfileCompetenceModel"]] = relationship(cascade="all, delete-orphan")
    criteria_skills: Mapped[list["ProfileCriteriaSkillModel"]] = relationship(cascade="all, delete-orphan")


class ExperienceModel(Base, UUIDPk, Timestamped):
    __tablename__ = "experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    entreprise_nom: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intitule: Mapped[str] = mapped_column(String(255), nullable=False)
    date_debut: Mapped[datetime] = mapped_column(nullable=False)
    date_fin: Mapped[datetime | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    skills: Mapped[list["ExperienceSkillModel"]] = relationship(cascade="all, delete-orphan")


class ExperienceSkillModel(Base, UUIDPk):
    __tablename__ = "experience_skills"

    experience_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiences.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), nullable=False)

    __table_args__ = (UniqueConstraint("experience_id", "skill_id", name="uq_experience_skill"),)


class ProfileCompetenceModel(Base, UUIDPk):
    """VO CompétenceProfil : SkillId + niveau + années d'expérience."""

    __tablename__ = "profile_competences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), nullable=False)
    niveau: Mapped[NiveauCompetence] = mapped_column(
        SAEnum(NiveauCompetence, native_enum=False, length=20), nullable=False
    )
    annees_experience: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("profile_id", "skill_id", name="uq_profile_competence"),)


class ProfileCriteriaSkillModel(Base, UUIDPk):
    """VO CritèresDeQualification.SkillId[] recherchés/exclus."""

    __tablename__ = "profile_criteria_skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), nullable=False)
    type: Mapped[TypeCritereSkill] = mapped_column(
        SAEnum(TypeCritereSkill, native_enum=False, length=20), nullable=False
    )

    __table_args__ = (UniqueConstraint("profile_id", "skill_id", "type", name="uq_profile_criteria_skill"),)
