import factory
from starlette.testclient import TestClient

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
    assert  body["type"] == "validation_error"
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


def test_change_password_is_a_success(client: TestClient) -> None:
    assert False


def test_change_password_with_invalid_current_password_fails(client: TestClient) -> None:
    assert False


def test_change_password_with_mismatched_new_passwords_fails(client: TestClient) -> None:
    assert False


def test_change_password_with_a_new_password_too_short_fails(client: TestClient) -> None:
    assert False


def test_me_when_authenticated_is_a_success(auth_client: TestClient) -> None:
    assert False


def test_me_without_authentication_is_rejected(client: TestClient) -> None:
    assert False


def test_logout_when_authenticated_is_a_success(auth_client: TestClient) -> None:
    assert False


def test_logout_without_authentication_is_rejected(client: TestClient) -> None:
    assert False
