import uuid

from memory_agent.exceptions import EntityNotFoundError
from memory_agent.repositories.interfaces import AuditEventRepository, CompanyRepository
from memory_agent.schemas.common import Acteur
from memory_agent.schemas.company import Company
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class CompanyService:
    def __init__(self, company_repo: CompanyRepository, audit_repo: AuditEventRepository) -> None:
        self._companies = company_repo
        self._audit = audit_repo

    def referencer_ou_reutiliser(
        self,
        *,
        nom: str,
        secteur: str | None = None,
        taille: str | None = None,
        site_web: str | None = None,
        ville: str | None = None,
        pays: str | None = None,
        acteur: Acteur,
    ) -> Company:
        existing = self._companies.par_nom(nom)
        if existing is not None:
            return existing

        company = self._companies.sauvegarder(
            Company(nom=nom, secteur=secteur, taille=taille, site_web=site_web, ville=ville, pays=pays)
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="CompanyCréée",
            entite_type="Company",
            entite_id=require_id(company),
            acteur=acteur,
        )
        return company

    def consulter(self, company_id: uuid.UUID) -> Company:
        company = self._companies.par_id(company_id)
        if company is None:
            raise EntityNotFoundError("Company", company_id)
        return company

    def mettre_a_jour(
        self,
        company_id: uuid.UUID,
        *,
        secteur: str | None = None,
        taille: str | None = None,
        site_web: str | None = None,
        ville: str | None = None,
        pays: str | None = None,
        acteur: Acteur,
    ) -> Company:
        company = self.consulter(company_id)
        if secteur is not None:
            company.secteur = secteur
        if taille is not None:
            company.taille = taille
        if site_web is not None:
            company.site_web = site_web
        if ville is not None:
            company.ville = ville
        if pays is not None:
            company.pays = pays

        saved = self._companies.sauvegarder(company)
        enregistrer_evenement(
            self._audit,
            type_evenement="CompanyMiseÀJour",
            entite_type="Company",
            entite_id=company_id,
            acteur=acteur,
        )
        return saved
