from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entity providing specific database operations.
    """

    def __init__(self) -> None:
        super().__init__(User)

    def find_by_email(self, session: Session, email: str) -> User | None:
        """Finds a user by their email address."""
        stmt = select(self.model).where(User.email == email)
        return session.execute(stmt).scalar_one_or_none()

    def find_by_username(self, session: Session, username: str) -> User | None:
        """Finds a user by their username."""
        stmt = select(self.model).where(User.username == username)
        return session.execute(stmt).scalar_one_or_none()

    def exists_by_email(self, session: Session, email: str) -> bool:
        """Checks if a user with the given email exists."""
        stmt = select(self.model.id).where(User.email == email).limit(1)
        return session.execute(stmt).scalar_one_or_none() is not None
