import uuid

import pytest

from memory_agent.enums import SourceType, StatutQualification
from memory_agent.exceptions import EntityNotFoundError, InvalidQualificationError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.schemas.common import Acteur, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from memory_agent.services.mission_service import MissionService
from tests.helpers import require_id


@pytest.fixture
def service(
    mission_repo: SqlAlchemyMissionRepository,
    company_repo: SqlAlchemyCompanyRepository,
    skill_repo: SqlAlchemySkillRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> MissionService:
    return MissionService(mission_repo, company_repo, skill_repo, audit_repo)


def test_enregistrer_mission_decouverte_company_inconnue_leve_not_found(
    service: MissionService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.enregistrer_mission_decouverte(
            user_id=require_id(user),
            company_id=uuid.uuid4(),
            titre="Mission DevOps",
            source=Source(type=SourceType.LINKEDIN),
            acteur=acteur,
        )


def test_enregistrer_mission_decouverte_dedup_par_reference_externe(
    service: MissionService, user: User, company: Company, acteur: Acteur
) -> None:
    source = Source(type=SourceType.LINKEDIN, reference_externe="https://linkedin.com/jobs/42")
    premiere = service.enregistrer_mission_decouverte(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Mission DevOps",
        source=source,
        acteur=acteur,
    )
    seconde = service.enregistrer_mission_decouverte(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Titre différent",
        source=source,
        acteur=acteur,
    )

    assert seconde.id == premiere.id
    assert seconde.titre == "Mission DevOps"  # pas écrasée par le ré-import


def test_qualifier_mission_statut_non_qualifiee_leve_erreur(
    service: MissionService, user: User, company: Company, acteur: Acteur
) -> None:
    mission = service.enregistrer_mission_decouverte(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Mission DevOps",
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    with pytest.raises(InvalidQualificationError):
        service.qualifier_mission(
            require_id(mission), statut=StatutQualification.NON_QUALIFIEE, acteur=acteur
        )


def test_qualifier_mission_score_hors_bornes_leve_erreur(
    service: MissionService, user: User, company: Company, acteur: Acteur
) -> None:
    mission = service.enregistrer_mission_decouverte(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Mission DevOps",
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )
    with pytest.raises(InvalidQualificationError):
        service.qualifier_mission(
            require_id(mission), statut=StatutQualification.QUALIFIEE, score=1.5, acteur=acteur
        )


def test_qualifier_mission(
    service: MissionService, user: User, company: Company, skill: Skill, acteur: Acteur
) -> None:
    mission = service.enregistrer_mission_decouverte(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Mission DevOps",
        source=Source(type=SourceType.LINKEDIN),
        acteur=acteur,
    )

    qualifiee = service.qualifier_mission(
        require_id(mission), statut=StatutQualification.QUALIFIEE, score=0.9, motif="bon match", acteur=acteur
    )

    assert qualifiee.statut_qualification == StatutQualification.QUALIFIEE
    assert qualifiee.score_qualification == 0.9
    assert qualifiee.id in [m.id for m in service.consulter_missions_qualifiees(require_id(user))]
