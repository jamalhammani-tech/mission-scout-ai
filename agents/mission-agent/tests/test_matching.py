import uuid

from memory_agent.enums import TypeContrat
from memory_agent.schemas.common import CriteresDeQualification

from mission_agent.matching import Decision, calculer_matching
from mission_agent.schemas import AnalyseMission


def _analyse(*, type_contrat: str | None = None, tjm_max: float | None = None) -> AnalyseMission:
    return AnalyseMission(
        titre="Développeur Python Freelance",
        resume="Mission de développement backend.",
        type_contrat=type_contrat,
        tjm_max=tjm_max,
    )


def test_toutes_competences_et_tjm_conformes_donne_postuler() -> None:
    skill_python = uuid.uuid4()
    skill_django = uuid.uuid4()
    analyse = _analyse(tjm_max=600.0)

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[("Python", skill_python), ("Django", skill_django)],
        skill_ids_profil={skill_python, skill_django},
        criteres=CriteresDeQualification(tjm_min=500.0),
    )

    assert rapport.score_pourcent == 100.0
    assert rapport.decision is Decision.POSTULER
    assert rapport.competences_manquantes == []
    assert len(rapport.points_forts) == 3  # 2 compétences + TJM conforme


def test_aucune_competence_presente_donne_a_ignorer() -> None:
    skill_python = uuid.uuid4()
    analyse = _analyse()

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[("Python", skill_python)],
        skill_ids_profil=set(),
        criteres=CriteresDeQualification(),
    )

    assert rapport.decision is Decision.A_IGNORER
    assert rapport.competences_manquantes == ["Python"]


def test_match_partiel_donne_a_etudier() -> None:
    skill_python = uuid.uuid4()
    skill_kubernetes = uuid.uuid4()
    analyse = _analyse()

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[("Python", skill_python), ("Kubernetes", skill_kubernetes)],
        skill_ids_profil={skill_python},
        criteres=CriteresDeQualification(),
    )

    # score_competences = 0.5 -> 0.5*80 + 1.0*20 (pas de tjm_min défini) = 60
    assert rapport.score_pourcent == 60.0
    assert rapport.decision is Decision.A_ETUDIER
    assert rapport.competences_manquantes == ["Kubernetes"]


def test_tjm_inferieur_au_minimum_penalise_le_score() -> None:
    skill_python = uuid.uuid4()
    analyse = _analyse(tjm_max=400.0)

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[("Python", skill_python)],
        skill_ids_profil={skill_python},
        criteres=CriteresDeQualification(tjm_min=500.0),
    )

    # score_competences = 1.0 -> 1.0*80 + 0.0*20 = 80
    assert rapport.score_pourcent == 80.0
    assert any("TJM proposé" in ecart for ecart in rapport.ecarts)


def test_aucune_competence_requise_dans_lannonce_ne_penalise_pas() -> None:
    analyse = _analyse()

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[],
        skill_ids_profil=set(),
        criteres=CriteresDeQualification(),
    )

    assert rapport.score_pourcent == 100.0
    assert rapport.decision is Decision.POSTULER
    assert any("Aucune compétence" in ecart for ecart in rapport.ecarts)


def test_type_de_contrat_hors_criteres_est_signale_sans_impacter_le_score() -> None:
    analyse = _analyse(type_contrat="CDI")

    rapport = calculer_matching(
        analyse=analyse,
        competences_resolues=[],
        skill_ids_profil=set(),
        criteres=CriteresDeQualification(types_contrat_acceptes=[TypeContrat.FREELANCE]),
    )

    assert rapport.score_pourcent == 100.0
    assert any("Type de contrat" in ecart for ecart in rapport.ecarts)
