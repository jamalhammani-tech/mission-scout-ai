"""Forme brute de l'extraction IA — distincte des schémas memory_agent.schemas.

`import_cv.py` fait le mapping vers les schémas du domaine (Profile, Experience, ...).
"""

from pydantic import BaseModel, Field


class ExperienceExtraite(BaseModel):
    intitule: str
    entreprise: str | None = None
    annee_debut: int = Field(description="Année de début, meilleure estimation si imprécis dans le CV")
    annee_fin: int | None = Field(default=None, description="Année de fin, absente si poste en cours")
    description: str | None = None
    competences: list[str] = Field(default_factory=list, description="Compétences/technologies utilisées")


class CvExtraction(BaseModel):
    nom: str | None = Field(default=None, description="Nom complet de la personne")
    titre: str | None = Field(default=None, description="Titre professionnel / poste actuel")
    experiences: list[ExperienceExtraite] = Field(default_factory=list)
    competences: list[str] = Field(default_factory=list, description="Compétences (méthodes, soft skills)")
    technologies: list[str] = Field(default_factory=list, description="Langages, frameworks, outils, cloud")
    certifications: list[str] = Field(default_factory=list)
    langues: list[str] = Field(
        default_factory=list, description="Ex. 'Français (natif)', 'Anglais (courant)'"
    )
    secteurs: list[str] = Field(default_factory=list, description="Secteurs d'activité rencontrés")
    resume_professionnel: str = Field(description="Résumé professionnel de 3 à 5 phrases, en français")
