from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool, Engine
from sqlalchemy.orm import Session

from app import app
from app.api.deps.db import get_db
from app.core.config import settings, Settings
from app.models import Base
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
    """
    with Session(bind=db_engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient]:
    """
    Provide a TestClient that uses the test database session.
    Override the get_db dependency to use the test session.
    """

    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
