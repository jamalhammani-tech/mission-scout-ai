import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import StatutPost, TaggableEntityType
from memory_agent.models.linkedin import (
    LinkedInConversationModel,
    LinkedInMessageModel,
    LinkedInPostModel,
    LinkedInProfileModel,
)
from memory_agent.repositories._tags import get_tags, sync_tags
from memory_agent.schemas.common import Metriques
from memory_agent.schemas.linkedin import LinkedInConversation, LinkedInPost, LinkedInProfile, Message


class SqlAlchemyLinkedInProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profile(self, user_id: uuid.UUID) -> LinkedInProfile | None:
        stmt = select(LinkedInProfileModel).where(LinkedInProfileModel.user_id == user_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return LinkedInProfile.model_validate(model) if model else None

    def sauvegarder(self, profile: LinkedInProfile) -> LinkedInProfile:
        model = self.session.get(LinkedInProfileModel, profile.id) if profile.id else None
        if model is None:
            model = LinkedInProfileModel(id=profile.id or uuid.uuid4(), user_id=profile.user_id)
            self.session.add(model)

        model.user_id = profile.user_id
        model.titre_affiche = profile.titre_affiche
        model.resume = profile.resume
        model.derniere_synchronisation = profile.derniere_synchronisation

        self.session.commit()
        self.session.refresh(model)
        return LinkedInProfile.model_validate(model)


class SqlAlchemyLinkedInPostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> LinkedInPost | None:
        model = self.session.get(LinkedInPostModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[LinkedInPost]:
        stmt = select(LinkedInPostModel).where(LinkedInPostModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_statut(self, user_id: uuid.UUID, statut: StatutPost) -> list[LinkedInPost]:
        stmt = select(LinkedInPostModel).where(
            LinkedInPostModel.user_id == user_id, LinkedInPostModel.statut == statut
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, post: LinkedInPost) -> LinkedInPost:
        model = self.session.get(LinkedInPostModel, post.id) if post.id else None
        if model is None:
            model = LinkedInPostModel(id=post.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = post.user_id
        model.linkedin_profile_id = post.linkedin_profile_id
        model.contenu = post.contenu
        model.statut = post.statut
        model.date_planifiee = post.date_planifiee
        model.date_publication = post.date_publication

        model.metriques_vues = post.metriques.vues
        model.metriques_reactions = post.metriques.reactions
        model.metriques_commentaires = post.metriques.commentaires
        model.metriques_mesurees_le = post.metriques.mesurees_le

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.LINKEDIN_POST, model.id, post.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: LinkedInPostModel) -> LinkedInPost:
        return LinkedInPost(
            id=model.id,
            user_id=model.user_id,
            linkedin_profile_id=model.linkedin_profile_id,
            contenu=model.contenu,
            statut=model.statut,
            date_planifiee=model.date_planifiee,
            date_publication=model.date_publication,
            metriques=Metriques(
                vues=model.metriques_vues,
                reactions=model.metriques_reactions,
                commentaires=model.metriques_commentaires,
                mesurees_le=model.metriques_mesurees_le,
            ),
            tags=get_tags(self.session, TaggableEntityType.LINKEDIN_POST, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyLinkedInConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> LinkedInConversation | None:
        model = self.session.get(LinkedInConversationModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[LinkedInConversation]:
        stmt = select(LinkedInConversationModel).where(LinkedInConversationModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_contact(self, contact_id: uuid.UUID) -> list[LinkedInConversation]:
        stmt = select(LinkedInConversationModel).where(LinkedInConversationModel.contact_id == contact_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, conversation: LinkedInConversation) -> LinkedInConversation:
        model = self.session.get(LinkedInConversationModel, conversation.id) if conversation.id else None
        if model is None:
            model = LinkedInConversationModel(id=conversation.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = conversation.user_id
        model.contact_id = conversation.contact_id
        model.statut = conversation.statut

        existing_by_id = {m.id: m for m in model.messages}
        new_messages = []
        for msg in conversation.messages:
            msg_model = existing_by_id.get(msg.id) if msg.id else None
            if msg_model is None:
                msg_model = LinkedInMessageModel(id=msg.id or uuid.uuid4())
            msg_model.expediteur = msg.expediteur
            msg_model.contenu = msg.contenu
            msg_model.horodatage = msg.horodatage
            new_messages.append(msg_model)
        model.messages = new_messages

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.LINKEDIN_CONVERSATION, model.id, conversation.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: LinkedInConversationModel) -> LinkedInConversation:
        return LinkedInConversation(
            id=model.id,
            user_id=model.user_id,
            contact_id=model.contact_id,
            statut=model.statut,
            messages=[
                Message(id=m.id, expediteur=m.expediteur, contenu=m.contenu, horodatage=m.horodatage)
                for m in model.messages
            ],
            tags=get_tags(self.session, TaggableEntityType.LINKEDIN_CONVERSATION, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
