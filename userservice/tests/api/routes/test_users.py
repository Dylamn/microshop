import uuid
from copy import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.pagination import PaginationParams
from tests.factories import UserFactory
from tests.utils import random_string, random_email


def test_index_returns_paginated_users_with_default_pagination_parameters(
    auth_client: TestClient
) -> None:
    default_pagination_params = PaginationParams()
    nb_users = default_pagination_params.per_page * 2
    # We subtract 1 because there is always at least one user (from the `auth_client` fixture)
    UserFactory.create_batch(nb_users - 1)

    response = auth_client.get("/users")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "per_page" in data
    assert "current_page" in data
    assert "last_page" in data
    assert "from" in data
    assert "to" in data
    assert "data" in data

    assert isinstance(data["data"], list)
    assert len(data["data"]) == default_pagination_params.per_page
    assert data["current_page"] == 1
    assert data["last_page"] == 2
    assert data["from"] == 1
    assert data["to"] == default_pagination_params.per_page
    assert data["total"] == nb_users


def test_index_returns_paginated_users_with_custom_pagination_parameters(
    auth_client: TestClient
) -> None:
    nb_users = 12
    # Same reason as above, we subtract 1 to ensure predictable results, as
    # `nb_users` will correspond to the real number of users in the database.
    UserFactory.create_batch(nb_users - 1)
    pagination_params = {"page": 2, "per_page": 5}

    response = auth_client.get("/users", params=pagination_params)

    assert response.status_code == 200
    data = response.json()

    assert data["current_page"] == pagination_params["page"]
    assert data["last_page"] == nb_users // pagination_params["per_page"] + 1
    assert data["from"] == pagination_params["per_page"] * (pagination_params["page"] - 1) + 1
    assert data["to"] == pagination_params["per_page"] * pagination_params["page"]
    assert data["total"] == nb_users
    assert len(data["data"]) == pagination_params["per_page"]


def test_create_user_success(auth_client: TestClient) -> None:
    payload = {
        "username": random_string(16),
        "email": random_email(),
        "password": random_string()
    }

    response = auth_client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "password" not in data


def test_create_user_invalid_data(auth_client: TestClient) -> None:
    payload = {"username": "", "email": "invalid", "password": "short"}

    response = auth_client.post("/users", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_user_fails_due_to_existing_email(auth_client: TestClient) -> None:
    email = random_email()
    UserFactory(email=email)
    payload = {
        "username": random_string(16),
        "email": email,
        "password": random_string()
    }

    response = auth_client.post("/users", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Email already registered" in data["detail"]


def test_show_user_success(auth_client: TestClient, db: Session) -> None:
    _ = UserFactory()
    user = copy(_)
    db.expunge(_)
    response = auth_client.get(f"/users/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert "password" not in data


def test_show_user_not_found(auth_client: TestClient) -> None:
    random_id = uuid.uuid4()

    response = auth_client.get(f"/users/{random_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "User not found" in data["detail"]


def test_update_user_success(auth_client: TestClient) -> None:
    user = UserFactory()
    payload = {"username": "updateduser", "email": "updated@example.com"}

    response = auth_client.put(f"/users/{user.id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]


def test_update_user_invalid_data(auth_client: TestClient) -> None:
    user = UserFactory()
    payload = {"username": "", "email": "invalid"}

    response = auth_client.put(f"/users/{user.id}", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_update_user_not_found(auth_client: TestClient) -> None:
    random_id = uuid.uuid4()
    payload = {"username": "ghost", "email": "ghost@example.com"}

    response = auth_client.put(f"/users/{random_id}", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "User not found" in data["detail"]


def test_delete_user_success(auth_client: TestClient) -> None:
    user = UserFactory()

    response = auth_client.delete(f"/users/{user.id}")

    assert response.status_code == 204


def test_delete_user_not_found(auth_client: TestClient) -> None:
    random_id = uuid.uuid4()

    response = auth_client.delete(f"/users/{random_id}")

    # Should succeed as no-op
    assert response.status_code == 204
