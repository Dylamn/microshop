import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.address import AddressQueryParams, AddressCreate, AddressUpdate
from app.services.address_service import AddressService
from tests.factories import AddressFactory, UserFactory


@pytest.fixture(scope="function")
def service(db: Session) -> AddressService:
    return AddressService(db)


def test_paginate_addresses(service: AddressService) -> None:
    nb_users = 11
    AddressFactory.create_batch(size=nb_users)
    params = AddressQueryParams(page=1, per_page=10)

    result = service.paginate(params)

    assert result.total >= nb_users
    assert len(result.data) == params.per_page
    assert result.current_page == params.page
    assert result.last_page == nb_users // params.per_page + 1


def test_paginate_addresses_of_a_given_user(service: AddressService) -> None:
    user = UserFactory()
    nb_user_addresses = 2
    nb_other_addresses = 3
    AddressFactory.create_batch(size=nb_user_addresses, user=user)
    AddressFactory.create_batch(size=nb_other_addresses)
    params = AddressQueryParams(user_id=user.id)

    result = service.paginate(params)

    assert result.total == nb_user_addresses
    assert len(result.data) == nb_user_addresses

    for address in result.data:
        assert address.user_id == user.id


def test_paginate_addresses_with_invalid_user_id(service: AddressService) -> None:
    AddressFactory.create()
    params = AddressQueryParams(user_id=uuid.uuid4())

    result = service.paginate(params)

    assert result.total == 0
    assert len(result.data) == 0


def test_find_by_id_success(service: AddressService) -> None:
    address_to_find = AddressFactory()
    address = service.find_by_id(address_to_find.id)

    assert address is not None
    assert address.id == address_to_find.id


def test_find_by_id_returns_none_for_missing_address(service: AddressService) -> None:
    assert service.find_by_id(1) is None


def test_create_address_success(service: AddressService) -> None:
    user = UserFactory()
    fake_data = AddressFactory.build()
    payload = AddressCreate(
        street=fake_data.street,
        city=fake_data.city,
        zipcode=fake_data.zipcode,
        state=fake_data.state,
        user_id=user.id
    )

    address = service.create(payload)

    assert address is not None
    assert address.street == payload.street
    assert address.city == payload.city
    assert address.zipcode == payload.zipcode
    assert address.state == payload.state
    assert address.user_id == payload.user_id


def test_create_address_with_invalid_user_id(service: AddressService, db: Session) -> None:
    fake_data = AddressFactory.build()
    payload = AddressCreate(
        street=fake_data.street,
        city=fake_data.city,
        zipcode=fake_data.zipcode,
        state=fake_data.state,
        user_id=uuid.uuid4()
    )

    with pytest.raises(HTTPException, match=".* user does not exist.*"):
        service.create(payload)


def test_update_all_fields_of_address_success(service: AddressService) -> None:
    existing_address = AddressFactory()
    old_fields = {**existing_address.__dict__}
    user = existing_address.user
    fake_data = AddressFactory.build()

    payload = AddressUpdate(
        street=fake_data.street,
        city=fake_data.city,
        zipcode=fake_data.zipcode,
        state=fake_data.state,
    )

    print("HAAAA", old_fields, payload)

    updated_address = service.update(existing_address.id, payload, owner=user.id)

    assert updated_address is not None
    assert updated_address.street == payload.street
    assert updated_address.city == payload.city
    assert updated_address.zipcode == payload.zipcode
    assert updated_address.state == payload.state
    assert updated_address.user_id == user.id

    assert updated_address.id == old_fields["id"]
    assert updated_address.street != old_fields["street"]
    assert updated_address.city != old_fields["city"]
    assert updated_address.zipcode != old_fields["zipcode"]
    assert updated_address.state != old_fields["state"]


def test_update_partial_fields_of_address_success(service: AddressService) -> None:
    existing_address = AddressFactory()
    old_fields = {**existing_address.__dict__}
    user = existing_address.user
    partial_payload = AddressUpdate(
        street="new street",
        city="new city",
        state=existing_address.state,
        zipcode=existing_address.zipcode
    )

    updated_address = service.update(existing_address.id, partial_payload, owner=user.id)

    assert updated_address is not None
    assert updated_address.id == old_fields["id"]
    assert updated_address.street == partial_payload.street
    assert updated_address.city == partial_payload.city

    assert updated_address.state == old_fields["state"]
    assert updated_address.zipcode == old_fields["zipcode"]


def test_update_address_with_invalid_user_id(service: AddressService) -> None:
    existing_address = AddressFactory()
    fake_data = AddressFactory.build()
    payload = AddressUpdate(
        street=fake_data.street,
        city=fake_data.city,
        zipcode=fake_data.zipcode,
        state=fake_data.state,
    )

    with pytest.raises(
        HTTPException,
        match=".* not authorized .*",
        check=lambda e: e.status_code == 403
    ):
        service.update(existing_address.id, payload, owner=uuid.uuid4())


def test_update_address_not_found(service: AddressService) -> None:
    fake_data = AddressFactory.build()
    payload = AddressUpdate(
        street=fake_data.street,
        city=fake_data.city,
        zipcode=fake_data.zipcode,
        state=fake_data.state,
    )

    address = service.update(0, payload, owner=fake_data.user.id)

    assert address is None


def test_delete_address_success(service: AddressService) -> None:
    address = AddressFactory()

    service.delete(address.id, owner=address.user.id)

    assert service.find_by_id(address.id) is None


def test_delete_address_not_found(service: AddressService) -> None:
    user = UserFactory()

    # The `delete` method is a no-op when the address does not exist.
    # So it'll return `None` instead of raising an exception.
    assert service.delete(0, owner=user.id) is None


def test_delete_address_with_invalid_user_id(service: AddressService) -> None:
    address = AddressFactory()
    another_user = UserFactory()

    with pytest.raises(HTTPException, match=".* not authorized .*", check=lambda e: e.status_code == 403):
        service.delete(address.id, owner=another_user.id)
