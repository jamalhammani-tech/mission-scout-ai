from sqlalchemy.orm import Session

from memory_agent.enums import SourceType, StatutQualification
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.schemas.common import Source, Tag
from memory_agent.schemas.company import Company
from memory_agent.schemas.mission import CompetenceRequise, Mission
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from tests.helpers import require_id


def _new_mission(user: User, company: Company, skill: Skill) -> Mission:
    return Mission(
        user_id=require_id(user),
        company_id=require_id(company),
        titre="Mission DevOps",
        source=Source(type=SourceType.LINKEDIN, reference_externe="https://linkedin.com/jobs/42"),
        competences_requises=[CompetenceRequise(skill_id=require_id(skill), obligatoire=True)],
        tags=[Tag(libelle="urgent")],
    )


def test_mission_dedup_par_reference_externe(
    session: Session, user: User, company: Company, skill: Skill
) -> None:
    repo = SqlAlchemyMissionRepository(session)
    user_id = require_id(user)
    saved = repo.sauvegarder(_new_mission(user, company, skill))

    dedup = repo.par_reference_externe(user_id, "https://linkedin.com/jobs/42")
    assert dedup is not None
    assert dedup.id == saved.id
    assert repo.par_reference_externe(user_id, "https://linkedin.com/jobs/inconnu") is None


def test_mission_par_tag(session: Session, user: User, company: Company, skill: Skill) -> None:
    repo = SqlAlchemyMissionRepository(session)
    user_id = require_id(user)
    saved = repo.sauvegarder(_new_mission(user, company, skill))

    tagged = repo.par_tag(user_id, Tag(libelle="urgent"))
    assert saved.id in [m.id for m in tagged]
    assert repo.par_tag(user_id, Tag(libelle="inconnu")) == []


def test_mission_qualification_et_recherche_par_statut(
    session: Session, user: User, company: Company, skill: Skill
) -> None:
    repo = SqlAlchemyMissionRepository(session)
    user_id = require_id(user)
    skill_id = require_id(skill)
    saved = repo.sauvegarder(_new_mission(user, company, skill))

    saved.statut_qualification = StatutQualification.QUALIFIEE
    saved.score_qualification = 0.9
    repo.sauvegarder(saved)

    qualifiees = repo.par_statut_de_qualification(user_id, StatutQualification.QUALIFIEE)
    assert saved.id in [m.id for m in qualifiees]

    fetched = repo.par_id(require_id(saved))
    assert fetched is not None
    assert fetched.competences_requises[0].skill_id == skill_id
    assert fetched.score_qualification == 0.9
