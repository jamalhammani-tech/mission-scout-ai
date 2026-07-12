import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.models.user import UserModel
from memory_agent.schemas.user import User


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def par_id(self, id: uuid.UUID) -> User | None:
        model = self.session.get(UserModel, id)
        return User.model_validate(model) if model else None

    def par_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        model = self.session.execute(stmt).scalar_one_or_none()
        return User.model_validate(model) if model else None

    def sauvegarder(self, user: User) -> User:
        model = self.session.get(UserModel, user.id) if user.id else None
        if model is None:
            model = UserModel(id=user.id or uuid.uuid4())
            self.session.add(model)

        model.email = user.email
        model.nom = user.nom
        model.statut_compte = user.statut_compte

        self.session.commit()
        self.session.refresh(model)
        return User.model_validate(model)
