import uuid

from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError
from memory_agent.repositories.interfaces import AuditEventRepository, CompanyRepository, ContactRepository
from memory_agent.schemas.common import Acteur, ContactInfo, Source, Tag
from memory_agent.schemas.contact import Contact
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class ContactService:
    def __init__(
        self,
        contact_repo: ContactRepository,
        company_repo: CompanyRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._contacts = contact_repo
        self._companies = company_repo
        self._audit = audit_repo

    def ajouter_contact(
        self,
        *,
        user_id: uuid.UUID,
        nom: str,
        contact_info: ContactInfo,
        source: Source,
        company_id: uuid.UUID | None = None,
        tags: list[Tag] | None = None,
        acteur: Acteur,
    ) -> Contact:
        if company_id is not None and self._companies.par_id(company_id) is None:
            raise EntityNotFoundError("Company", company_id)
        if contact_info.email and self._contacts.par_email(user_id, contact_info.email) is not None:
            raise DuplicateEntityError("Contact", "email", contact_info.email)
        if source.reference_externe and self._contacts.par_reference_externe(
            user_id, source.reference_externe
        ):
            raise DuplicateEntityError("Contact", "source.reference_externe", source.reference_externe)

        contact = self._contacts.sauvegarder(
            Contact(
                user_id=user_id,
                company_id=company_id,
                nom=nom,
                contact_info=contact_info,
                source=source,
                tags=tags or [],
            )
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="ContactAjouté",
            entite_type="Contact",
            entite_id=require_id(contact),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return contact

    def consulter(self, contact_id: uuid.UUID) -> Contact:
        contact = self._contacts.par_id(contact_id)
        if contact is None:
            raise EntityNotFoundError("Contact", contact_id)
        return contact

    def consulter_plusieurs(self, contact_ids: list[uuid.UUID]) -> list[Contact]:
        """Primitive utilisée pour composer ConsulterContactsParCandidature/ParMission
        (docs/domain-model.md §12) à partir des `contact_ids` déjà portés par ces agrégats."""
        return [self.consulter(contact_id) for contact_id in contact_ids]

    def consulter_par_company(self, company_id: uuid.UUID) -> list[Contact]:
        return self._contacts.par_company(company_id)

    def mettre_a_jour_contact(
        self,
        contact_id: uuid.UUID,
        *,
        nom: str | None = None,
        contact_info: ContactInfo | None = None,
        company_id: uuid.UUID | None = None,
        acteur: Acteur,
    ) -> Contact:
        contact = self.consulter(contact_id)
        if nom is not None:
            contact.nom = nom
        if contact_info is not None:
            contact.contact_info = contact_info
        if company_id is not None:
            if self._companies.par_id(company_id) is None:
                raise EntityNotFoundError("Company", company_id)
            contact.company_id = company_id

        saved = self._contacts.sauvegarder(contact)
        enregistrer_evenement(
            self._audit,
            type_evenement="ContactMisÀJour",
            entite_type="Contact",
            entite_id=contact_id,
            acteur=acteur,
            proprietaire_user_id=contact.user_id,
        )
        return saved
