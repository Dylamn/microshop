import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError

from app.models import Address
from app.repositories.address_repository import AddressRepository
from app.schemas.address import (
    AddressCreate,
    AddressQueryParams,
    AddressUpdate,
)
from app.services.address_service import AddressService


@pytest.fixture
def mock_repository(mocker: MockerFixture) -> MagicMock:
    return mocker.MagicMock(spec=AddressRepository)


@pytest.fixture
def service(mock_db: MagicMock, mock_repository: MagicMock) -> AddressService:
    srv = AddressService(mock_db)
    srv.repository = mock_repository
    return srv


def test_paginate_with_user_id(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    criteria = AddressQueryParams(page=1, per_page=10, user_id=uuid.uuid4())
    mock_address = MagicMock(spec=Address)
    mock_address.id = 1
    mock_address.street = "123 Main St"
    mock_address.city = "Springfield"
    mock_address.state = "IL"
    mock_address.zipcode = "12345"
    mock_address.user_id = criteria.user_id

    mock_repository.paginate.return_value = ([mock_address], 1)

    # Act
    result = service.paginate(criteria)

    # Assert
    mock_repository.paginate.assert_called_once()
    called_query = mock_repository.paginate.call_args[0][1]
    # Check that the query has a WHERE condition matching the user_id filtering
    assert "where" in str(called_query).lower()

    assert result.total == 1
    assert len(result.data) == 1
    assert result.data[0].id == 1
    assert result.data[0].street == "123 Main St"


def test_paginate_without_user_id(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    criteria = AddressQueryParams(page=1, per_page=10, user_id=None)
    mock_address = MagicMock(spec=Address)
    mock_address.id = 1
    mock_address.street = "123 Main St"
    mock_address.city = "Springfield"
    mock_address.state = "IL"
    mock_address.zipcode = "12345"
    mock_address.user_id = uuid.uuid4()

    mock_repository.paginate.return_value = ([mock_address], 1)

    # Act
    result = service.paginate(criteria)

    # Assert
    mock_repository.paginate.assert_called_once()
    called_query = mock_repository.paginate.call_args[0][1]
    # Check that the query does NOT filter by user_id
    assert "where" not in str(called_query).lower()

    assert result.total == 1
    assert len(result.data) == 1
    assert result.data[0].id == 1
    assert result.data[0].street == "123 Main St"


def test_find_by_id_found(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    mock_address = MagicMock(spec=Address)
    mock_address.id = 42
    mock_repository.find_by_id.return_value = mock_address

    # Act
    result = service.find_by_id(42)

    # Assert
    mock_repository.find_by_id.assert_called_once_with(42)
    assert result is mock_address


def test_find_by_id_not_found(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    mock_repository.find_by_id.return_value = None

    # Act
    result = service.find_by_id(999)

    # Assert
    mock_repository.find_by_id.assert_called_once_with(999)
    assert result is None


def test_create_success(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    user_id = uuid.uuid4()
    payload = AddressCreate(
        street="456 Elm St",
        city="Chicago",
        state="IL",
        zipcode="60601",
        user_id=user_id,
    )

    # Act
    result = service.create(payload)

    # Assert
    mock_repository.create.assert_called_once()
    assert result.street == "456 Elm St"
    assert result.city == "Chicago"
    assert result.state == "IL"
    assert result.zipcode == "60601"
    assert result.user_id == user_id


def test_create_integrity_error_foreign_key(
    service: AddressService, mock_repository: MagicMock
) -> None:
    # Arrange
    payload = AddressCreate(
        street="456 Elm St",
        city="Chicago",
        state="IL",
        zipcode="60601",
        user_id=uuid.uuid4(),
    )
    orig_error = Exception("insert or update on table \"addresses\" violates foreign key constraint \"23503\"")
    integrity_error = IntegrityError("select", {}, orig_error)
    mock_repository.create.side_effect = integrity_error

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.create(payload)

    assert exc_info.value.status_code == 422
    assert "user does not exist" in exc_info.value.detail


def test_create_other_integrity_error(
    service: AddressService, mock_repository: MagicMock
) -> None:
    # Arrange
    payload = AddressCreate(
        street="456 Elm St",
        city="Chicago",
        state="IL",
        zipcode="60601",
        user_id=uuid.uuid4(),
    )
    orig_error = Exception("some other constraint check failed")
    integrity_error = IntegrityError("select", {}, orig_error)
    mock_repository.create.side_effect = integrity_error

    # Act & Assert
    with pytest.raises(IntegrityError):
        service.create(payload)


def test_update_success(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    owner_id = uuid.uuid4()
    mock_address = MagicMock(spec=Address)
    mock_address.user_id = owner_id
    mock_repository.find_by_id.return_value = mock_address
    mock_repository.update.return_value = mock_address

    payload = AddressUpdate(
        street="789 Pine St",
        city="Naperville",
        state="IL",
        zipcode="60540",
    )

    # Act
    result = service.update(address_id=10, payload=payload, owner=owner_id)

    # Assert
    mock_repository.find_by_id.assert_called_once_with(10)
    mock_address.update.assert_called_once_with(payload)
    mock_repository.update.assert_called_once_with(mock_address)
    assert result is mock_address


def test_update_not_found(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    mock_repository.find_by_id.return_value = None
    payload = AddressUpdate(
        street="789 Pine St",
        city="Naperville",
        state="IL",
        zipcode="60540",
    )

    # Act
    result = service.update(address_id=999, payload=payload, owner=uuid.uuid4())

    # Assert
    mock_repository.find_by_id.assert_called_once_with(999)
    assert result is None


def test_update_unauthorized(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    mock_address = MagicMock(spec=Address)
    mock_address.user_id = owner_id
    mock_repository.find_by_id.return_value = mock_address

    payload = AddressUpdate(
        street="789 Pine St",
        city="Naperville",
        state="IL",
        zipcode="60540",
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.update(address_id=10, payload=payload, owner=other_user_id)

    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail


def test_delete_success(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    owner_id = uuid.uuid4()
    mock_address = MagicMock(spec=Address)
    mock_address.user_id = owner_id
    mock_repository.find_by_id.return_value = mock_address

    # Act
    service.delete(address_id=10, owner=owner_id)

    # Assert
    mock_repository.find_by_id.assert_called_once_with(10)
    mock_repository.delete.assert_called_once_with(mock_address)


def test_delete_not_found(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    mock_repository.find_by_id.return_value = None

    # Act
    service.delete(address_id=999, owner=uuid.uuid4())

    # Assert
    mock_repository.find_by_id.assert_called_once_with(999)
    mock_repository.delete.assert_not_called()


def test_delete_unauthorized(service: AddressService, mock_repository: MagicMock) -> None:
    # Arrange
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    mock_address = MagicMock(spec=Address)
    mock_address.user_id = owner_id
    mock_repository.find_by_id.return_value = mock_address

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        service.delete(address_id=10, owner=other_user_id)

    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail
    mock_repository.delete.assert_not_called()
