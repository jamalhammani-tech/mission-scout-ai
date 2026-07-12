from datetime import datetime

from sqlalchemy.orm import Session

from memory_agent.enums import NiveauCompetence
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.schemas.common import TJM
from memory_agent.schemas.profile import CompetenceProfil, Experience, Profile
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from tests.helpers import require_id


def test_profile_with_experience_and_competence(session: Session, user: User, skill: Skill) -> None:
    repo = SqlAlchemyProfileRepository(session)
    user_id = require_id(user)
    skill_id = require_id(skill)

    repo.sauvegarder(
        Profile(
            user_id=user_id,
            titre="Architecte Cloud",
            tjm=TJM(montant_min=500, montant_max=700),
            experiences=[
                Experience(intitule="Lead Dev", date_debut=datetime(2020, 1, 1), skill_ids=[skill_id])
            ],
            competences=[
                CompetenceProfil(skill_id=skill_id, niveau=NiveauCompetence.EXPERT, annees_experience=5)
            ],
        )
    )

    fetched = repo.get_profil(user_id)
    assert fetched is not None
    assert fetched.titre == "Architecte Cloud"
    assert fetched.tjm.montant_min == 500
    assert len(fetched.experiences) == 1
    assert fetched.experiences[0].skill_ids == [skill_id]
    assert fetched.competences[0].niveau == NiveauCompetence.EXPERT


def test_profile_update_replaces_children(session: Session, user: User, skill: Skill) -> None:
    repo = SqlAlchemyProfileRepository(session)
    user_id = require_id(user)
    skill_id = require_id(skill)

    saved = repo.sauvegarder(
        Profile(
            user_id=user_id,
            experiences=[
                Experience(intitule="Lead Dev", date_debut=datetime(2020, 1, 1), skill_ids=[skill_id])
            ],
        )
    )

    fetched = repo.get_profil(user_id)
    assert fetched is not None
    fetched.experiences[0].skill_ids = []
    repo.sauvegarder(fetched)

    refetched = repo.get_profil(user_id)
    assert refetched is not None
    assert refetched.id == saved.id
    assert refetched.experiences[0].skill_ids == []


def test_get_profil_absent(session: Session, user: User) -> None:
    assert SqlAlchemyProfileRepository(session).get_profil(require_id(user)) is None
