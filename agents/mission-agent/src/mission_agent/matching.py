"""Score de matching mission/profil : fonctions pures, aucun accès réseau ni base de données.

Le score pondère à 80% la couverture des compétences requises (résolues en Skill via
memory-agent, comparaison par ID — pas de matching texte) et à 20% la compatibilité TJM.
Le type de contrat n'entre pas dans le score : c'est une information ajoutée aux écarts.
"""

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from memory_agent.enums import TypeContrat
from memory_agent.schemas.common import CriteresDeQualification

from mission_agent.schemas import AnalyseMission

SEUIL_POSTULER = 70.0
SEUIL_A_ETUDIER = 40.0

_POIDS_COMPETENCES = 0.8
_POIDS_TJM = 0.2


class Decision(StrEnum):
    POSTULER = "Postuler"
    A_ETUDIER = "À étudier"
    A_IGNORER = "À ignorer"


@dataclass
class RapportMatching:
    score_pourcent: float
    decision: Decision
    points_forts: list[str] = field(default_factory=list)
    ecarts: list[str] = field(default_factory=list)
    competences_manquantes: list[str] = field(default_factory=list)


def calculer_matching(
    *,
    analyse: AnalyseMission,
    competences_resolues: list[tuple[str, uuid.UUID]],
    skill_ids_profil: set[uuid.UUID],
    criteres: CriteresDeQualification,
) -> RapportMatching:
    points_forts: list[str] = []
    ecarts: list[str] = []

    score_competences, competences_manquantes = _evaluer_competences(
        competences_resolues, skill_ids_profil, points_forts, ecarts
    )
    score_tjm = _evaluer_tjm(analyse, criteres, points_forts, ecarts)
    _evaluer_type_contrat(analyse, criteres, ecarts)

    score = (score_competences * _POIDS_COMPETENCES + score_tjm * _POIDS_TJM) * 100
    return RapportMatching(
        score_pourcent=round(score, 1),
        decision=_decider(score),
        points_forts=points_forts,
        ecarts=ecarts,
        competences_manquantes=competences_manquantes,
    )


def _decider(score_pourcent: float) -> Decision:
    if score_pourcent >= SEUIL_POSTULER:
        return Decision.POSTULER
    if score_pourcent >= SEUIL_A_ETUDIER:
        return Decision.A_ETUDIER
    return Decision.A_IGNORER


def _evaluer_competences(
    competences_resolues: list[tuple[str, uuid.UUID]],
    skill_ids_profil: set[uuid.UUID],
    points_forts: list[str],
    ecarts: list[str],
) -> tuple[float, list[str]]:
    if not competences_resolues:
        ecarts.append("Aucune compétence explicite identifiée dans l'annonce.")
        return 1.0, []

    manquantes = [nom for nom, skill_id in competences_resolues if skill_id not in skill_ids_profil]
    presentes = [nom for nom, skill_id in competences_resolues if skill_id in skill_ids_profil]

    for nom in presentes:
        points_forts.append(f"Compétence maîtrisée : {nom}")
    if manquantes:
        ecarts.append(f"{len(manquantes)} compétence(s) manquante(s) : {', '.join(manquantes)}")

    return len(presentes) / len(competences_resolues), manquantes


def _evaluer_tjm(
    analyse: AnalyseMission,
    criteres: CriteresDeQualification,
    points_forts: list[str],
    ecarts: list[str],
) -> float:
    if criteres.tjm_min is None:
        return 1.0

    tjm_offert = analyse.tjm_max or analyse.tjm_min
    if tjm_offert is None:
        ecarts.append("TJM non précisé dans l'annonce.")
        return 0.5

    if tjm_offert >= criteres.tjm_min:
        points_forts.append(
            f"TJM proposé ({tjm_offert:.0f}€) conforme à votre minimum ({criteres.tjm_min:.0f}€)"
        )
        return 1.0

    ecarts.append(f"TJM proposé ({tjm_offert:.0f}€) inférieur à votre minimum ({criteres.tjm_min:.0f}€)")
    return 0.0


def _evaluer_type_contrat(
    analyse: AnalyseMission, criteres: CriteresDeQualification, ecarts: list[str]
) -> None:
    if not criteres.types_contrat_acceptes or not analyse.type_contrat:
        return

    detecte = _detecter_type_contrat(analyse.type_contrat)
    if detecte is not None and detecte not in criteres.types_contrat_acceptes:
        ecarts.append(f"Type de contrat détecté ({analyse.type_contrat}) hors de vos types acceptés.")


def _detecter_type_contrat(libelle: str) -> TypeContrat | None:
    normalise = libelle.strip().lower()
    if "freelance" in normalise or "indépendant" in normalise:
        return TypeContrat.FREELANCE
    if "portage" in normalise:
        return TypeContrat.PORTAGE
    if "cdi" in normalise:
        return TypeContrat.CDI
    return None
