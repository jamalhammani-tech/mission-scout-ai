import uuid

import pytest

from memory_agent.enums import CategorieSkill
from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.schemas.common import Acteur
from memory_agent.services.skill_service import SkillService
from tests.helpers import require_id


@pytest.fixture
def service(
    skill_repo: SqlAlchemySkillRepository, audit_repo: SqlAlchemyAuditEventRepository
) -> SkillService:
    return SkillService(skill_repo, audit_repo)


def test_referencer_ou_reutiliser_cree_si_absent(service: SkillService, acteur: Acteur) -> None:
    skill = service.referencer_ou_reutiliser(nom="React", categorie=CategorieSkill.FRAMEWORK, acteur=acteur)
    assert skill.id is not None
    assert skill.categorie == CategorieSkill.FRAMEWORK


def test_referencer_ou_reutiliser_dedupe_par_nom(service: SkillService, acteur: Acteur) -> None:
    premier = service.referencer_ou_reutiliser(nom="React", acteur=acteur)
    second = service.referencer_ou_reutiliser(nom="React", acteur=acteur)
    assert second.id == premier.id


def test_consulter_absent_leve_not_found(service: SkillService) -> None:
    with pytest.raises(EntityNotFoundError):
        service.consulter(uuid.uuid4())


def test_fusionner_absorbe_alias_et_nom_source(service: SkillService, acteur: Acteur) -> None:
    react = service.referencer_ou_reutiliser(nom="React", acteur=acteur)
    reactjs = service.referencer_ou_reutiliser(nom="ReactJS", acteur=acteur)

    fusion = service.fusionner(source_id=require_id(reactjs), cible_id=require_id(react), acteur=acteur)

    assert "ReactJS" in fusion.aliases
