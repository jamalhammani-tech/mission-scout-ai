import uuid
from datetime import datetime

from memory_agent.enums import NiveauCompetence
from memory_agent.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidPeriodError,
    InvalidTjmRangeError,
)
from memory_agent.repositories.interfaces import (
    AuditEventRepository,
    ProfileRepository,
    SkillRepository,
    UserRepository,
)
from memory_agent.schemas.common import (
    TJM,
    Acteur,
    CriteresDeQualification,
    LocalisationPreference,
    PeriodeDisponibilite,
)
from memory_agent.schemas.profile import CompetenceProfil, Experience, Profile
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class ProfileService:
    def __init__(
        self,
        profile_repo: ProfileRepository,
        user_repo: UserRepository,
        skill_repo: SkillRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._profiles = profile_repo
        self._users = user_repo
        self._skills = skill_repo
        self._audit = audit_repo

    def consulter_profil(self, user_id: uuid.UUID) -> Profile:
        profil = self._profiles.get_profil(user_id)
        if profil is None:
            raise EntityNotFoundError("Profile", user_id)
        return profil

    def creer_profil(
        self, user_id: uuid.UUID, *, titre: str | None = None, resume: str | None = None, acteur: Acteur
    ) -> Profile:
        if self._users.par_id(user_id) is None:
            raise EntityNotFoundError("User", user_id)
        if self._profiles.get_profil(user_id) is not None:
            raise DuplicateEntityError("Profile", "user_id", user_id)

        profil = self._profiles.sauvegarder(Profile(user_id=user_id, titre=titre, resume=resume))
        enregistrer_evenement(
            self._audit,
            type_evenement="ProfilCréé",
            entite_type="Profile",
            entite_id=require_id(profil),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return profil

    def ajouter_competence(
        self,
        user_id: uuid.UUID,
        *,
        skill_id: uuid.UUID,
        niveau: NiveauCompetence,
        annees_experience: int | None = None,
        acteur: Acteur,
    ) -> Profile:
        profil = self.consulter_profil(user_id)
        if self._skills.par_id(skill_id) is None:
            raise EntityNotFoundError("Skill", skill_id)

        profil.competences = [c for c in profil.competences if c.skill_id != skill_id]
        profil.competences.append(
            CompetenceProfil(skill_id=skill_id, niveau=niveau, annees_experience=annees_experience)
        )

        saved = self._profiles.sauvegarder(profil)
        enregistrer_evenement(
            self._audit,
            type_evenement="CompétenceProfilAjoutée",
            entite_type="Profile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
            details={"skill_id": str(skill_id)},
        )
        return saved

    def retirer_competence(self, user_id: uuid.UUID, *, skill_id: uuid.UUID, acteur: Acteur) -> Profile:
        profil = self.consulter_profil(user_id)
        if not any(c.skill_id == skill_id for c in profil.competences):
            raise EntityNotFoundError("CompetenceProfil", skill_id)

        profil.competences = [c for c in profil.competences if c.skill_id != skill_id]
        saved = self._profiles.sauvegarder(profil)
        enregistrer_evenement(
            self._audit,
            type_evenement="CompétenceProfilRetirée",
            entite_type="Profile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
            details={"skill_id": str(skill_id)},
        )
        return saved

    def ajouter_experience(
        self,
        user_id: uuid.UUID,
        *,
        intitule: str,
        date_debut: datetime,
        date_fin: datetime | None = None,
        company_id: uuid.UUID | None = None,
        entreprise_nom: str | None = None,
        description: str | None = None,
        skill_ids: list[uuid.UUID] | None = None,
        acteur: Acteur,
    ) -> Profile:
        if date_fin is not None and date_fin < date_debut:
            raise InvalidPeriodError(f"date_fin ({date_fin}) doit être >= date_debut ({date_debut})")

        profil = self.consulter_profil(user_id)
        profil.experiences.append(
            Experience(
                intitule=intitule,
                date_debut=date_debut,
                date_fin=date_fin,
                company_id=company_id,
                entreprise_nom=entreprise_nom,
                description=description,
                skill_ids=skill_ids or [],
            )
        )

        saved = self._profiles.sauvegarder(profil)
        enregistrer_evenement(
            self._audit,
            type_evenement="ExpérienceAjoutée",
            entite_type="Profile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return saved

    def definir_criteres_de_qualification(
        self, user_id: uuid.UUID, criteres: CriteresDeQualification, *, acteur: Acteur
    ) -> Profile:
        profil = self.consulter_profil(user_id)
        profil.criteres_qualification = criteres
        saved = self._profiles.sauvegarder(profil)

        enregistrer_evenement(
            self._audit,
            type_evenement="CritèresDeQualificationModifiés",
            entite_type="Profile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return saved

    def definir_preferences_de_mission(
        self,
        user_id: uuid.UUID,
        *,
        tjm: TJM | None = None,
        localisation_preference: LocalisationPreference | None = None,
        disponibilite: PeriodeDisponibilite | None = None,
        acteur: Acteur,
    ) -> Profile:
        if (
            tjm is not None
            and tjm.montant_min is not None
            and tjm.montant_max is not None
            and tjm.montant_min > tjm.montant_max
        ):
            raise InvalidTjmRangeError(tjm.montant_min, tjm.montant_max)

        profil = self.consulter_profil(user_id)
        if tjm is not None:
            profil.tjm = tjm
        if localisation_preference is not None:
            profil.localisation_preference = localisation_preference
        if disponibilite is not None:
            profil.disponibilite = disponibilite

        saved = self._profiles.sauvegarder(profil)
        enregistrer_evenement(
            self._audit,
            type_evenement="PréférencesDeMissionModifiées",
            entite_type="Profile",
            entite_id=require_id(saved),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return saved
