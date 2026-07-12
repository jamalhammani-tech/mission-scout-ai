import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.models.company import CompanyModel
from memory_agent.schemas.company import Company


class SqlAlchemyCompanyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Company | None:
        model = self.session.get(CompanyModel, id)
        return Company.model_validate(model) if model else None

    def par_nom(self, nom: str) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.nom == nom)
        model = self.session.execute(stmt).scalar_one_or_none()
        return Company.model_validate(model) if model else None

    def sauvegarder(self, company: Company) -> Company:
        model = self.session.get(CompanyModel, company.id) if company.id else None
        if model is None:
            model = CompanyModel(id=company.id or uuid.uuid4())
            self.session.add(model)

        model.nom = company.nom
        model.secteur = company.secteur
        model.taille = company.taille
        model.site_web = company.site_web
        model.ville = company.ville
        model.pays = company.pays

        self.session.commit()
        self.session.refresh(model)
        return Company.model_validate(model)
