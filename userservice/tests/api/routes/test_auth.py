import pytest
from starlette.testclient import TestClient

from app.core.security import verify_password
from app.models import User
from tests.factories import UserFactory
from tests.utils import random_email, random_string


def test_login_with_existing_credentials_is_a_success(client: TestClient) -> None:
    user_password = random_string()
    user = UserFactory(email=random_email(), password=user_password)
    payload = {
        "username": user.email,
        "password": user_password,
    }

    response = client.post("auth/login/access-token", data=payload)

    assert response.status_code == 200

    body = response.json()
    assert "access_token" in body
    assert "token_type" in body
    assert body["token_type"] == "bearer"


def test_login_with_invalid_password_fails(client: TestClient) -> None:
    user_password = random_string()
    user = UserFactory(email=random_email(), password=user_password)
    payload = {
        "username": user.email,
        "password": user_password + "invalid",
    }

    response = client.post("auth/login/access-token", data=payload)
    body = response.json()

    assert response.status_code == 400
    assert "detail" in body
    assert body["detail"] == "Incorrect email or password"


def test_register_with_valid_data_is_a_success(client: TestClient) -> None:
    random_password = random_string(17)
    user_data = UserFactory.build()

    payload = {
        "email": user_data.email,
        "username": user_data.username,
        "password": random_password,
    }

    response = client.post("auth/register", json=payload)

    assert response.status_code == 201

    body = response.json()
    assert "access_token" in body
    assert "token_type" in body
    assert body["token_type"] == "bearer"


def test_register_with_existing_email_fails(client: TestClient) -> None:
    duplicate_email = random_email()
    UserFactory.create(email=duplicate_email)
    payload = {
        "username": random_string(16),
        "email": duplicate_email,
        "password": random_string(),
    }

    response = client.post("auth/register", json=payload)
    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert "Email already registered" in body["detail"]


def test_register_with_invalid_email_fails(client: TestClient) -> None:
    invalid_email = random_email().replace("@", "at")
    payload = {
        "username": random_string(30),
        "email": invalid_email,
        "password": random_string(),
    }

    response = client.post("auth/register", json=payload)
    assert response.status_code == 422

    body = response.json()
    # {'type': 'validation_error', 'title': 'Validation error', 'status': 422, 'detail': 'The given data is not valid.', 'instance': '/auth/register', 'timestamp': '2025-12-09T21:37:18.343243Z', 'errors': [{'field': 'email', 'message': 'value is not a valid email address: An email address must have an @-sign.', 'code': 'value_error'}]}
    assert "type" in body
    assert body["type"] == "validation_error"
    assert "status" in body
    assert body["status"] == 422
    assert "detail" in body
    assert "the given data is not valid" in body["detail"].lower()
    assert "errors" in body
    assert len(body["errors"]) == 1
    assert body["errors"][0]["field"] == "email"


def test_register_with_a_short_password_fails(client: TestClient) -> None:
    too_short_password = random_string(15)
    payload = {
        "username": random_string(16),
        "email": random_email(),
        "password": too_short_password,
    }

    response = client.post("auth/register", json=payload)
    assert response.status_code == 422

    body = response.json()

    assert "type" in body
    assert body["type"] == "validation_error"
    assert "errors" in body
    assert len(body["errors"]) == 1
    assert body["errors"][0]["field"] == "password"
    assert body["errors"][0]["code"] == "too_short"


@pytest.mark.parametrize(
    "current_user", [{"password": "aPasswordToChange"}], indirect=True
)
def test_change_password_is_a_success(current_user: User, auth_client: TestClient) -> None:
    current_password = "aPasswordToChange"
    new_password = random_string(16)
    payload = {
        "current_password": current_password,
        "new_password": new_password,
        "confirm_password": new_password,
    }

    response = auth_client.post("/auth/change-password", json=payload)
    assert response.status_code == 204

    assert verify_password(current_password, current_user.password) is False
    assert verify_password(new_password, current_user.password)


def test_change_password_with_invalid_current_password_fails(auth_client: TestClient) -> None:
    new_password = random_string(16)
    payload = {
        "current_password": random_string(),
        "new_password": new_password,
        "confirm_password": new_password,
    }

    response = auth_client.post("/auth/change-password", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid current password"


@pytest.mark.parametrize(
    "current_user", [{"password": "aPassword"}], indirect=True
)
def test_change_password_with_mismatched_new_passwords_fails(auth_client: TestClient) -> None:
    current_password = "aPassword"
    payload = {
        "current_password": current_password,
        "new_password": random_string(16),
        "confirm_password": random_string(16),
    }

    response = auth_client.post("/auth/change-password", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"


@pytest.mark.parametrize(
    "current_user", [{"password": "aPassword"}], indirect=True
)
def test_change_password_with_a_new_password_too_short_fails(auth_client: TestClient) -> None:
    current_password = "aPassword"
    payload = {
        "current_password": current_password,
        "new_password": random_string(15),
        "confirm_password": random_string(15),
    }

    response = auth_client.post("/auth/change-password", json=payload)
    assert response.status_code == 422
    body = response.json()
    errors = body["errors"]

    assert body["detail"] == "The given data is not valid."

    for error in errors:
        assert error["field"] in ["new_password", "confirm_password"]
        assert error["code"] == "string_too_short"


@pytest.mark.parametrize(
    "current_user", [{"password": "aC0mplexPassword!"}], indirect=True
)
def test_change_password_with_new_password_identical_to_current_fails(auth_client: TestClient) -> None:
    # Password must be at least 16 characters long,
    # otherwise we'll get a 422 error from the validation
    current_password = new_password = "aC0mplexPassword!"
    payload = {
        "current_password": current_password,
        "new_password": new_password,
        "confirm_password": new_password,
    }

    response = auth_client.post("/auth/change-password", json=payload)
    print(response.json())
    assert response.status_code == 400
    assert response.json()["detail"] == "New password cannot be the same as the current one"


def test_change_password_when_not_authenticated_fails(client: TestClient) -> None:
    a_password = random_string(16)
    new_password = random_string(16)
    UserFactory.create(password=a_password)

    payload = {
        "current_password": a_password,
        "new_password": new_password,
        "confirm_password": new_password,
    }

    response = client.post("/auth/change-password", json=payload)
    assert response.status_code == 401


def test_me_when_authenticated_is_a_success(auth_client: TestClient, current_user: User) -> None:
    response = auth_client.get("/auth/me")

    assert response.status_code == 200

    body = response.json()
    assert body["username"] == current_user.username
    assert body["email"] == current_user.email
    assert "password" not in body


def test_me_without_authentication_is_rejected(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401

    assert response.json()["detail"] == "Not authenticated"
