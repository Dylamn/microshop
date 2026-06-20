from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.core import security
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdatePassword
from app.services.auth_service import AuthService


@pytest.fixture
def mock_user_repository(mocker: MockerFixture) -> MagicMock:
    return mocker.MagicMock(spec=UserRepository)


@pytest.fixture
def service(mock_db: MagicMock, mock_user_repository: MagicMock) -> AuthService:
    srv = AuthService(mock_db)
    srv.user_repository = mock_user_repository
    return srv


def test_get_user_by_email_found(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    email = "test@example.com"
    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.email = email
    mock_user_repository.find_by_email.return_value = mock_user

    # Act
    result = service.get_user_by_email(email)

    # Assert
    assert result is mock_user
    mock_user_repository.find_by_email.assert_called_once_with(email)


def test_get_user_by_email_not_found(
    service: AuthService, mock_user_repository: MagicMock
) -> None:
    # Arrange
    email = "test@example.com"
    mock_user_repository.find_by_email.return_value = None

    # Act
    result = service.get_user_by_email(email)

    # Assert
    assert result is None
    mock_user_repository.find_by_email.assert_called_once_with(email)


def test_authenticate_success(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    email = "test@example.com"
    password = "secretpassword_12345"
    hashed = security.hash_password(password)

    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.email = email
    mock_user.password = hashed
    mock_user_repository.find_by_email.return_value = mock_user

    # Act
    result = service.authenticate(email, password)

    # Assert
    assert result is mock_user
    mock_user_repository.find_by_email.assert_called_once_with(email)


def test_authenticate_user_not_found(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    email = "test@example.com"
    password = "secretpassword_12345"
    mock_user_repository.find_by_email.return_value = None
    verify_spy = mocker.spy(security, "verify_password")

    # Act
    result = service.authenticate(email, password)

    # Assert
    assert result is None
    # Timing attack prevention check: verify_password should be called with DUMMY_HASH
    verify_spy.assert_called_once_with(password, security.DUMMY_HASH)


def test_authenticate_wrong_password(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    email = "test@example.com"
    password = "secretpassword_12345"
    hashed = security.hash_password("otherpassword_12345")

    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.email = email
    mock_user.password = hashed
    mock_user_repository.find_by_email.return_value = mock_user

    # Act
    result = service.authenticate(email, password)

    # Assert
    assert result is None


def test_update_user_password_success(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    current_password = "oldpassword123_456"
    new_password = "newpassword123_456"
    hashed = security.hash_password(current_password)

    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.password = hashed

    # Stub the update method since it modifies the dict and returns self.
    def mock_update(data: dict[str, Any]) -> MagicMock:
        # We simulate updates on attributes if present
        for k, v in data.items():
            setattr(mock_user, k, v)
        return mock_user

    mock_user.update.side_effect = mock_update

    passwords = UserUpdatePassword(
        current_password=current_password,
        new_password=new_password,
        confirm_password=new_password,
    )

    # Act
    service.update_user_password(mock_user, passwords)

    # Assert
    mock_user_repository.update.assert_called_once_with(mock_user)
    assert security.verify_password(new_password, mock_user.password)


def test_update_user_password_no_password(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.password = None

    passwords = UserUpdatePassword(
        current_password="oldpassword123_456",
        new_password="newpassword123_456",
        confirm_password="newpassword123_456",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.update_user_password(mock_user, passwords)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User does not have a password"
    mock_user_repository.update.assert_not_called()


def test_update_user_password_invalid_current(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    hashed = security.hash_password("actualpassword_123")
    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.password = hashed

    passwords = UserUpdatePassword(
        current_password="wrongpassword_123",
        new_password="newpassword123_456",
        confirm_password="newpassword123_456",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.update_user_password(mock_user, passwords)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid current password"
    mock_user_repository.update.assert_not_called()


def test_update_user_password_mismatched_new(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    hashed = security.hash_password("actualpassword_123")
    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.password = hashed

    passwords = UserUpdatePassword(
        current_password="actualpassword_123",
        new_password="newpassword123_456",
        confirm_password="differentnew123_456",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.update_user_password(mock_user, passwords)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Passwords do not match"
    mock_user_repository.update.assert_not_called()


def test_update_user_password_same_as_current(
    service: AuthService, mock_user_repository: MagicMock, mocker: MockerFixture
) -> None:
    # Arrange
    hashed = security.hash_password("actualpassword_123")
    mock_user: MagicMock = mocker.MagicMock(spec=User)
    mock_user.password = hashed

    passwords = UserUpdatePassword(
        current_password="actualpassword_123",
        new_password="actualpassword_123",
        confirm_password="actualpassword_123",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.update_user_password(mock_user, passwords)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "New password cannot be the same as the current one"
    mock_user_repository.update.assert_not_called()
