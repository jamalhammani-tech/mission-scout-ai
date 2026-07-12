from pathlib import Path

import docx
from memory_agent.enums import TypeDocument
from sqlalchemy.orm import Session

from cv_agent.import_cv import importer_cv
from cv_agent.schemas import CvExtraction, ExperienceExtraite


def _creer_cv_docx(chemin: Path) -> None:
    document = docx.Document()
    document.add_paragraph("Jean Dupont — Développeur Backend Python")
    document.save(str(chemin))


class FakeLlmExtractor:
    def __init__(self, extraction: CvExtraction) -> None:
        self._extraction = extraction

    def extraire(self, texte_cv: str) -> CvExtraction:
        return self._extraction


def _extraction_type() -> CvExtraction:
    return CvExtraction(
        nom="Jean Dupont",
        titre="Développeur Backend Python",
        experiences=[
            ExperienceExtraite(
                intitule="Lead Developer",
                entreprise="Acme Corp",
                annee_debut=2020,
                annee_fin=2023,
                description="Développement d'API",
                competences=["Python", "PostgreSQL"],
            )
        ],
        competences=["Gestion d'équipe"],
        technologies=["Python", "PostgreSQL", "Docker"],
        certifications=["AWS Certified Solutions Architect"],
        langues=["Français (natif)", "Anglais (courant)"],
        secteurs=["Finance"],
        resume_professionnel="Développeur backend senior avec 5 ans d'expérience Python.",
    )


def test_importer_cv_cree_user_profil_competences_experiences_document(
    session: Session, tmp_path: Path
) -> None:
    chemin = tmp_path / "cv.docx"
    _creer_cv_docx(chemin)

    resultat = importer_cv(
        chemin,
        email="jean@example.com",
        nom_fallback=None,
        extracteur=FakeLlmExtractor(_extraction_type()),
        session=session,
    )

    assert resultat.user.email == "jean@example.com"
    assert resultat.user.nom == "Jean Dupont"
    assert resultat.profil_deja_existant is False

    assert resultat.profil.titre == "Développeur Backend Python"
    assert resultat.profil.resume == "Développeur backend senior avec 5 ans d'expérience Python."

    noms_competences = {c.skill_id for c in resultat.profil.competences}
    assert len(noms_competences) == 4  # Gestion d'équipe, Python, PostgreSQL, Docker

    assert len(resultat.profil.experiences) == 1
    experience = resultat.profil.experiences[0]
    assert experience.intitule == "Lead Developer"
    assert experience.entreprise_nom == "Acme Corp"
    assert experience.date_debut.year == 2020
    assert experience.date_fin is not None
    assert experience.date_fin.year == 2023
    assert len(experience.skill_ids) == 2  # Python, PostgreSQL

    assert resultat.document.type == TypeDocument.CV
    assert resultat.document.reference_fichier == str(chemin)


def test_importer_cv_deux_fois_ne_duplique_pas_les_competences(session: Session, tmp_path: Path) -> None:
    chemin = tmp_path / "cv.docx"
    _creer_cv_docx(chemin)
    extracteur = FakeLlmExtractor(_extraction_type())

    importer_cv(chemin, email="jean@example.com", nom_fallback=None, extracteur=extracteur, session=session)
    second_resultat = importer_cv(
        chemin, email="jean@example.com", nom_fallback=None, extracteur=extracteur, session=session
    )

    assert second_resultat.profil_deja_existant is True
    # ajouter_competence est un upsert par skill_id : pas de doublon après un second import
    assert len(second_resultat.profil.competences) == 4
    # ajouter_experience n'est pas idempotent (MVP) : une deuxième expérience identique est ajoutée
    assert len(second_resultat.profil.experiences) == 2
