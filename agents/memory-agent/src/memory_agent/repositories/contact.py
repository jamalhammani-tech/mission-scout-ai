import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import TaggableEntityType
from memory_agent.models.contact import ContactModel
from memory_agent.repositories._tags import get_tags, sync_tags
from memory_agent.schemas.common import ContactInfo, Source
from memory_agent.schemas.contact import Contact


class SqlAlchemyContactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> Contact | None:
        model = self.session.get(ContactModel, id)
        return self._to_schema(model) if model else None

    def par_proprietaire(self, user_id: uuid.UUID) -> list[Contact]:
        stmt = select(ContactModel).where(ContactModel.user_id == user_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def par_email(self, user_id: uuid.UUID, email: str) -> Contact | None:
        stmt = select(ContactModel).where(ContactModel.user_id == user_id, ContactModel.email == email)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_schema(model) if model else None

    def par_reference_externe(self, user_id: uuid.UUID, reference_externe: str) -> Contact | None:
        stmt = select(ContactModel).where(
            ContactModel.user_id == user_id, ContactModel.source_reference_externe == reference_externe
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_schema(model) if model else None

    def par_company(self, company_id: uuid.UUID) -> list[Contact]:
        stmt = select(ContactModel).where(ContactModel.company_id == company_id)
        return [self._to_schema(m) for m in self.session.execute(stmt).scalars().all()]

    def sauvegarder(self, contact: Contact) -> Contact:
        model = self.session.get(ContactModel, contact.id) if contact.id else None
        if model is None:
            model = ContactModel(id=contact.id or uuid.uuid4())
            self.session.add(model)

        model.user_id = contact.user_id
        model.company_id = contact.company_id
        model.nom = contact.nom

        model.email = contact.contact_info.email
        model.telephone = contact.contact_info.telephone
        model.url_linkedin = contact.contact_info.url_linkedin

        model.source_type = contact.source.type
        model.source_reference_externe = contact.source.reference_externe
        model.source_agent_responsable = contact.source.agent_responsable
        model.source_importe_le = contact.source.importe_le

        self.session.flush()
        sync_tags(self.session, TaggableEntityType.CONTACT, model.id, contact.tags)

        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def _to_schema(self, model: ContactModel) -> Contact:
        return Contact(
            id=model.id,
            user_id=model.user_id,
            company_id=model.company_id,
            nom=model.nom,
            contact_info=ContactInfo(
                email=model.email, telephone=model.telephone, url_linkedin=model.url_linkedin
            ),
            source=Source(
                type=model.source_type,
                reference_externe=model.source_reference_externe,
                agent_responsable=model.source_agent_responsable,
                importe_le=model.source_importe_le,
            ),
            tags=get_tags(self.session, TaggableEntityType.CONTACT, model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
