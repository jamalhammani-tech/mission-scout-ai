import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import CategorieSkill
from memory_agent.models.skill import SkillAliasModel, SkillModel
from memory_agent.schemas.skill import Skill


class SqlAlchemySkillRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Skill | None:
        model = self.session.get(SkillModel, id)
        return self._to_schema(model) if model else None

    def par_nom_ou_alias(self, libelle: str) -> Skill | None:
        stmt = select(SkillModel).where(SkillModel.nom == libelle)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            alias_stmt = select(SkillAliasModel).where(SkillAliasModel.libelle == libelle)
            alias = self.session.execute(alias_stmt).scalar_one_or_none()
            model = alias.skill if alias else None
        return self._to_schema(model) if model else None

    def lister(self, categorie: CategorieSkill | None = None) -> list[Skill]:
        stmt = select(SkillModel)
        if categorie is not None:
            stmt = stmt.where(SkillModel.categorie == categorie)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_schema(m) for m in models]

    def sauvegarder(self, skill: Skill) -> Skill:
        model = self.session.get(SkillModel, skill.id) if skill.id else None
        if model is None:
            model = SkillModel(id=skill.id or uuid.uuid4())
            self.session.add(model)

        model.nom = skill.nom
        model.categorie = skill.categorie

        existing_aliases = {a.libelle: a for a in model.aliases}
        model.aliases = [
            existing_aliases.get(libelle, SkillAliasModel(libelle=libelle)) for libelle in set(skill.aliases)
        ]

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    @staticmethod
    def _to_schema(model: SkillModel) -> Skill:
        return Skill(
            id=model.id,
            nom=model.nom,
            categorie=model.categorie,
            aliases=[a.libelle for a in model.aliases],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
