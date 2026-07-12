import uuid
from datetime import datetime

from memory_agent.enums import StatutCandidature, StatutEntretien
from memory_agent.schemas.common import SchemaBase, Tag


class HistoriqueStatutEntry(SchemaBase):
    statut_precedent: StatutCandidature | None = None
    statut_nouveau: StatutCandidature
    horodatage: datetime
    motif: str | None = None


class Entretien(SchemaBase):
    id: uuid.UUID | None = None
    statut: StatutEntretien = StatutEntretien.PLANIFIE
    type: str | None = None
    date_prevue: datetime | None = None
    date_realisee: datetime | None = None
    preparation: str | None = None
    compte_rendu: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Candidature(SchemaBase):
    id: uuid.UUID | None = None
    user_id: uuid.UUID
    mission_id: uuid.UUID
    document_id: uuid.UUID | None = None
    statut: StatutCandidature = StatutCandidature.REPEREE
    entretiens: list[Entretien] = []
    statut_historique: list[HistoriqueStatutEntry] = []
    contact_ids: list[uuid.UUID] = []
    tags: list[Tag] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
