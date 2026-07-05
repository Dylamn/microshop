from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import SessionDep
from app.core import security
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdatePassword


def get_auth_service(session: SessionDep) -> "AuthService":
    return AuthService(session)


AuthServiceDep = Annotated["AuthService", Depends(get_auth_service)]


class AuthService:
    """
    Service handling authentication business logic.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize AuthService with a database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.user_repository = UserRepository(session)

    def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieves a user from the repository based on their email.

        Args:
            email (str): The email address of the user.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        return self.user_repository.find_by_email(email)

    def authenticate(self, email: str, password: str) -> User | None:
        """Authenticates a user by verifying the provided email and password.

        This method retrieves a user from the database based on the provided email.
        If a user is found, it verifies the provided password against the stored hash.
        If the user does not exist or the password is incorrect, the method returns None.

        Args:
            email (str): The email address of the user attempting to authenticate.
            password (str): The password provided for authentication.

        Returns:
            User | None: The authenticated user object if credentials are valid, otherwise None.
        """
        db_user = self.get_user_by_email(email=email)

        target_password = db_user.password if db_user else security.DUMMY_HASH

        is_password_correct = security.verify_password(password, target_password)

        if not db_user or not is_password_correct:
            return None

        return db_user

    def update_user_password(self, user: User, passwords: UserUpdatePassword) -> None:
        """
        Updates a user's password with business logic validation.

        Args:
            user (User): The user whose password is to be updated.
            passwords (UserUpdatePassword): The schema containing old and new passwords.
        """
        if user.password is None:
            # User can have no password if they are using external authentication.
            # In a further version, a user authentication source will be introduced.
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="User does not have a password"
            )

        if not security.verify_password(passwords.current_password, user.password):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Invalid current password"
            )
        elif passwords.new_password != passwords.confirm_password:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        elif passwords.current_password == passwords.new_password:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the current one",
            )

        hash_password = security.hash_password(passwords.new_password)
        user.update({"password": hash_password})
        self.user_repository.update(user)
