import uuid

from memory_agent.enums import CategorieSkill
from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.interfaces import AuditEventRepository, SkillRepository
from memory_agent.schemas.common import Acteur
from memory_agent.schemas.skill import Skill
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class SkillService:
    def __init__(self, skill_repo: SkillRepository, audit_repo: AuditEventRepository) -> None:
        self._skills = skill_repo
        self._audit = audit_repo

    def referencer_ou_reutiliser(
        self,
        *,
        nom: str,
        categorie: CategorieSkill = CategorieSkill.AUTRE,
        acteur: Acteur,
    ) -> Skill:
        """Déduplique par nom/alias (docs/domain-model.md §12) avant de créer un nouveau Skill."""
        existing = self._skills.par_nom_ou_alias(nom)
        if existing is not None:
            return existing

        skill = self._skills.sauvegarder(Skill(nom=nom, categorie=categorie))
        enregistrer_evenement(
            self._audit,
            type_evenement="SkillCréé",
            entite_type="Skill",
            entite_id=require_id(skill),
            acteur=acteur,
        )
        return skill

    def consulter(self, skill_id: uuid.UUID) -> Skill:
        skill = self._skills.par_id(skill_id)
        if skill is None:
            raise EntityNotFoundError("Skill", skill_id)
        return skill

    def lister(self, categorie: CategorieSkill | None = None) -> list[Skill]:
        return self._skills.lister(categorie)

    def fusionner(self, *, source_id: uuid.UUID, cible_id: uuid.UUID, acteur: Acteur) -> Skill:
        """Absorbe les alias (et le nom) de `source` dans `cible`.

        Ne supprime pas `source` et ne repointe pas les références existantes (Profil,
        Mission) : les repositories n'exposent pas ces opérations (docs/domain-model.md §11).
        C'est une limite assumée — voir docs/adr/0004-services-metier.md.
        """
        source = self.consulter(source_id)
        cible = self.consulter(cible_id)

        nouveaux_alias = dict.fromkeys(cible.aliases)
        nouveaux_alias[source.nom] = None
        for alias in source.aliases:
            nouveaux_alias[alias] = None
        cible.aliases = list(nouveaux_alias)

        saved = self._skills.sauvegarder(cible)
        enregistrer_evenement(
            self._audit,
            type_evenement="SkillFusionné",
            entite_type="Skill",
            entite_id=cible_id,
            acteur=acteur,
            details={"source_id": str(source_id)},
        )
        return saved
