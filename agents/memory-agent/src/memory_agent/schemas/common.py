import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from memory_agent.enums import ActeurType, RemotePreference, SourceType, TypeContrat


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Tag(SchemaBase):
    libelle: str
    categorie: str | None = None


class Source(SchemaBase):
    type: SourceType
    reference_externe: str | None = None
    agent_responsable: str | None = None
    importe_le: datetime | None = None


class Acteur(SchemaBase):
    type: ActeurType
    identifiant: str


class ContactInfo(SchemaBase):
    email: str | None = None
    telephone: str | None = None
    url_linkedin: str | None = None


class TJM(SchemaBase):
    montant_min: float | None = None
    montant_max: float | None = None
    devise: str = "EUR"
    unite: str = "jour"


class PeriodeDisponibilite(SchemaBase):
    debut: datetime | None = None
    fin: datetime | None = None


class LocalisationPreference(SchemaBase):
    remote: RemotePreference | None = None
    ville_base: str | None = None
    perimetre_deplacement_km: int | None = None


class CriteresDeQualification(SchemaBase):
    tjm_min: float | None = None
    remote_requis: bool | None = None
    skills_recherches: list[uuid.UUID] = []
    skills_exclus: list[uuid.UUID] = []
    types_contrat_acceptes: list[TypeContrat] = []
    secteurs_exclus: list[str] = []


class Metriques(SchemaBase):
    vues: int | None = None
    reactions: int | None = None
    commentaires: int | None = None
    mesurees_le: datetime | None = None
