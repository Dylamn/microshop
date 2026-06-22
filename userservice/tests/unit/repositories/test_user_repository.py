import pytest
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.user_repository import UserRepository
from tests.factories import UserFactory


@pytest.fixture
def repository(db: Session) -> UserRepository:
    """Fixture to provide a UserRepository instance."""
    return UserRepository(db)


def test_find_by_email_found(repository: UserRepository) -> None:
    # Arrange
    user: User = UserFactory.create(email="test@example.com")

    # Act
    found = repository.find_by_email("test@example.com")

    # Assert
    assert found is not None
    assert found.id == user.id
    assert found.email == "test@example.com"


def test_find_by_email_not_found(repository: UserRepository) -> None:
    # Act
    found = repository.find_by_email("nonexistent@example.com")

    # Assert
    assert found is None


def test_find_by_username_found(repository: UserRepository) -> None:
    # Arrange
    user: User = UserFactory.create(username="testuser")

    # Act
    found = repository.find_by_username("testuser")

    # Assert
    assert found is not None
    assert found.id == user.id
    assert found.username == "testuser"


def test_find_by_username_not_found(repository: UserRepository) -> None:
    # Act
    found = repository.find_by_username("nonexistentuser")

    # Assert
    assert found is None


def test_exists_by_email_true(repository: UserRepository) -> None:
    # Arrange
    UserFactory.create(email="exists@example.com")

    # Act
    exists = repository.exists_by_email("exists@example.com")

    # Assert
    assert exists is True


def test_exists_by_email_false(repository: UserRepository) -> None:
    # Act
    exists = repository.exists_by_email("doesnotexist@example.com")

    # Assert
    assert exists is False
