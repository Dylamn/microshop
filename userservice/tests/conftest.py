from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool, Engine, event, text
from sqlalchemy.orm import Session

from app import app
from app.api.deps.auth import get_current_user
from app.api.deps.db import get_db
from app.core.config import settings, Settings
from app.models import Base, User
from tests.factories import AddressFactory, UserFactory


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[Settings]:
    settings.__init__(_env_file=".env.testing")
    print(f"Switching to {settings.ENVIRONMENT} environment")

    yield settings


@pytest.fixture(scope="session")
def db_engine(override_settings: Settings) -> Generator[Engine]:
    engine = create_engine(
        override_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Enable foreign key constraints for SQLite
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))

    # To ensure it's enabled for every connection provided by the pool (crucial for SQLite)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine


@pytest.fixture(autouse=True)
def set_session_for_factories(db: Session) -> None:
    UserFactory._meta.sqlalchemy_session = db
    AddressFactory._meta.sqlalchemy_session = db


@pytest.fixture(scope="session", autouse=True)
def setup_database(db_engine: Engine) -> None:
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)


@pytest.fixture(scope="function")
def db(db_engine: Engine) -> Generator[Session]:
    """
    Create a new database session for each test and roll it back after the test.

    Args:
        db_engine: The database engine used to create the test session.

    Yields:
        Generator[Session]: A database session object.
    """
    with Session(bind=db_engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient]:
    """
    Provide a TestClient that uses the test database session.
    Override the get_db dependency to use the test session.

    Args:
        db: The test database session.

    Yields:
        A TestClient instance.
    """

    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def current_user(request: pytest.FixtureRequest) -> User:
    """
    Provide a user.

    This fixture generates and returns a user using the UserFactory, which can be used
    as the authenticated user for testing within the given function scope.
    It can be configured with ``@pytest.mark.parametrize("current_user", {...}, indirect=True)``

    Args:
        request: pytest.FixtureRequest instance representing the fixture request context.

    Returns:
        User: An instance of the User class representing the current authenticated user.
    """
    params: dict = getattr(request, "param", {})

    return UserFactory(**params)


@pytest.fixture(scope="function")
def auth_client(client: TestClient, current_user: User) -> Generator[TestClient]:
    """
    Authenticates and provides a test client for making API requests.

    This function is responsible for authenticating a test client for testing
    purposes. It yields the authenticated client to the caller and ensures
    proper teardown after testing is complete.

    Args:
        current_user: The user to be authenticated for testing.
        client: The test client instance used to interact with the API.

    Yields:
        Generator[TestClient]: An authenticated test client instance.
    """

    def override_get_current_user() -> User:
        return current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    yield client
