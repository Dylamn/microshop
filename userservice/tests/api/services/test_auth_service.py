from sqlalchemy.orm import Session

from app.services import auth_service
from tests.factories import UserFactory
from tests.utils import random_string, random_email


def test_get_user_by_email_returns_none_for_missing_user(db: Session) -> None:
    user = auth_service.get_user_by_email(db, "non-exist@example.com")

    assert user is None


def test_get_user_by_email_returns_an_existing_user(db: Session) -> None:
    email = "test@example.com"
    UserFactory(email=email)

    found = auth_service.get_user_by_email(db, email)

    assert found is not None
    assert found.email == email


def test_authenticate_returns_none_for_non_existing_user(db: Session) -> None:
    email = random_email()
    password = random_string(16)

    user = auth_service.authenticate(db, email, password)

    assert user is None


def test_authenticate_returns_user_that_exist(db: Session) -> None:
    email = random_email()
    password = random_string(16)
    UserFactory(email=email, password=password)

    user = auth_service.authenticate(db, email, password)

    assert user is not None
    assert user.email == email