import uuid

from memory_agent.enums import TypeDocument
from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.interfaces import AuditEventRepository, DocumentRepository, MissionRepository
from memory_agent.schemas.common import Acteur, Source, Tag
from memory_agent.schemas.document import Document
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        mission_repo: MissionRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._documents = document_repo
        self._missions = mission_repo
        self._audit = audit_repo

    def enregistrer_document(
        self,
        *,
        user_id: uuid.UUID,
        type: TypeDocument,
        reference_fichier: str,
        source: Source,
        version_label: str | None = None,
        mission_id: uuid.UUID | None = None,
        previous_version_id: uuid.UUID | None = None,
        tags: list[Tag] | None = None,
        acteur: Acteur,
    ) -> Document:
        if mission_id is not None and self._missions.par_id(mission_id) is None:
            raise EntityNotFoundError("Mission", mission_id)

        previous = None
        if previous_version_id is not None:
            previous = self._documents.par_id(previous_version_id)
            if previous is None:
                raise EntityNotFoundError("Document", previous_version_id)

        document = self._documents.sauvegarder(
            Document(
                user_id=user_id,
                mission_id=mission_id,
                previous_version_id=previous_version_id,
                type=type,
                version_label=version_label,
                reference_fichier=reference_fichier,
                source=source,
                tags=tags or [],
            )
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="NouvelleVersionDocumentAjoutée" if previous else "DocumentCréé",
            entite_type="Document",
            entite_id=require_id(document),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return document

    def consulter(self, document_id: uuid.UUID) -> Document:
        document = self._documents.par_id(document_id)
        if document is None:
            raise EntityNotFoundError("Document", document_id)
        return document

    def consulter_par_mission(self, mission_id: uuid.UUID) -> list[Document]:
        return self._documents.par_mission(mission_id)

    def consulter_par_candidature(self, candidature_id: uuid.UUID) -> list[Document]:
        return self._documents.par_candidature(candidature_id)
