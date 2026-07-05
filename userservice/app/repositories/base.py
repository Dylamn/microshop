from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import ORMOption

from app.models import Base
from app.schemas.pagination import PaginationParams


class BaseRepository[T: Base]:
    """
    Generic repository providing common database operations for any SQLAlchemy model.

    This repository handles:
    - CRUD operations
    - Pagination
    - Basic queries
    """

    def __init__(self, model: type[T], session: Session):
        self.model = model
        self.session = session

    def paginate(
        self,
        pagination: PaginationParams,
        query: Select[tuple[T]] | None = None,
        unique: bool = False,
    ) -> tuple[Sequence[T], int]:
        """
        Paginates a query with the given pagination parameters.

        Args:
            pagination: Pagination parameters.
            query: Optional pre-built query. If None, selects all from the model.
            unique: If True, returns only unique results. This is meant for queries that
                join multiple tables and return duplicate rows.

        Returns:
            PaginationResponse containing metadata and results.
        """
        if query is None:
            query = select(self.model)

        count_query = query.with_only_columns(
            func.count(), maintain_column_froms=True
        ).order_by(None)

        total = self.session.scalar(count_query) or 0
        query = query.offset(pagination.get_skip).limit(pagination.per_page)
        result = self.session.execute(query).scalars()

        if unique:
            result = result.unique()

        return result.all(), total

    def find_by_id(
        self,
        ident: Any,
        *,
        options: list[ORMOption] | None = None
    ) -> T | None:
        """
        Retrieves a record from the database by its identifier.

        This method attempts to retrieve an entity of the specified model type by
        its identifier (mainly referred to as its primary key).
        Additional query options can be passed to customize the retrieval process,
        like specifying relationships to be loaded (eager/lazy loading).

        Args:
            ident: The identifier of the record to retrieve.
            options: A list of ORMOption instances used to alter the query behavior
                (optional).

        Returns:
            The record of type `T` if found, otherwise None.
        """
        return self.session.get(self.model, ident, options=options)

    def find_all(self) -> Sequence[T]:
        """Retrieves all entities."""
        stmt = select(self.model)
        return self.session.execute(stmt).scalars().all()

    def create(self, entity: T) -> T:
        """
        Creates a new entity in the database.

        Persists an entity into the database session, commits the transaction,
        and refreshes the entity instance with its latest state from the database.

        Args:
            entity: The entity object to be created in the database.

        Returns:
            The created entity, including any updated attributes set by the database.
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """
        Updates an existing entity in the database.

        This method updates the provided entity in the database by adding it to the
        current session, committing the changes, and refreshing the state of the entity
        to reflect the latest database state. The updated entity is then returned.

        Args:
            entity: The entity to be updated in the database.

        Returns:
            The updated entity after saving changes to the database.
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """
        Deletes the specified entity from the database.

        This method removes the given entity from the database session and commits
        the transaction. It is the responsibility of the caller to ensure the entity
        exists in the session before invoking this method.

        Args:
            entity: The entity object to be deleted from the database.

        Returns:
            None
        """
        # TODO: Handle exceptions
        self.session.delete(entity)
        self.session.commit()
