from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column, Session
import pytest

from app.models import Base
from app.repositories.base import BaseRepository
from app.schemas.pagination import PaginationParams


class DummyModel(Base):
    """Fictitious database model used exclusively for generic repository testing."""
    __tablename__ = "dummy_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)


@pytest.fixture
def repository(db: Session) -> BaseRepository[DummyModel]:
    """Instantiate BaseRepository targeting the DummyModel model."""
    return BaseRepository(DummyModel, db)


def test_create(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    item = DummyModel(name="Generic Item")

    # Act
    created = repository.create(item)

    # Assert
    assert created.id is not None
    # Verify persistence by querying the DB session directly
    persisted = db.get(DummyModel, created.id)
    assert persisted is not None
    assert persisted.name == "Generic Item"


def test_find_by_id_found(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    item = DummyModel(name="Found Item")
    db.add(item)
    db.commit()

    # Act
    found = repository.find_by_id(item.id)

    # Assert
    assert found is not None
    assert found.id == item.id
    assert found.name == "Found Item"


def test_find_by_id_not_found(repository: BaseRepository[DummyModel]) -> None:
    # Act
    found = repository.find_by_id(9999)

    # Assert
    assert found is None


def test_find_all(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    item1 = DummyModel(name="Item A")
    item2 = DummyModel(name="Item B")
    db.add(item1)
    db.add(item2)
    db.commit()

    # Act
    results = repository.find_all()

    # Assert
    assert len(results) >= 2
    found_names = {item.name for item in results}
    assert "Item A" in found_names
    assert "Item B" in found_names


def test_update(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    item = DummyModel(name="Old Name")
    db.add(item)
    db.commit()
    item.name = "Updated Name"

    # Act
    updated = repository.update(item)

    # Assert
    assert updated.name == "Updated Name"

    # Force reload from the database to ensure changes are flushed/committed
    db.expire(item)
    persisted = db.get(DummyModel, item.id)
    assert persisted is not None
    assert persisted.name == "Updated Name"


def test_delete(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    item = DummyModel(name="To Delete")
    db.add(item)
    db.commit()
    item_id = item.id

    # Act
    repository.delete(item)

    # Assert
    persisted = db.get(DummyModel, item_id)
    assert persisted is None


def test_paginate_default_query(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    for i in range(5):
        db.add(DummyModel(name=f"Item {i}"))
    db.commit()
    params = PaginationParams(page=1, per_page=2)

    # Act
    items, total = repository.paginate(params)

    # Assert
    assert len(items) == 2
    assert total >= 5


def test_paginate_custom_query(repository: BaseRepository[DummyModel], db: Session) -> None:
    # Arrange
    for i in range(3):
        db.add(DummyModel(name=f"Filter {i}"))
    for i in range(2):
        db.add(DummyModel(name=f"Other {i}"))
    db.commit()

    params = PaginationParams(page=1, per_page=10)
    query = select(DummyModel).where(DummyModel.name.like("Filter%"))

    # Act
    items, total = repository.paginate(params, query=query)

    # Assert
    assert len(items) == 3
    assert total == 3
    for item in items:
        assert item.name.startswith("Filter")
