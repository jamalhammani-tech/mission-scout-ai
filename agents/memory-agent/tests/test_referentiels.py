import uuid

from sqlalchemy.orm import Session

from memory_agent.enums import CategorieSkill, StatutCompte
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.company import Company
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User


def test_user_roundtrip(session: Session) -> None:
    repo = SqlAlchemyUserRepository(session)
    saved = repo.sauvegarder(User(email="jamal@example.com", nom="Jamal"))

    assert saved.id is not None
    assert saved.statut_compte == StatutCompte.ACTIF

    fetched = repo.par_email("jamal@example.com")
    assert fetched is not None
    assert fetched.id == saved.id


def test_user_par_id_absent(session: Session) -> None:
    assert SqlAlchemyUserRepository(session).par_id(uuid.uuid4()) is None


def test_skill_dedup_par_nom_ou_alias(session: Session, skill: Skill) -> None:
    repo = SqlAlchemySkillRepository(session)

    par_nom = repo.par_nom_ou_alias("React")
    assert par_nom is not None
    assert par_nom.id == skill.id

    par_alias = repo.par_nom_ou_alias("ReactJS")
    assert par_alias is not None
    assert par_alias.id == skill.id

    assert repo.par_nom_ou_alias("inconnu") is None


def test_skill_lister_par_categorie(session: Session, skill: Skill) -> None:
    repo = SqlAlchemySkillRepository(session)
    assert skill.id in [s.id for s in repo.lister(CategorieSkill.FRAMEWORK)]
    assert skill.id not in [s.id for s in repo.lister(CategorieSkill.CLOUD)]


def test_company_roundtrip(session: Session) -> None:
    repo = SqlAlchemyCompanyRepository(session)
    saved = repo.sauvegarder(Company(nom="Acme Corp", secteur="finance"))

    fetched = repo.par_nom("Acme Corp")
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.secteur == "finance"
