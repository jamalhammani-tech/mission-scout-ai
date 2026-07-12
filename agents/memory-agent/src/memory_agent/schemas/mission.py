import uuid
from datetime import datetime

from memory_agent.enums import NiveauCompetence, StatutQualification
from memory_agent.schemas.common import SchemaBase, Source, Tag, TJM


class CompetenceRequise(SchemaBase):
    skill_id: uuid.UUID
    niveau_requis: NiveauCompetence | None = None
    obligatoire: bool = True


class Mission(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    company_id: uuid.UUID
    titre: str
    description: str | None = None
    tjm: TJM = TJM()
    statut_qualification: StatutQualification = StatutQualification.NON_QUALIFIEE
    score_qualification: float | None = None
    motif_qualification: str | None = None
    source: Source
    competences_requises: list[CompetenceRequise] = []
    contact_ids: list[uuid.UUID] = []
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
