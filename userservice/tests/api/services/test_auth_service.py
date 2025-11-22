import pytest
from fastapi import HTTPException
from pydantic_core import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.schemas.user import UserUpdatePassword
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


def test_authenticate_returns_none_for_wrong_password(db: Session) -> None:
    email = random_email()
    wrong_password = random_string(16)
    UserFactory(email=email, password=random_string(16))

    user = auth_service.authenticate(db, email, wrong_password)

    assert user is None


def test_update_user_password_success(db: Session) -> None:
    current_password = random_string(16)
    new_password = random_string(16)
    user = UserFactory(password=current_password)

    passwords = UserUpdatePassword(
        current_password=current_password,
        new_password=new_password,
        confirm_password=new_password
    )

    auth_service.update_user_password(db, user, passwords)

    assert not security.verify_password(current_password, user.password)
    assert security.verify_password(new_password, user.password)


def test_update_user_password_fails_with_wrong_current_password(db: Session) -> None:
    user = UserFactory(password=random_string(16))
    new_password = random_string(16)

    passwords = UserUpdatePassword(
        current_password=random_string(),
        new_password=new_password,
        confirm_password=new_password
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.update_user_password(db, user, passwords)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid current password"


def test_update_user_password_fails_with_mismatched_new_passwords(db: Session) -> None:
    current_password = random_string(16)
    user = UserFactory(password=current_password)
    new_password = random_string(16)

    passwords = UserUpdatePassword(
        current_password=current_password,
        new_password=new_password,
        confirm_password=random_string(16)
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.update_user_password(db, user, passwords)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Passwords do not match"


def test_update_user_password_fails_with_new_password_same_as_current_password(db: Session) -> None:
    current_password = random_string(16)
    user = UserFactory(password=current_password)
    new_password = current_password

    passwords = UserUpdatePassword(
        current_password=current_password,
        new_password=new_password,
        confirm_password=new_password
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.update_user_password(db, user, passwords)

    assert exc.value.status_code == 400
    assert exc.value.detail == "New password cannot be the same as the current password"


def test_update_user_with_new_password_length_lower_than_password_policy(db: Session) -> None:
    user = UserFactory(password=random_string(15))
    new_password = random_string(15)

    with pytest.raises(ValidationError) as exc:
        UserUpdatePassword(
            current_password=user.password,
            new_password=new_password,
            confirm_password=new_password
        )

    assert len(exc.value.errors()) == 2
    for error in exc.value.errors():
        assert "min_length" in error["ctx"]
