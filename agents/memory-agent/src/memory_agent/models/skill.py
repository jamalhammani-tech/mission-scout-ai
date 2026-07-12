import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_agent.enums import CategorieSkill
from memory_agent.models.base import Base, Timestamped, UUIDPk


class SkillModel(Base, UUIDPk, Timestamped):
    """Référentiel partagé de compétences (docs/domain-model.md §1, §3) — sans propriétaire."""

    __tablename__ = "skills"

    nom: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    categorie: Mapped[CategorieSkill] = mapped_column(
        SAEnum(CategorieSkill, native_enum=False, length=20), nullable=False, default=CategorieSkill.AUTRE
    )

    aliases: Mapped[list["SkillAliasModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class SkillAliasModel(Base, UUIDPk):
    __tablename__ = "skill_aliases"

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    libelle: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)

    skill: Mapped["SkillModel"] = relationship(back_populates="aliases")

    __table_args__ = (UniqueConstraint("skill_id", "libelle", name="uq_skill_alias"),)
