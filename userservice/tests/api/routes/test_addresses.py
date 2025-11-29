from starlette.testclient import TestClient

from tests.factories import AddressFactory, UserFactory


def test_index_returns_all_addresses_with_pagination(auth_client: TestClient) -> None:
    nb_addresses = 3
    AddressFactory.create_batch(size=nb_addresses)

    response = auth_client.get("/addresses")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "per_page" in data
    assert "current_page" in data
    assert "last_page" in data

    assert data["from"] == 1

    assert len(data["data"]) == nb_addresses


def test_index_returns_addresses_of_a_given_user(auth_client: TestClient) -> None:
    user = UserFactory()
    nb_user_addresses = 2
    nb_other_addresses = 3
    AddressFactory.create_batch(size=nb_user_addresses, user=user)
    AddressFactory.create_batch(size=nb_other_addresses)
    params = {"user_id": user.id}

    response = auth_client.get("/addresses", params=params)

    assert response.status_code == 200

    data = response.json()

    assert len(data["data"]) == nb_user_addresses
    assert data["current_page"] == 1
    assert data["last_page"] == 1
    assert data["from"] == 1
    assert data["to"] == nb_user_addresses