"""Cas d'usage complet : importer une mission -> analyser -> scorer -> persister via
les Services du Memory Agent (aucune logique de mémoire/profil dupliquée ici)."""

import hashlib
import logging
import uuid
from dataclasses import dataclass

from memory_agent.enums import ActeurType, SourceType, StatutQualification
from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.company import SqlAlchemyCompanyRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import TJM, Acteur, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.mission import CompetenceRequise, Mission
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from memory_agent.services.company_service import CompanyService
from memory_agent.services.mission_service import MissionService
from memory_agent.services.profile_service import ProfileService
from memory_agent.services.skill_service import SkillService
from memory_agent.services.user_service import UserService
from sqlalchemy.orm import Session

from mission_agent.llm_analysis import AnalyseurMission
from mission_agent.matching import Decision, RapportMatching, calculer_matching
from mission_agent.schemas import AnalyseMission
from mission_agent.text_extraction import recuperer_texte_url

logger = logging.getLogger(__name__)

ACTEUR_MISSION_AGENT = Acteur(type=ActeurType.AGENT, identifiant="mission-agent")


@dataclass
class ResultatImportMission:
    user: User
    mission: Mission
    analyse: AnalyseMission
    rapport: RapportMatching
    mission_deja_connue: bool


def importer_mission(
    *,
    url: str | None,
    texte: str | None,
    email: str,
    analyseur: AnalyseurMission,
    session: Session,
) -> ResultatImportMission:
    if bool(url) == bool(texte):
        raise ValueError("Fournis exactement un des deux : --url ou --texte.")

    texte_annonce = recuperer_texte_url(url) if url else texte
    assert texte_annonce is not None

    analyse = analyseur.analyser(texte_annonce)
    logger.info(
        "Analyse IA : titre=%r, %d compétence(s) requise(s)", analyse.titre, len(analyse.competences_requises)
    )

    audit_repo = SqlAlchemyAuditEventRepository(session)
    user_service = UserService(SqlAlchemyUserRepository(session), audit_repo)
    profile_service = ProfileService(
        SqlAlchemyProfileRepository(session),
        SqlAlchemyUserRepository(session),
        SqlAlchemySkillRepository(session),
        audit_repo,
    )
    skill_service = SkillService(SqlAlchemySkillRepository(session), audit_repo)
    company_service = CompanyService(SqlAlchemyCompanyRepository(session), audit_repo)
    mission_repo = SqlAlchemyMissionRepository(session)
    mission_service = MissionService(
        mission_repo, SqlAlchemyCompanyRepository(session), SqlAlchemySkillRepository(session), audit_repo
    )

    logger.info("Chargement du profil utilisateur (%s)", email)
    user = user_service.trouver_par_email(email)
    if user is None:
        raise ValueError(
            f"Aucun utilisateur trouvé pour {email}. Importe d'abord ton profil (`uv run import-cv ...`)."
        )
    user_id = _require_id(user)

    try:
        profil = profile_service.consulter_profil(user_id)
    except EntityNotFoundError as exc:
        raise ValueError(
            f"Aucun profil trouvé pour {email}. Importe d'abord ton CV (`uv run import-cv ...`)."
        ) from exc
    logger.info(
        "Profil chargé : %d compétence(s) enregistrée(s), tjm_min=%s",
        len(profil.competences),
        profil.criteres_qualification.tjm_min,
    )

    logger.info("Lecture des compétences du Memory Agent (%d à résoudre)", len(analyse.competences_requises))
    competences_resolues = _resoudre_competences(analyse, skill_service)
    skill_ids_profil = {c.skill_id for c in profil.competences}
    logger.info("Compétences résolues côté Memory Agent : %d", len(competences_resolues))

    logger.info("Début du scoring")
    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=competences_resolues,
        skill_ids_profil=skill_ids_profil,
        criteres=profil.criteres_qualification,
    )
    logger.info(
        "Scoring terminé : score=%.1f %%, décision=%s", rapport.score_pourcent, rapport.decision.value
    )

    logger.info("Persistance de la mission")
    company = company_service.referencer_ou_reutiliser(
        nom=analyse.entreprise or "Entreprise non précisée", ville=analyse.lieu, acteur=ACTEUR_MISSION_AGENT
    )

    reference_externe = url or f"texte:{hashlib.sha256(texte_annonce.encode('utf-8')).hexdigest()}"
    mission_deja_connue = mission_repo.par_reference_externe(user_id, reference_externe) is not None

    mission = mission_service.enregistrer_mission_decouverte(
        user_id=user_id,
        company_id=_require_id(company),
        titre=analyse.titre,
        source=Source(
            type=SourceType.SAISIE_MANUELLE,
            reference_externe=reference_externe,
            agent_responsable="mission-agent",
        ),
        description=analyse.resume,
        tjm=TJM(montant_min=analyse.tjm_min, montant_max=analyse.tjm_max),
        competences_requises=[
            CompetenceRequise(skill_id=skill_id, obligatoire=True) for _, skill_id in competences_resolues
        ],
        acteur=ACTEUR_MISSION_AGENT,
    )

    if not mission_deja_connue:
        statut = (
            StatutQualification.ECARTEE
            if rapport.decision is Decision.A_IGNORER
            else StatutQualification.QUALIFIEE
        )
        mission = mission_service.qualifier_mission(
            _require_id(mission),
            statut=statut,
            score=rapport.score_pourcent / 100,
            motif=f"Décision Career Scout Agent : {rapport.decision.value}",
            acteur=ACTEUR_MISSION_AGENT,
        )
    logger.info("Mission persistée (id=%s, déjà connue=%s)", mission.id, mission_deja_connue)

    logger.info("Génération du rapport final")
    return ResultatImportMission(
        user=user,
        mission=mission,
        analyse=analyse,
        rapport=rapport,
        mission_deja_connue=mission_deja_connue,
    )


def _resoudre_competences(
    analyse: AnalyseMission, skill_service: SkillService
) -> list[tuple[str, uuid.UUID]]:
    noms = dict.fromkeys(nom.strip() for nom in analyse.competences_requises if nom.strip())
    resolues: list[tuple[str, uuid.UUID]] = []
    for nom in noms:
        skill = skill_service.referencer_ou_reutiliser(nom=nom, acteur=ACTEUR_MISSION_AGENT)
        resolues.append((nom, _require_id(skill)))
    return resolues


def _require_id(entite: User | Mission | Company | Skill) -> uuid.UUID:
    assert entite.id is not None
    return entite.id
