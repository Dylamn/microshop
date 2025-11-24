from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import SessionDep
from app.core.security import hash_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.pagination import PaginationParams, PaginationResponse
from app.schemas.user import UserCreate, UserResource, UserUpdate


def get_user_service(session: SessionDep) -> "UserService":
    return UserService(session)


UserServiceDep = Annotated["UserService", Depends(get_user_service)]


class UserService:
    """
    Service handling business logic for User operations.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize UserService with a database session.

        Args:
            session: SQLAlchemy database session.
        """

        self.repository = UserRepository(session)

    def paginate(
        self,
        pagination: PaginationParams
    ) -> PaginationResponse[UserResource]:
        """Paginates users."""
        users, total = self.repository.paginate(pagination)
        return pagination.to_response(users, total)

    def find_by_id(self, user_id: UUID) -> User | None:
        """Retrieves a user by ID."""
        return self.repository.find_by_id(
            user_id, options=[joinedload(User.addresses)]
        )

    def create(self, user_in: UserCreate) -> User:
        """
        Creates a new user with business logic validation.
        """
        # Business logic: check if email already exists
        if self.repository.exists_by_email(str(user_in.email)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Email already registered")

        data = user_in.model_dump(exclude_unset=True, exclude_defaults=True)
        password = hash_password(user_in.password.get_secret_value())

        user = User(**data, password=password)
        return self.repository.create(user)

    def update(self, user_id: UUID, payload: UserUpdate) -> User | None:
        """Updates a user with business logic."""
        user = self.repository.find_by_id(user_id)
        if not user:
            return None

        # Business logic: if email changes, check uniqueness
        if payload.email and payload.email != user.email:
            if self.repository.exists_by_email(str(payload.email)):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Email already taken")

        user.update(payload)
        return self.repository.update(user)

    def delete(self, user_id: UUID) -> bool:
        """Deletes a user."""
        user = self.repository.find_by_id(user_id)
        if not user:
            return False

        self.repository.delete(user)
        return True
