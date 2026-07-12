"""Cas d'usage complet : importer un CV -> extraire -> persister via les Services du Memory Agent."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from memory_agent.enums import ActeurType, NiveauCompetence, SourceType, TypeDocument
from memory_agent.exceptions import DuplicateEntityError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.document import SqlAlchemyDocumentRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.repositories.profile import SqlAlchemyProfileRepository
from memory_agent.repositories.skill import SqlAlchemySkillRepository
from memory_agent.repositories.user import SqlAlchemyUserRepository
from memory_agent.schemas.common import Acteur, Source
from memory_agent.schemas.document import Document
from memory_agent.schemas.profile import Profile
from memory_agent.schemas.skill import Skill
from memory_agent.schemas.user import User
from memory_agent.services.document_service import DocumentService
from memory_agent.services.profile_service import ProfileService
from memory_agent.services.skill_service import SkillService
from memory_agent.services.user_service import UserService
from sqlalchemy.orm import Session

from cv_agent.llm_extraction import LlmExtractor
from cv_agent.schemas import CvExtraction
from cv_agent.text_extraction import extraire_texte

logger = logging.getLogger(__name__)

ACTEUR_CV_AGENT = Acteur(type=ActeurType.AGENT, identifiant="cv-agent")


@dataclass
class ResultatImportCv:
    user: User
    profil: Profile
    document: Document
    extraction: CvExtraction
    profil_deja_existant: bool


def importer_cv(
    chemin: Path,
    *,
    email: str,
    nom_fallback: str | None,
    extracteur: LlmExtractor,
    session: Session,
) -> ResultatImportCv:
    texte = extraire_texte(chemin)
    logger.info("Texte extrait de %s (%d caractères)", chemin, len(texte))

    extraction = extracteur.extraire(texte)
    logger.info(
        "Extraction IA : %d expérience(s), %d compétence(s), %d technologie(s)",
        len(extraction.experiences),
        len(extraction.competences),
        len(extraction.technologies),
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
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session), SqlAlchemyMissionRepository(session), audit_repo
    )

    user = user_service.trouver_par_email(email)
    if user is None:
        user = user_service.creer_user(
            email=email, nom=nom_fallback or extraction.nom or "Utilisateur", acteur=ACTEUR_CV_AGENT
        )
    user_id = _require_id(user)

    profil_deja_existant = True
    try:
        profile_service.creer_profil(
            user_id, titre=extraction.titre, resume=extraction.resume_professionnel, acteur=ACTEUR_CV_AGENT
        )
        profil_deja_existant = False
    except DuplicateEntityError:
        # MVP : un profil existant n'est pas réécrit (titre/résumé inchangés) — seuls
        # compétences et expériences sont ajoutées. À affiner si le besoin se confirme.
        pass

    skills_par_nom = _enregistrer_competences_globales(extraction, skill_service, profile_service, user_id)
    _enregistrer_experiences(extraction, skill_service, profile_service, user_id, skills_par_nom)

    document = document_service.enregistrer_document(
        user_id=user_id,
        type=TypeDocument.CV,
        reference_fichier=str(chemin),
        source=Source(type=SourceType.SAISIE_MANUELLE),
        acteur=ACTEUR_CV_AGENT,
    )

    profil_final = profile_service.consulter_profil(user_id)
    return ResultatImportCv(
        user=user,
        profil=profil_final,
        document=document,
        extraction=extraction,
        profil_deja_existant=profil_deja_existant,
    )


def _enregistrer_competences_globales(
    extraction: CvExtraction,
    skill_service: SkillService,
    profile_service: ProfileService,
    user_id: uuid.UUID,
) -> dict[str, Skill]:
    noms = {nom.strip() for nom in extraction.competences + extraction.technologies if nom.strip()}
    skills_par_nom: dict[str, Skill] = {}
    for nom in noms:
        skill = skill_service.referencer_ou_reutiliser(nom=nom, acteur=ACTEUR_CV_AGENT)
        skills_par_nom[nom.lower()] = skill
        profile_service.ajouter_competence(
            user_id, skill_id=_require_id(skill), niveau=NiveauCompetence.CONFIRME, acteur=ACTEUR_CV_AGENT
        )
    return skills_par_nom


def _enregistrer_experiences(
    extraction: CvExtraction,
    skill_service: SkillService,
    profile_service: ProfileService,
    user_id: uuid.UUID,
    skills_par_nom: dict[str, Skill],
) -> None:
    for experience in extraction.experiences:
        skill_ids: list[uuid.UUID] = []
        for nom_brut in experience.competences:
            nom = nom_brut.strip()
            if not nom:
                continue
            skill = skills_par_nom.get(nom.lower())
            if skill is None:
                skill = skill_service.referencer_ou_reutiliser(nom=nom, acteur=ACTEUR_CV_AGENT)
                skills_par_nom[nom.lower()] = skill
            skill_ids.append(_require_id(skill))

        profile_service.ajouter_experience(
            user_id,
            intitule=experience.intitule,
            date_debut=datetime(experience.annee_debut, 1, 1),
            date_fin=datetime(experience.annee_fin, 12, 31) if experience.annee_fin else None,
            entreprise_nom=experience.entreprise,
            description=experience.description,
            skill_ids=skill_ids,
            acteur=ACTEUR_CV_AGENT,
        )


def _require_id(entite: User | Skill) -> uuid.UUID:
    assert entite.id is not None
    return entite.id
