import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import TypeCritereSkill
from memory_agent.models.profile import (
    ExperienceModel,
    ExperienceSkillModel,
    ProfileCompetenceModel,
    ProfileCriteriaSkillModel,
    ProfileModel,
)
from memory_agent.schemas.common import TJM, CriteresDeQualification, LocalisationPreference, PeriodeDisponibilite
from memory_agent.schemas.profile import CompetenceProfil, Experience, Profile


class SqlAlchemyProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profil(self, user_id: uuid.UUID) -> Profile | None:
        stmt = select(ProfileModel).where(ProfileModel.user_id == user_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_schema(model) if model else None

    def sauvegarder(self, profil: Profile) -> Profile:
        model = self.session.get(ProfileModel, profil.id) if profil.id else None
        if model is None:
            model = ProfileModel(id=profil.id or uuid.uuid4(), user_id=profil.user_id)
            self.session.add(model)

        model.user_id = profil.user_id
        model.titre = profil.titre
        model.resume = profil.resume

        model.tjm_min = profil.tjm.montant_min
        model.tjm_max = profil.tjm.montant_max
        model.tjm_devise = profil.tjm.devise
        model.tjm_unite = profil.tjm.unite

        model.remote_preference = profil.localisation_preference.remote
        model.ville_base = profil.localisation_preference.ville_base
        model.perimetre_deplacement_km = profil.localisation_preference.perimetre_deplacement_km

        model.disponibilite_debut = profil.disponibilite.debut
        model.disponibilite_fin = profil.disponibilite.fin

        model.criteres_tjm_min = profil.criteres_qualification.tjm_min
        model.criteres_remote_requis = profil.criteres_qualification.remote_requis
        model.criteres_types_contrat_acceptes = [t.value for t in profil.criteres_qualification.types_contrat_acceptes]
        model.criteres_secteurs_exclus = profil.criteres_qualification.secteurs_exclus

        self._sync_experiences(model, profil.experiences)
        self._sync_competences(model, profil.competences)
        self._sync_criteria_skills(model, profil.criteres_qualification)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    @staticmethod
    def _sync_experiences(model: ProfileModel, experiences: list[Experience]) -> None:
        existing_by_id = {e.id: e for e in model.experiences}
        new_list: list[ExperienceModel] = []
        for exp in experiences:
            exp_model = existing_by_id.get(exp.id) if exp.id else None
            if exp_model is None:
                exp_model = ExperienceModel(id=exp.id or uuid.uuid4())
            exp_model.company_id = exp.company_id
            exp_model.entreprise_nom = exp.entreprise_nom
            exp_model.intitule = exp.intitule
            exp_model.date_debut = exp.date_debut
            exp_model.date_fin = exp.date_fin
            exp_model.description = exp.description

            existing_skills = {s.skill_id: s for s in exp_model.skills}
            exp_model.skills = [
                existing_skills.get(skill_id, ExperienceSkillModel(skill_id=skill_id))
                for skill_id in exp.skill_ids
            ]
            new_list.append(exp_model)
        model.experiences = new_list

    @staticmethod
    def _sync_competences(model: ProfileModel, competences: list[CompetenceProfil]) -> None:
        existing_by_skill = {c.skill_id: c for c in model.competences}
        new_list: list[ProfileCompetenceModel] = []
        for comp in competences:
            comp_model = existing_by_skill.get(comp.skill_id, ProfileCompetenceModel(skill_id=comp.skill_id))
            comp_model.niveau = comp.niveau
            comp_model.annees_experience = comp.annees_experience
            new_list.append(comp_model)
        model.competences = new_list

    @staticmethod
    def _sync_criteria_skills(model: ProfileModel, criteres: CriteresDeQualification) -> None:
        existing_by_key = {(c.skill_id, c.type): c for c in model.criteria_skills}
        new_list: list[ProfileCriteriaSkillModel] = []
        for skill_id in criteres.skills_recherches:
            key = (skill_id, TypeCritereSkill.RECHERCHE)
            new_list.append(existing_by_key.get(key, ProfileCriteriaSkillModel(skill_id=skill_id, type=TypeCritereSkill.RECHERCHE)))
        for skill_id in criteres.skills_exclus:
            key = (skill_id, TypeCritereSkill.EXCLU)
            new_list.append(existing_by_key.get(key, ProfileCriteriaSkillModel(skill_id=skill_id, type=TypeCritereSkill.EXCLU)))
        model.criteria_skills = new_list

    @staticmethod
    def _to_schema(model: ProfileModel) -> Profile:
        return Profile(
            id=model.id,
            user_id=model.user_id,
            titre=model.titre,
            resume=model.resume,
            tjm=TJM(
                montant_min=model.tjm_min,
                montant_max=model.tjm_max,
                devise=model.tjm_devise,
                unite=model.tjm_unite,
            ),
            localisation_preference=LocalisationPreference(
                remote=model.remote_preference,
                ville_base=model.ville_base,
                perimetre_deplacement_km=model.perimetre_deplacement_km,
            ),
            disponibilite=PeriodeDisponibilite(debut=model.disponibilite_debut, fin=model.disponibilite_fin),
            criteres_qualification=CriteresDeQualification(
                tjm_min=model.criteres_tjm_min,
                remote_requis=model.criteres_remote_requis,
                skills_recherches=[c.skill_id for c in model.criteria_skills if c.type == TypeCritereSkill.RECHERCHE],
                skills_exclus=[c.skill_id for c in model.criteria_skills if c.type == TypeCritereSkill.EXCLU],
                types_contrat_acceptes=model.criteres_types_contrat_acceptes or [],
                secteurs_exclus=model.criteres_secteurs_exclus or [],
            ),
            experiences=[
                Experience(
                    id=e.id,
                    company_id=e.company_id,
                    entreprise_nom=e.entreprise_nom,
                    intitule=e.intitule,
                    date_debut=e.date_debut,
                    date_fin=e.date_fin,
                    description=e.description,
                    skill_ids=[s.skill_id for s in e.skills],
                )
                for e in model.experiences
            ],
            competences=[
                CompetenceProfil(skill_id=c.skill_id, niveau=c.niveau, annees_experience=c.annees_experience)
                for c in model.competences
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
