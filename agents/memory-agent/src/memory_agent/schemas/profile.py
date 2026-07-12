import uuid
from datetime import datetime

from memory_agent.enums import NiveauCompetence
from memory_agent.schemas.common import (
    CriteresDeQualification,
    LocalisationPreference,
    PeriodeDisponibilite,
    SchemaBase,
    TJM,
)


class CompetenceProfil(SchemaBase):
    skill_id: uuid.UUID
    niveau: NiveauCompetence
    annees_experience: int | None = None


class Experience(SchemaBase):
    id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    entreprise_nom: str | None = None
    intitule: str
    date_debut: datetime
    date_fin: datetime | None = None
    description: str | None = None
    skill_ids: list[uuid.UUID] = []


class Profile(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    titre: str | None = None
    resume: str | None = None
    tjm: TJM = TJM()
    localisation_preference: LocalisationPreference = LocalisationPreference()
    disponibilite: PeriodeDisponibilite = PeriodeDisponibilite()
    criteres_qualification: CriteresDeQualification = CriteresDeQualification()
    experiences: list[Experience] = []
    competences: list[CompetenceProfil] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
