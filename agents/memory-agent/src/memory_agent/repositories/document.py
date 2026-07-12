import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import TaggableEntityType
from memory_agent.models.candidature import CandidatureModel
from memory_agent.models.document import DocumentModel
from memory_agent.repositories._tags import get_tags, sync_tags
from memory_agent.schemas.common import Source
from memory_agent.schemas.document import Document


class SqlAlchemyDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Document | None:
        model = self.session.get(DocumentModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[Document]:
        stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_candidature(self, candidature_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(DocumentModel)
            .join(CandidatureModel, CandidatureModel.document_id == DocumentModel.id)
            .where(CandidatureModel.id == candidature_id)
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_mission(self, mission_id: uuid.UUID) -> list[Document]:
        stmt = select(DocumentModel).where(DocumentModel.mission_id == mission_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, document: Document) -> Document:
        model = self.session.get(DocumentModel, document.id) if document.id else None
        if model is None:
            model = DocumentModel(id=document.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = document.user_id
        model.mission_id = document.mission_id
        model.previous_version_id = document.previous_version_id
        model.type = document.type
        model.version_label = document.version_label
        model.reference_fichier = document.reference_fichier

        model.source_type = document.source.type
        model.source_reference_externe = document.source.reference_externe
        model.source_agent_responsable = document.source.agent_responsable
        model.source_importe_le = document.source.importe_le

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.DOCUMENT, model.id, document.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            user_id=model.user_id,
            mission_id=model.mission_id,
            previous_version_id=model.previous_version_id,
            type=model.type,
            version_label=model.version_label,
            reference_fichier=model.reference_fichier,
            source=Source(
                type=model.source_type,
                reference_externe=model.source_reference_externe,
                agent_responsable=model.source_agent_responsable,
                importe_le=model.source_importe_le,
            ),
            tags=get_tags(self.session, TaggableEntityType.DOCUMENT, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
