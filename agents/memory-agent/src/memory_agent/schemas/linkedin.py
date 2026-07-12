import uuid
from datetime import datetime

from memory_agent.enums import ExpediteurMessage, StatutConversation, StatutPost
from memory_agent.schemas.common import Metriques, SchemaBase, Tag


class LinkedInProfile(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    titre_affiche: str | None = None
    resume: str | None = None
    derniere_synchronisation: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LinkedInPost(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    linkedin_profile_id: uuid.UUID
    contenu: str
    statut: StatutPost = StatutPost.BROUILLON
    date_planifiee: datetime | None = None
    date_publication: datetime | None = None
    metriques: Metriques = Metriques()
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Message(SchemaBase):
    id: uuid.UUID | None = None
    expediteur: ExpediteurMessage
    contenu: str
    horodatage: datetime


class LinkedInConversation(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    contact_id: uuid.UUID
    statut: StatutConversation = StatutConversation.ACTIVE
    messages: list[Message] = []
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
