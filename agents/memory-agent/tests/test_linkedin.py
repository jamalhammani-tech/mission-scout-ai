from datetime import datetime

from sqlalchemy.orm import Session

from memory_agent.enums import ExpediteurMessage, SourceType, StatutConversation, StatutPost
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.repositories.linkedin import (
    SqlAlchemyLinkedInConversationRepository,
    SqlAlchemyLinkedInPostRepository,
    SqlAlchemyLinkedInProfileRepository,
)
from memory_agent.schemas.common import ContactInfo, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.contact import Contact
from memory_agent.schemas.linkedin import LinkedInConversation, LinkedInPost, LinkedInProfile, Message
from memory_agent.schemas.user import User
from tests.helpers import require_id


def test_linkedin_profile_get_ou_absent(session: Session, user: User) -> None:
    repo = SqlAlchemyLinkedInProfileRepository(session)
    user_id = require_id(user)
    assert repo.get_profile(user_id) is None

    saved = repo.sauvegarder(LinkedInProfile(user_id=user_id, titre_affiche="Architecte Cloud freelance"))
    fetched = repo.get_profile(user_id)
    assert fetched is not None
    assert fetched.id == saved.id


def test_linkedin_post_par_statut(session: Session, user: User) -> None:
    user_id = require_id(user)
    profile = SqlAlchemyLinkedInProfileRepository(session).sauvegarder(LinkedInProfile(user_id=user_id))
    repo = SqlAlchemyLinkedInPostRepository(session)

    saved = repo.sauvegarder(
        LinkedInPost(
            user_id=user_id,
            linkedin_profile_id=require_id(profile),
            contenu="Retour sur ma dernière mission",
            statut=StatutPost.PLANIFIE,
        )
    )

    assert saved.id in [p.id for p in repo.par_statut(user_id, StatutPost.PLANIFIE)]
    assert saved.id not in [p.id for p in repo.par_statut(user_id, StatutPost.PUBLIE)]


def test_linkedin_conversation_par_contact(session: Session, user: User, company: Company) -> None:
    user_id = require_id(user)
    contact = SqlAlchemyContactRepository(session).sauvegarder(
        Contact(
            user_id=user_id,
            company_id=require_id(company),
            nom="Recruteur X",
            contact_info=ContactInfo(email="recruteur@acme.com"),
            source=Source(type=SourceType.LINKEDIN),
        )
    )
    contact_id = require_id(contact)

    repo = SqlAlchemyLinkedInConversationRepository(session)
    saved = repo.sauvegarder(
        LinkedInConversation(
            user_id=user_id,
            contact_id=contact_id,
            statut=StatutConversation.ACTIVE,
            messages=[
                Message(
                    expediteur=ExpediteurMessage.CONTACT, contenu="Bonjour", horodatage=datetime(2026, 7, 5)
                )
            ],
        )
    )

    fetched_list = repo.par_contact(contact_id)
    assert saved.id in [c.id for c in fetched_list]
    fetched = repo.par_id(require_id(saved))
    assert fetched is not None
    assert len(fetched.messages) == 1
