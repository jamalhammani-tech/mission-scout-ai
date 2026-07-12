import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memory_agent.enums import ExpediteurMessage, StatutConversation, StatutPost
from memory_agent.models.base import Base, Timestamped, UUIDPk


class LinkedInProfileModel(Base, UUIDPk, Timestamped):
    """Agrégat LinkedInProfile (docs/domain-model.md §5) — un par User, distinct de Profil."""

    __tablename__ = "linkedin_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    titre_affiche: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    derniere_synchronisation: Mapped[datetime | None] = mapped_column(nullable=True)


class LinkedInPostModel(Base, UUIDPk, Timestamped):
    """Agrégat LinkedInPost — référence LinkedInProfileId (docs/domain-model.md §5)."""

    __tablename__ = "linkedin_posts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    linkedin_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("linkedin_profiles.id", ondelete="CASCADE"), nullable=False)

    contenu: Mapped[str] = mapped_column(String(8000), nullable=False)
    statut: Mapped[StatutPost] = mapped_column(
        SAEnum(StatutPost, native_enum=False, length=20), nullable=False, default=StatutPost.BROUILLON
    )
    date_planifiee: Mapped[datetime | None] = mapped_column(nullable=True)
    date_publication: Mapped[datetime | None] = mapped_column(nullable=True)

    # Métriques (VO)
    metriques_vues: Mapped[int | None] = mapped_column(nullable=True)
    metriques_reactions: Mapped[int | None] = mapped_column(nullable=True)
    metriques_commentaires: Mapped[int | None] = mapped_column(nullable=True)
    metriques_mesurees_le: Mapped[datetime | None] = mapped_column(nullable=True)


class LinkedInConversationModel(Base, UUIDPk, Timestamped):
    """Agrégat LinkedInConversation — rattachée à exactement un Contact."""

    __tablename__ = "linkedin_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    statut: Mapped[StatutConversation] = mapped_column(
        SAEnum(StatutConversation, native_enum=False, length=20), nullable=False, default=StatutConversation.ACTIVE
    )

    messages: Mapped[list["LinkedInMessageModel"]] = relationship(cascade="all, delete-orphan")


class LinkedInMessageModel(Base, UUIDPk):
    """VO Message : liste horodatée des échanges d'une LinkedInConversation."""

    __tablename__ = "linkedin_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("linkedin_conversations.id", ondelete="CASCADE"), nullable=False
    )
    expediteur: Mapped[ExpediteurMessage] = mapped_column(
        SAEnum(ExpediteurMessage, native_enum=False, length=20), nullable=False
    )
    contenu: Mapped[str] = mapped_column(String(4000), nullable=False)
    horodatage: Mapped[datetime] = mapped_column(nullable=False)
