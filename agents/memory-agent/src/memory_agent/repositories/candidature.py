import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import StatutCandidature, TaggableEntityType
from memory_agent.models.candidature import (
    CandidatureContactModel,
    CandidatureModel,
    CandidatureStatutHistoriqueModel,
    EntretienModel,
)
from memory_agent.repositories._tags import get_tags, sync_tags
from memory_agent.schemas.candidature import Candidature, Entretien, HistoriqueStatutEntry

CANDIDATURE_STATUTS_CLOTURES = {
    StatutCandidature.ACCEPTEE,
    StatutCandidature.REFUSEE,
    StatutCandidature.ABANDONNEE,
}


class SqlAlchemyCandidatureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Candidature | None:
        model = self.session.get(CandidatureModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[Candidature]:
        stmt = select(CandidatureModel).where(CandidatureModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_mission(self, mission_id: uuid.UUID) -> Candidature | None:
        stmt = select(CandidatureModel).where(CandidatureModel.mission_id == mission_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_schema(model) if model else None

    def par_statut(self, user_id: uuid.UUID, statut: StatutCandidature) -> list[Candidature]:
        stmt = select(CandidatureModel).where(
            CandidatureModel.user_id == user_id, CandidatureModel.statut == statut
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def lister_actives(self, user_id: uuid.UUID) -> list[Candidature]:
        stmt = select(CandidatureModel).where(
            CandidatureModel.user_id == user_id,
            CandidatureModel.statut.notin_(CANDIDATURE_STATUTS_CLOTURES),
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, candidature: Candidature) -> Candidature:
        model = self.session.get(CandidatureModel, candidature.id) if candidature.id else None
        if model is None:
            model = CandidatureModel(id=candidature.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = candidature.user_id
        model.mission_id = candidature.mission_id
        model.document_id = candidature.document_id
        model.statut = candidature.statut

        existing_entretiens = {e.id: e for e in model.entretiens}
        new_entretiens = []
        for entretien in candidature.entretiens:
            e_model = existing_entretiens.get(entretien.id) if entretien.id else None
            if e_model is None:
                e_model = EntretienModel(id=entretien.id or uuid.uuid4())
            e_model.statut = entretien.statut
            e_model.type = entretien.type
            e_model.date_prevue = entretien.date_prevue
            e_model.date_realisee = entretien.date_realisee
            e_model.preparation = entretien.preparation
            e_model.compte_rendu = entretien.compte_rendu
            new_entretiens.append(e_model)
        model.entretiens = new_entretiens

        model.statut_historique = [
            CandidatureStatutHistoriqueModel(
                statut_precedent=entry.statut_precedent,
                statut_nouveau=entry.statut_nouveau,
                horodatage=entry.horodatage,
                motif=entry.motif,
            )
            for entry in candidature.statut_historique
        ]

        existing_contacts = {c.contact_id: c for c in model.contacts}
        model.contacts = [
            existing_contacts.get(contact_id, CandidatureContactModel(contact_id=contact_id))
            for contact_id in candidature.contact_ids
        ]

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.CANDIDATURE, model.id, candidature.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: CandidatureModel) -> Candidature:
        return Candidature(
            id=model.id,
            user_id=model.user_id,
            mission_id=model.mission_id,
            document_id=model.document_id,
            statut=model.statut,
            entretiens=[
                Entretien(
                    id=e.id,
                    statut=e.statut,
                    type=e.type,
                    date_prevue=e.date_prevue,
                    date_realisee=e.date_realisee,
                    preparation=e.preparation,
                    compte_rendu=e.compte_rendu,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                )
                for e in model.entretiens
            ],
            statut_historique=[
                HistoriqueStatutEntry(
                    statut_precedent=h.statut_precedent,
                    statut_nouveau=h.statut_nouveau,
                    horodatage=h.horodatage,
                    motif=h.motif,
                )
                for h in model.statut_historique
            ],
            contact_ids=[c.contact_id for c in model.contacts],
            tags=get_tags(self.session, TaggableEntityType.CANDIDATURE, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
