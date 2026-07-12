import pytest
from memory_agent.enums import ActeurType, CategorieSkill, NiveauCompetence, StatutQualification
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import Acteur, CriteresDeQualification
from memory_agent.services.profile_service import ProfileService
from memory_agent.services.skill_service import SkillService
from memory_agent.services.user_service import UserService
from sqlalchemy.orm import Session

from mission_agent.import_mission import importer_mission
from mission_agent.schemas import AnalyseMission

ACTEUR_TEST = Acteur(type=ActeurType.UTILISATEUR, identifiant="test")


class FakeAnalyseurMission:
    def __init__(self, analyse: AnalyseMission) -> None:
        self._analyse = analyse

    def analyser(self, texte_annonce: str) -> AnalyseMission:
        return self._analyse


def _analyse_bien_matchee() -> AnalyseMission:
    return AnalyseMission(
        titre="Développeur Python Freelance",
        entreprise="Acme Corp",
        lieu="Paris",
        type_contrat="freelance",
        tjm_max=600.0,
        competences_requises=["Python"],
        resume="Mission de développement backend Python.",
    )


@pytest.fixture
def profil_existant(session: Session) -> str:
    """Crée un user + profil (compétence Python, TJM min 500€) et retourne son email."""
    audit_repo = SqlAlchemyAuditEventRepository(session)
    user_service = UserService(SqlAlchemyUserRepository(session), audit_repo)
    skill_service = SkillService(SqlAlchemySkillRepository(session), audit_repo)
    profile_service = ProfileService(
        SqlAlchemyProfileRepository(session),
        SqlAlchemyUserRepository(session),
        SqlAlchemySkillRepository(session),
        audit_repo,
    )

    user = user_service.creer_user(email="jamal@example.com", nom="Jamal", acteur=ACTEUR_TEST)
    assert user.id is not None
    profile_service.creer_profil(user.id, titre="Développeur Python", acteur=ACTEUR_TEST)

    python = skill_service.referencer_ou_reutiliser(
        nom="Python", categorie=CategorieSkill.LANGAGE, acteur=ACTEUR_TEST
    )
    assert python.id is not None
    profile_service.ajouter_competence(
        user.id, skill_id=python.id, niveau=NiveauCompetence.EXPERT, acteur=ACTEUR_TEST
    )
    profile_service.definir_criteres_de_qualification(
        user.id, CriteresDeQualification(tjm_min=500.0), acteur=ACTEUR_TEST
    )

    return user.email


def test_importer_mission_texte_cree_mission_qualifiee(session: Session, profil_existant: str) -> None:
    resultat = importer_mission(
        url=None,
        texte="Annonce : recherche développeur Python freelance, TJM 600€.",
        email=profil_existant,
        analyseur=FakeAnalyseurMission(_analyse_bien_matchee()),
        session=session,
    )

    assert resultat.mission.titre == "Développeur Python Freelance"
    assert resultat.mission.statut_qualification == StatutQualification.QUALIFIEE
    assert resultat.rapport.score_pourcent == 100.0
    assert resultat.mission_deja_connue is False


def test_importer_mission_deux_fois_ne_duplique_pas(session: Session, profil_existant: str) -> None:
    texte = "Annonce : recherche développeur Python freelance, TJM 600€."
    analyseur = FakeAnalyseurMission(_analyse_bien_matchee())

    premier = importer_mission(
        url=None, texte=texte, email=profil_existant, analyseur=analyseur, session=session
    )
    second = importer_mission(
        url=None, texte=texte, email=profil_existant, analyseur=analyseur, session=session
    )

    assert premier.mission.id == second.mission.id
    assert second.mission_deja_connue is True


def test_importer_mission_email_inconnu_leve_value_error(session: Session) -> None:
    with pytest.raises(ValueError, match="import-cv"):
        importer_mission(
            url=None,
            texte="texte",
            email="inconnu@example.com",
            analyseur=FakeAnalyseurMission(_analyse_bien_matchee()),
            session=session,
        )


def test_importer_mission_ni_url_ni_texte_leve_value_error(session: Session, profil_existant: str) -> None:
    with pytest.raises(ValueError, match="--url ou --texte"):
        importer_mission(
            url=None,
            texte=None,
            email=profil_existant,
            analyseur=FakeAnalyseurMission(_analyse_bien_matchee()),
            session=session,
        )
