import uuid

from memory_agent.enums import StatutQualification
from memory_agent.exceptions import EntityNotFoundError, InvalidQualificationError
from memory_agent.repositories.interfaces import (
    AuditEventRepository,
    CompanyRepository,
    MissionRepository,
    SkillRepository,
)
from memory_agent.schemas.common import TJM, Acteur, Source, Tag
from memory_agent.schemas.mission import CompetenceRequise, Mission
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class MissionService:
    def __init__(
        self,
        mission_repo: MissionRepository,
        company_repo: CompanyRepository,
        skill_repo: SkillRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._missions = mission_repo
        self._companies = company_repo
        self._skills = skill_repo
        self._audit = audit_repo

    def enregistrer_mission_decouverte(
        self,
        *,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        titre: str,
        source: Source,
        description: str | None = None,
        tjm: TJM | None = None,
        competences_requises: list[CompetenceRequise] | None = None,
        tags: list[Tag] | None = None,
        acteur: Acteur,
    ) -> Mission:
        """Déduplique par `source.reference_externe` (docs/domain-model.md §8) : un ré-import
        d'une mission déjà connue renvoie l'existante sans créer de doublon ni d'événement."""
        if source.reference_externe:
            existing = self._missions.par_reference_externe(user_id, source.reference_externe)
            if existing is not None:
                return existing

        if self._companies.par_id(company_id) is None:
            raise EntityNotFoundError("Company", company_id)
        for competence in competences_requises or []:
            if self._skills.par_id(competence.skill_id) is None:
                raise EntityNotFoundError("Skill", competence.skill_id)

        mission = self._missions.sauvegarder(
            Mission(
                user_id=user_id,
                company_id=company_id,
                titre=titre,
                description=description,
                tjm=tjm or TJM(),
                source=source,
                competences_requises=competences_requises or [],
                tags=tags or [],
            )
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="MissionDécouverte",
            entite_type="Mission",
            entite_id=require_id(mission),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return mission

    def consulter_mission(self, mission_id: uuid.UUID) -> Mission:
        mission = self._missions.par_id(mission_id)
        if mission is None:
            raise EntityNotFoundError("Mission", mission_id)
        return mission

    def consulter_missions_qualifiees(self, user_id: uuid.UUID) -> list[Mission]:
        return self._missions.par_statut_de_qualification(user_id, StatutQualification.QUALIFIEE)

    def qualifier_mission(
        self,
        mission_id: uuid.UUID,
        *,
        statut: StatutQualification,
        score: float | None = None,
        motif: str | None = None,
        acteur: Acteur,
    ) -> Mission:
        if statut is StatutQualification.NON_QUALIFIEE:
            raise InvalidQualificationError("qualifier_mission ne peut pas cibler NON_QUALIFIEE")
        if score is not None and not (0.0 <= score <= 1.0):
            raise InvalidQualificationError(f"score_qualification doit être dans [0, 1] (reçu {score})")

        mission = self.consulter_mission(mission_id)
        mission.statut_qualification = statut
        mission.score_qualification = score
        mission.motif_qualification = motif

        saved = self._missions.sauvegarder(mission)
        enregistrer_evenement(
            self._audit,
            type_evenement="MissionQualifiée"
            if statut is StatutQualification.QUALIFIEE
            else "MissionÉcartée",
            entite_type="Mission",
            entite_id=mission_id,
            acteur=acteur,
            proprietaire_user_id=mission.user_id,
            details={"score": score, "motif": motif},
        )
        return saved
