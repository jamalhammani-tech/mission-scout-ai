import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import SourceType, StatutQualification, TaggableEntityType
from memory_agent.models.mission import MissionCompetenceRequiseModel, MissionContactModel, MissionModel
from memory_agent.models.tag import EntityTagModel, TagModel
from memory_agent.repositories._tags import get_tags, sync_tags
from memory_agent.schemas.common import TJM, Source, Tag
from memory_agent.schemas.mission import CompetenceRequise, Mission


class SqlAlchemyMissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Mission | None:
        model = self.session.get(MissionModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[Mission]:
        stmt = select(MissionModel).where(MissionModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_reference_externe(self, user_id: uuid.UUID, reference_externe: str) -> Mission | None:
        stmt = select(MissionModel).where(
            MissionModel.user_id == user_id, MissionModel.source_reference_externe == reference_externe
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_schema(model) if model else None

    def par_source(self, user_id: uuid.UUID, source_type: SourceType) -> list[Mission]:
        stmt = select(MissionModel).where(MissionModel.user_id == user_id, MissionModel.source_type == source_type)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_statut_de_qualification(self, user_id: uuid.UUID, statut: StatutQualification) -> list[Mission]:
        stmt = select(MissionModel).where(
            MissionModel.user_id == user_id, MissionModel.statut_qualification == statut
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_tag(self, user_id: uuid.UUID, tag: Tag) -> list[Mission]:
        stmt = (
            select(MissionModel)
            .join(EntityTagModel, EntityTagModel.entity_id == MissionModel.id)
            .join(TagModel, TagModel.id == EntityTagModel.tag_id)
            .where(
                MissionModel.user_id == user_id,
                EntityTagModel.entity_type == TaggableEntityType.MISSION,
                TagModel.libelle == tag.libelle,
                TagModel.categorie == tag.categorie,
            )
        )
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, mission: Mission) -> Mission:
        model = self.session.get(MissionModel, mission.id) if mission.id else None
        if model is None:
            model = MissionModel(id=mission.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = mission.user_id
        model.company_id = mission.company_id
        model.titre = mission.titre
        model.description = mission.description

        model.tjm_min = mission.tjm.montant_min
        model.tjm_max = mission.tjm.montant_max
        model.tjm_devise = mission.tjm.devise
        model.tjm_unite = mission.tjm.unite

        model.statut_qualification = mission.statut_qualification
        model.score_qualification = mission.score_qualification
        model.motif_qualification = mission.motif_qualification

        model.source_type = mission.source.type
        model.source_reference_externe = mission.source.reference_externe
        model.source_agent_responsable = mission.source.agent_responsable
        model.source_importe_le = mission.source.importe_le

        existing_competences = {c.skill_id: c for c in model.competences_requises}
        model.competences_requises = [
            _merge_competence_requise(existing_competences.get(cr.skill_id), cr) for cr in mission.competences_requises
        ]

        existing_contacts = {c.contact_id for c in model.contacts}
        wanted_contacts = set(mission.contact_ids)
        model.contacts = [
            next((c for c in model.contacts if c.contact_id == contact_id), None) or MissionContactModel(contact_id=contact_id)
            for contact_id in wanted_contacts
        ]

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.MISSION, model.id, mission.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: MissionModel) -> Mission:
        return Mission(
            id=model.id,
            user_id=model.user_id,
            company_id=model.company_id,
            titre=model.titre,
            description=model.description,
            tjm=TJM(montant_min=model.tjm_min, montant_max=model.tjm_max, devise=model.tjm_devise, unite=model.tjm_unite),
            statut_qualification=model.statut_qualification,
            score_qualification=model.score_qualification,
            motif_qualification=model.motif_qualification,
            source=Source(
                type=model.source_type,
                reference_externe=model.source_reference_externe,
                agent_responsable=model.source_agent_responsable,
                importe_le=model.source_importe_le,
            ),
            competences_requises=[
                CompetenceRequise(skill_id=c.skill_id, niveau_requis=c.niveau_requis, obligatoire=c.obligatoire)
                for c in model.competences_requises
            ],
            contact_ids=[c.contact_id for c in model.contacts],
            tags=get_tags(self.session, TaggableEntityType.MISSION, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def _merge_competence_requise(
    existing: MissionCompetenceRequiseModel | None, wanted: CompetenceRequise
) -> MissionCompetenceRequiseModel:
    model = existing or MissionCompetenceRequiseModel(skill_id=wanted.skill_id)
    model.niveau_requis = wanted.niveau_requis
    model.obligatoire = wanted.obligatoire
    return model
