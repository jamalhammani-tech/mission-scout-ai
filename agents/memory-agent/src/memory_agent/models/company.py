from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.models.base import Base, Timestamped, UUIDPk


class CompanyModel(Base, UUIDPk, Timestamped):
    """Référentiel partagé d'entreprises (docs/domain-model.md §1, §3) — sans propriétaire."""

    __tablename__ = "companies"

    nom: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    secteur: Mapped[str | None] = mapped_column(String(150), nullable=True)
    taille: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site_web: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ville: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pays: Mapped[str | None] = mapped_column(String(150), nullable=True)
