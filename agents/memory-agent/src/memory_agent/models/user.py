from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from memory_agent.enums import StatutCompte
from memory_agent.models.base import Base, Timestamped, UUIDPk


class UserModel(Base, UUIDPk, Timestamped):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    statut_compte: Mapped[StatutCompte] = mapped_column(
        SAEnum(StatutCompte, native_enum=False, length=20), nullable=False, default=StatutCompte.ACTIF
    )
