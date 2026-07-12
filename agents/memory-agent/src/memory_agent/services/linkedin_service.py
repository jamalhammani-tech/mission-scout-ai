import uuid
from datetime import UTC, datetime

from memory_agent.enums import ExpediteurMessage, StatutConversation, StatutPost
from memory_agent.exceptions import (
    EntityNotFoundError,
    InvalidMetricsStateError,
    InvalidStatusTransitionError,
)
from memory_agent.repositories.interfaces import (
    AuditEventRepository,
    ContactRepository,
    LinkedInConversationRepository,
    LinkedInPostRepository,
    LinkedInProfileRepository,
)
from memory_agent.schemas.common import Acteur, Metriques, Tag
from memory_agent.schemas.linkedin import LinkedInConversation, LinkedInPost, LinkedInProfile, Message
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id

_POST_TRANSITIONS: dict[StatutPost, frozenset[StatutPost]] = {
    StatutPost.BROUILLON: frozenset({StatutPost.PLANIFIE, StatutPost.PUBLIE, StatutPost.ARCHIVE}),
    StatutPost.PLANIFIE: frozenset({StatutPost.PUBLIE, StatutPost.BROUILLON, StatutPost.ARCHIVE}),
    StatutPost.PUBLIE: frozenset({StatutPost.ARCHIVE}),
    StatutPost.ARCHIVE: frozenset(),
}


class LinkedInService:
    """Cas d'usage du sous-domaine LinkedIn (docs/domain-model.md §12) : LinkedInProfile,
    LinkedInPost, LinkedInConversation."""

    def __init__(
        self,
        profile_repo: LinkedInProfileRepository,
        post_repo: LinkedInPostRepository,
        conversation_repo: LinkedInConversationRepository,
        contact_repo: ContactRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._profiles = profile_repo
        self._posts = post_repo
        self._conversations = conversation_repo
        self._contacts = contact_repo
        self._audit = audit_repo

    def synchroniser_linkedin_profile(
        self,
        user_id: uuid.UUID,
        *,
        titre_affiche: str | None = None,
        resume: str | None = None,
        acteur: Acteur,
    ) -> LinkedInProfile:
        profil = self._profiles.get_profile(user_id) or LinkedInProfile(user_id=user_id)
        profil.titre_affiche = titre_affiche
        profil.resume = resume
        profil.derniere_synchronisation = datetime.now(UTC)

        saved = self._profiles.sauvegarder(profil)
        enregistrer_evenement(
            self._audit,
            type_evenement="LinkedInProfileSynchronisé",
            entite_type="LinkedInProfile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return saved

    def consulter_linkedin_profile(self, user_id: uuid.UUID) -> LinkedInProfile:
        profil = self._profiles.get_profile(user_id)
        if profil is None:
            raise EntityNotFoundError("LinkedInProfile", user_id)
        return profil

    def planifier_post(
        self,
        *,
        user_id: uuid.UUID,
        contenu: str,
        date_planifiee: datetime | None = None,
        tags: list[Tag] | None = None,
        acteur: Acteur,
    ) -> LinkedInPost:
        profil = self.consulter_linkedin_profile(user_id)

        post = self._posts.sauvegarder(
            LinkedInPost(
                user_id=user_id,
                linkedin_profile_id=require_id(profil),
                contenu=contenu,
                statut=StatutPost.PLANIFIE,
                date_planifiee=date_planifiee,
                tags=tags or [],
            )
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="LinkedInPostPlanifié",
            entite_type="LinkedInPost",
            entite_id=require_id(post),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return post

    def consulter_post(self, post_id: uuid.UUID) -> LinkedInPost:
        post = self._posts.par_id(post_id)
        if post is None:
            raise EntityNotFoundError("LinkedInPost", post_id)
        return post

    def publier_post(self, post_id: uuid.UUID, *, acteur: Acteur) -> LinkedInPost:
        post = self.consulter_post(post_id)
        self._transitionner_post(post, StatutPost.PUBLIE)
        post.date_publication = datetime.now(UTC)

        saved = self._posts.sauvegarder(post)
        enregistrer_evenement(
            self._audit,
            type_evenement="LinkedInPostPublié",
            entite_type="LinkedInPost",
            entite_id=post_id,
            acteur=acteur,
            proprietaire_user_id=post.user_id,
        )
        return saved

    def enregistrer_metriques_post(
        self,
        post_id: uuid.UUID,
        *,
        vues: int | None = None,
        reactions: int | None = None,
        commentaires: int | None = None,
        acteur: Acteur,
    ) -> LinkedInPost:
        post = self.consulter_post(post_id)
        if post.statut is not StatutPost.PUBLIE:
            raise InvalidMetricsStateError(
                f"Impossible d'enregistrer des métriques sur un post au statut {post.statut}"
            )

        post.metriques = Metriques(
            vues=vues, reactions=reactions, commentaires=commentaires, mesurees_le=datetime.now(UTC)
        )

        saved = self._posts.sauvegarder(post)
        enregistrer_evenement(
            self._audit,
            type_evenement="MétriquesPostMisesÀJour",
            entite_type="LinkedInPost",
            entite_id=post_id,
            acteur=acteur,
            proprietaire_user_id=post.user_id,
        )
        return saved

    def ouvrir_conversation(
        self, *, user_id: uuid.UUID, contact_id: uuid.UUID, acteur: Acteur
    ) -> LinkedInConversation:
        if self._contacts.par_id(contact_id) is None:
            raise EntityNotFoundError("Contact", contact_id)

        conversation = self._conversations.sauvegarder(
            LinkedInConversation(user_id=user_id, contact_id=contact_id, statut=StatutConversation.ACTIVE)
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="LinkedInConversationOuverte",
            entite_type="LinkedInConversation",
            entite_id=require_id(conversation),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return conversation

    def consulter_conversation(self, conversation_id: uuid.UUID) -> LinkedInConversation:
        conversation = self._conversations.par_id(conversation_id)
        if conversation is None:
            raise EntityNotFoundError("LinkedInConversation", conversation_id)
        return conversation

    def consulter_conversations_par_contact(self, contact_id: uuid.UUID) -> list[LinkedInConversation]:
        return self._conversations.par_contact(contact_id)

    def enregistrer_message(
        self,
        conversation_id: uuid.UUID,
        *,
        expediteur: ExpediteurMessage,
        contenu: str,
        horodatage: datetime | None = None,
        acteur: Acteur,
    ) -> LinkedInConversation:
        conversation = self.consulter_conversation(conversation_id)
        conversation.messages.append(
            Message(expediteur=expediteur, contenu=contenu, horodatage=horodatage or datetime.now(UTC))
        )
        if expediteur is ExpediteurMessage.CONTACT and conversation.statut is StatutConversation.SANS_REPONSE:
            conversation.statut = StatutConversation.ACTIVE

        saved = self._conversations.sauvegarder(conversation)
        enregistrer_evenement(
            self._audit,
            type_evenement="MessageEnregistré",
            entite_type="LinkedInConversation",
            entite_id=conversation_id,
            acteur=acteur,
            proprietaire_user_id=conversation.user_id,
        )
        return saved

    @staticmethod
    def _transitionner_post(post: LinkedInPost, nouveau_statut: StatutPost) -> None:
        if nouveau_statut not in _POST_TRANSITIONS.get(post.statut, frozenset()):
            raise InvalidStatusTransitionError("LinkedInPost", post.statut, nouveau_statut)
        post.statut = nouveau_statut
