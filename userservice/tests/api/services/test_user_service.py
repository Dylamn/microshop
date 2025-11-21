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
    payload = UserCreate(username="alice", email="alice@example.com", password=long_password)
    user = service.create(db, payload)

    assert isinstance(user, User)
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    # password should be stored hashed
    assert user.password and user.password != long_password
    assert security.verify_password(long_password, user.password)


def test_create_hashes_password_and_not_plaintext(db: Session, service: UserService) -> None:
    pwd = secrets.token_urlsafe(24)
    payload = UserCreate(username="harry", email="harry@example.com", password=pwd)
    created = service.create(db, payload)

    assert created.password != pwd
    assert security.verify_password(pwd, created.password)


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
    nb_users = 7
    UserFactory.create_batch(size=nb_users)

    params = PaginationParams(page=1, per_page=5)
    result = service.paginate(db, params)
    print(result)
    assert result.total >= nb_users
    assert len(result.data) <= 5


def test_paginate_respects_page_and_per_page(db: Session, service: UserService) -> None:
    # Seed predictable number of users
    nb_users = 12
    UserFactory.create_batch(size=nb_users)

    # Page 2 with per_page 5 should return 5 items and same total
    params = PaginationParams(page=2, per_page=5)
    page2 = service.paginate(db, params)

    assert page2.total >= nb_users
    assert len(page2.data) == 5


def test_find_by_id_returns_none_for_missing_user(db: Session, service: UserService) -> None:
    missing_id = uuid.uuid4()
    assert service.find_by_id(db, missing_id) is None


def test_update_does_not_change_email_when_same_value(db: Session, service: UserService) -> None:
    user = UserFactory(email="same@example.com", username="sam")
    # attempt to set same email; should not trigger uniqueness error
    update_payload = UserUpdate(email="same@example.com", username="sam2")
    updated = service.update(db, user.id, update_payload)

    assert updated is not None
    assert updated.email == "same@example.com"
    assert updated.username == "sam2"


def test_delete_returns_false_when_user_missing(db: Session, service: UserService) -> None:
    # Ensure behavior explicitly when user does not exist
    assert service.delete(db, uuid.uuid4()) is False
