import uuid

import pytest

from memory_agent.enums import ExpediteurMessage, SourceType, StatutConversation, StatutPost
from memory_agent.exceptions import (
    EntityNotFoundError,
    InvalidMetricsStateError,
    InvalidStatusTransitionError,
)
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.repositories.linkedin import (
    SqlAlchemyLinkedInConversationRepository,
    SqlAlchemyLinkedInPostRepository,
    SqlAlchemyLinkedInProfileRepository,
)
from memory_agent.schemas.common import Acteur, ContactInfo, Source
from memory_agent.schemas.contact import Contact
from memory_agent.schemas.user import User
from memory_agent.services.linkedin_service import LinkedInService
from tests.helpers import require_id


@pytest.fixture
def service(
    linkedin_profile_repo: SqlAlchemyLinkedInProfileRepository,
    linkedin_post_repo: SqlAlchemyLinkedInPostRepository,
    linkedin_conversation_repo: SqlAlchemyLinkedInConversationRepository,
    contact_repo: SqlAlchemyContactRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> LinkedInService:
    return LinkedInService(
        linkedin_profile_repo, linkedin_post_repo, linkedin_conversation_repo, contact_repo, audit_repo
    )


@pytest.fixture
def contact(contact_repo: SqlAlchemyContactRepository, user: User) -> Contact:
    return contact_repo.sauvegarder(
        Contact(
            user_id=require_id(user),
            nom="Recruteur X",
            contact_info=ContactInfo(email="r@acme.com"),
            source=Source(type=SourceType.LINKEDIN),
        )
    )


def test_planifier_post_sans_profil_leve_not_found(
    service: LinkedInService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.planifier_post(user_id=require_id(user), contenu="Retour de mission", acteur=acteur)


def test_synchroniser_puis_planifier_publier_post(
    service: LinkedInService, user: User, acteur: Acteur
) -> None:
    service.synchroniser_linkedin_profile(require_id(user), titre_affiche="Architecte Cloud", acteur=acteur)

    post = service.planifier_post(user_id=require_id(user), contenu="Retour de mission", acteur=acteur)
    assert post.statut == StatutPost.PLANIFIE

    publie = service.publier_post(require_id(post), acteur=acteur)
    assert publie.statut == StatutPost.PUBLIE
    assert publie.date_publication is not None


def test_publier_post_deja_publie_leve_transition_invalide(
    service: LinkedInService, user: User, acteur: Acteur
) -> None:
    service.synchroniser_linkedin_profile(require_id(user), acteur=acteur)
    post = service.planifier_post(user_id=require_id(user), contenu="Retour de mission", acteur=acteur)
    service.publier_post(require_id(post), acteur=acteur)

    with pytest.raises(InvalidStatusTransitionError):
        service.publier_post(require_id(post), acteur=acteur)


def test_metriques_sur_post_non_publie_leve_erreur(
    service: LinkedInService, user: User, acteur: Acteur
) -> None:
    service.synchroniser_linkedin_profile(require_id(user), acteur=acteur)
    post = service.planifier_post(user_id=require_id(user), contenu="Retour de mission", acteur=acteur)

    with pytest.raises(InvalidMetricsStateError):
        service.enregistrer_metriques_post(require_id(post), vues=100, acteur=acteur)


def test_metriques_apres_publication(service: LinkedInService, user: User, acteur: Acteur) -> None:
    service.synchroniser_linkedin_profile(require_id(user), acteur=acteur)
    post = service.planifier_post(user_id=require_id(user), contenu="Retour de mission", acteur=acteur)
    service.publier_post(require_id(post), acteur=acteur)

    avec_metriques = service.enregistrer_metriques_post(
        require_id(post), vues=100, reactions=10, commentaires=2, acteur=acteur
    )
    assert avec_metriques.metriques.vues == 100


def test_ouvrir_conversation_contact_inconnu_leve_not_found(
    service: LinkedInService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.ouvrir_conversation(user_id=require_id(user), contact_id=uuid.uuid4(), acteur=acteur)


def test_ouvrir_conversation_et_enregistrer_message(
    service: LinkedInService, user: User, contact: Contact, acteur: Acteur
) -> None:
    conversation = service.ouvrir_conversation(
        user_id=require_id(user), contact_id=require_id(contact), acteur=acteur
    )

    updated = service.enregistrer_message(
        require_id(conversation), expediteur=ExpediteurMessage.UTILISATEUR, contenu="Bonjour", acteur=acteur
    )
    assert len(updated.messages) == 1
    assert updated.id in [c.id for c in service.consulter_conversations_par_contact(require_id(contact))]


def test_message_contact_reactive_une_conversation_sans_reponse(
    service: LinkedInService,
    linkedin_conversation_repo: SqlAlchemyLinkedInConversationRepository,
    user: User,
    contact: Contact,
    acteur: Acteur,
) -> None:
    conversation = service.ouvrir_conversation(
        user_id=require_id(user), contact_id=require_id(contact), acteur=acteur
    )
    conversation.statut = StatutConversation.SANS_REPONSE
    linkedin_conversation_repo.sauvegarder(conversation)

    updated = service.enregistrer_message(
        require_id(conversation),
        expediteur=ExpediteurMessage.CONTACT,
        contenu="Toujours intéressé ?",
        acteur=acteur,
    )
    assert updated.statut == StatutConversation.ACTIVE
