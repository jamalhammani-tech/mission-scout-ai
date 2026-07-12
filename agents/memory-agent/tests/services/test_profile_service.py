import uuid
from datetime import datetime

import pytest

from memory_agent.enums import NiveauCompetence
from memory_agent.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidPeriodError,
    InvalidTjmRangeError,
)
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import TJM, Acteur
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from memory_agent.services.profile_service import ProfileService
from tests.helpers import require_id


@pytest.fixture
def service(
    profile_repo: SqlAlchemyProfileRepository,
    user_repo: SqlAlchemyUserRepository,
    skill_repo: SqlAlchemySkillRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> ProfileService:
    return ProfileService(profile_repo, user_repo, skill_repo, audit_repo)


def test_creer_profil_pour_user_inexistant_leve_not_found(service: ProfileService, acteur: Acteur) -> None:
    with pytest.raises(EntityNotFoundError):
        service.creer_profil(uuid.uuid4(), acteur=acteur)


def test_creer_profil_puis_doublon_leve_duplicate(
    service: ProfileService, user: User, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), titre="Architecte Cloud", acteur=acteur)
    with pytest.raises(DuplicateEntityError):
        service.creer_profil(require_id(user), acteur=acteur)


def test_consulter_profil_absent_leve_not_found(service: ProfileService, user: User) -> None:
    with pytest.raises(EntityNotFoundError):
        service.consulter_profil(require_id(user))


def test_ajouter_competence_avec_skill_inconnu_leve_not_found(
    service: ProfileService, user: User, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), acteur=acteur)
    with pytest.raises(EntityNotFoundError):
        service.ajouter_competence(
            require_id(user), skill_id=uuid.uuid4(), niveau=NiveauCompetence.EXPERT, acteur=acteur
        )


def test_ajouter_puis_retirer_competence(
    service: ProfileService, user: User, skill: Skill, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), acteur=acteur)

    profil = service.ajouter_competence(
        require_id(user), skill_id=require_id(skill), niveau=NiveauCompetence.EXPERT, acteur=acteur
    )
    assert profil.competences[0].skill_id == require_id(skill)

    profil = service.retirer_competence(require_id(user), skill_id=require_id(skill), acteur=acteur)
    assert profil.competences == []


def test_retirer_competence_absente_leve_not_found(
    service: ProfileService, user: User, skill: Skill, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), acteur=acteur)
    with pytest.raises(EntityNotFoundError):
        service.retirer_competence(require_id(user), skill_id=require_id(skill), acteur=acteur)


def test_ajouter_experience_periode_invalide_leve_erreur(
    service: ProfileService, user: User, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), acteur=acteur)
    with pytest.raises(InvalidPeriodError):
        service.ajouter_experience(
            require_id(user),
            intitule="Lead Dev",
            date_debut=datetime(2024, 1, 1),
            date_fin=datetime(2023, 1, 1),
            acteur=acteur,
        )


def test_definir_preferences_tjm_invalide_leve_erreur(
    service: ProfileService, user: User, acteur: Acteur
) -> None:
    service.creer_profil(require_id(user), acteur=acteur)
    with pytest.raises(InvalidTjmRangeError):
        service.definir_preferences_de_mission(
            require_id(user), tjm=TJM(montant_min=700, montant_max=500), acteur=acteur
        )


def test_definir_preferences_de_mission(service: ProfileService, user: User, acteur: Acteur) -> None:
    service.creer_profil(require_id(user), acteur=acteur)
    profil = service.definir_preferences_de_mission(
        require_id(user), tjm=TJM(montant_min=500, montant_max=700), acteur=acteur
    )
    assert profil.tjm.montant_min == 500
