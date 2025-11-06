import uuid

import pytest
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService
from tests.factories import UserFactory


@pytest.fixture()
def service() -> UserService:
    return UserService()


def test_create_user_success(db: Session, service: UserService) -> None:
    long_password = secrets.token_urlsafe(32)
    print(
        f"Long password: {long_password}")
    payload = UserCreate(username="alice", email="alice@example.com", password=long_password)
    user = service.create(db, payload)

    assert isinstance(user, User)
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    # password should be stored hashed
    assert user.password and user.password != long_password
    assert security.verify_password(long_password, user.password)


def test_create_user_email_already_exists(db: Session, service: UserService) -> None:
    UserFactory(email="dup@example.com")
    payload = UserCreate(username="bob", email="dup@example.com", password=secrets.token_urlsafe(32))

    with pytest.raises(HTTPException) as exc:
        service.create(db, payload)

    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_find_by_id_returns_user_with_addresses_loaded(db: Session, service: UserService) -> None:
    user = UserFactory()
    # Storing the `user.id` is mandatory, otherwise accessing it
    # after the expunging will cause detached instance errors.
    user_id = user.id
    # Expunging the instance is necessary, otherwise the service's
    # `find_by_id` will return the same reference due to the
    # identity map mechanism.
    # Same reference, which has not the relationship loaded,
    # will raise an error when accessing the relationship.
    db.expunge(user)


    found = service.find_by_id(db, user_id)

    assert found is not None
    # relationship should be available (not raise an error)
    assert found.addresses is not None


def test_update_user_success(db: Session, service: UserService) -> None:
    user = UserFactory(email="charlie@example.com")
    update_payload = UserUpdate(username="charlie2", email="charlie2@example.com")

    updated = service.update(db, user.id, update_payload)

    assert updated is not None
    assert updated.username == update_payload.username
    assert updated.email == str(update_payload.email)


def test_update_user_email_uniqueness_enforced(db: Session, service: UserService) -> None:
    UserFactory(email="taken@example.com")
    user = UserFactory(email="free@example.com")

    with pytest.raises(HTTPException) as exc:
        service.update(db, user.id, UserUpdate(email="taken@example.com", username="ghost"))

    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_returns_none_when_user_missing(db: Session, service: UserService) -> None:
    user_data = UserFactory.build()
    update_payload = UserUpdate(email=user_data.email, username=user_data.username)
    result = service.update(db, uuid.uuid4(), payload=update_payload)

    assert result is None


def test_delete_user_success(db: Session, service: UserService) -> None:
    user = UserFactory()

    assert db.get(User, user.id) is not None
    assert service.delete(db, user.id) is True
    assert db.get(User, user.id) is None


def test_delete_user_not_found(db: Session, service: UserService) -> None:
    import uuid

    assert service.delete(db, uuid.uuid4()) is False


def test_paginate_users(db: Session, service: UserService) -> None:
    # create more than page size
    for _ in range(7):
        UserFactory()

    params = PaginationParams(page=1, per_page=5)
    result = service.paginate(db, params)

    assert result.total >= 7
    assert len(result.data) <= 5
