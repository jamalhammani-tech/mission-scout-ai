"""Forme brute de l'analyse IA d'une annonce — distincte des schémas memory_agent.schemas.

`import_mission.py` fait le mapping vers les schémas du domaine (Mission, CompetenceRequise, ...).
"""

from pydantic import BaseModel, Field


class AnalyseMission(BaseModel):
    titre: str = Field(description="Titre normalisé de la mission/du poste")
    entreprise: str | None = Field(default=None, description="Entreprise ou client final, si mentionné")
    lieu: str | None = Field(default=None, description="Ville ou zone géographique")
    type_contrat: str | None = Field(
        default=None, description="Type de contrat perçu : freelance, CDI, portage salarial, régie, etc."
    )
    tjm_min: float | None = Field(default=None, description="TJM minimum en euros/jour, si mentionné")
    tjm_max: float | None = Field(default=None, description="TJM maximum en euros/jour, si mentionné")
    competences_requises: list[str] = Field(
        default_factory=list, description="Compétences/technologies explicitement requises ou souhaitées"
    )
    seniorite: str | None = Field(
        default=None, description="Niveau de séniorité perçu, ex. 'Senior (8-10 ans)'"
    )
    resume: str = Field(description="Résumé de la mission en 2 à 3 phrases, en français")
