import uuid

from memory_agent.enums import StatutCompte
from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError
from memory_agent.repositories.interfaces import AuditEventRepository, UserRepository
from memory_agent.schemas.common import Acteur
from memory_agent.schemas.user import User
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id


class UserService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditEventRepository) -> None:
        self._users = user_repo
        self._audit = audit_repo

    def creer_user(self, *, email: str, nom: str, acteur: Acteur) -> User:
        if self._users.par_email(email) is not None:
            raise DuplicateEntityError("User", "email", email)

        user = self._users.sauvegarder(User(email=email, nom=nom))
        user_id = require_id(user)
        enregistrer_evenement(
            self._audit,
            type_evenement="UserCréé",
            entite_type="User",
            entite_id=user_id,
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return user

    def consulter_user(self, user_id: uuid.UUID) -> User:
        user = self._users.par_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return user

    def trouver_par_email(self, email: str) -> User | None:
        """Lecture tolérante (pas d'exception) — utile pour un flux get-or-create côté appelant."""
        return self._users.par_email(email)

    def desactiver_user(self, user_id: uuid.UUID, *, acteur: Acteur) -> User:
        user = self.consulter_user(user_id)
        user.statut_compte = StatutCompte.DESACTIVE
        saved = self._users.sauvegarder(user)

        enregistrer_evenement(
            self._audit,
            type_evenement="UserDésactivé",
            entite_type="User",
            entite_id=user_id,
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return saved
