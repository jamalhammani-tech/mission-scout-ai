import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.models.audit import AuditEventModel
from memory_agent.schemas.audit import AuditEvent
from memory_agent.schemas.common import Acteur


class SqlAlchemyAuditEventRepository:
    """Append-only : aucune méthode de mise à jour ou de suppression n'est exposée
    (docs/domain-model.md §9 — un AuditEvent est immuable après création)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def enregistrer(self, event: AuditEvent) -> AuditEvent:
        model = AuditEventModel(
            id=event.id or uuid.uuid4(),
            type_evenement=event.type_evenement,
            entite_type=event.entite_type,
            entite_id=event.entite_id,
            acteur_type=event.acteur.type,
            acteur_identifiant=event.acteur.identifiant,
            proprietaire_user_id=event.proprietaire_user_id,
            details=event.details,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def par_entite(self, entite_type: str, entite_id: uuid.UUID) -> list[AuditEvent]:
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.entite_type == entite_type, AuditEventModel.entite_id == entite_id)
            .order_by(AuditEventModel.horodatage)
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_proprietaire(
        self, user_id: uuid.UUID, depuis: datetime | None = None, jusqua: datetime | None = None
    ) -> list[AuditEvent]:
        stmt = select(AuditEventModel).where(AuditEventModel.proprietaire_user_id == user_id)
        if depuis is not None:
            stmt = stmt.where(AuditEventModel.horodatage >= depuis)
        if jusqua is not None:
            stmt = stmt.where(AuditEventModel.horodatage <= jusqua)
        stmt = stmt.order_by(AuditEventModel.horodatage)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_acteur(self, acteur: Acteur) -> list[AuditEvent]:
        stmt = (
            select(AuditEventModel)
            .where(
                AuditEventModel.acteur_type == acteur.type,
                AuditEventModel.acteur_identifiant == acteur.identifiant,
            )
            .order_by(AuditEventModel.horodatage)
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    @staticmethod
    def _to_schema(model: AuditEventModel) -> AuditEvent:
        return AuditEvent(
            id=model.id,
            horodatage=model.horodatage,
            type_evenement=model.type_evenement,
            entite_type=model.entite_type,
            entite_id=model.entite_id,
            acteur=Acteur(type=model.acteur_type, identifiant=model.acteur_identifiant),
            proprietaire_user_id=model.proprietaire_user_id,
            details=model.details,
        )
