import logging
from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Address
from app.schemas.address import (
    AddressCreate,
    AddressQueryParams,
    AddressResource,
    AddressUpdate,
)
from app.schemas.pagination import PaginationResponse

logger = logging.getLogger(__name__)


def paginate(
    session: Session,
    criteria: AddressQueryParams
) -> PaginationResponse[AddressResource]:
    """
    Paginates a query of Address entities based on given filters and pagination parameters.

    Args:
        session (Session): SQLAlchemy session object used to interact with the database.
        criteria (AddressQueryParams): Object containing pagination and filters.

    Returns:
        PaginationResponse[Address]: An object encapsulating pagination metadata and
            the list of Address records matching the query criteria.
    """
    query = select(Address)

    if criteria.user_id:
        query = query.where(Address.user_id.is_(criteria.user_id))

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # TODO: with the total, we can predicate if the ongoing will return an
    #   empty list. If so, we can skip the following query.
    query = query.offset(criteria.get_skip).limit(criteria.per_page)

    result = session.execute(query.order_by(Address.id)).scalars().all()

    return PaginationResponse(**criteria.get_pagination_metadata(total), data=result)


def get_addresses(session: Session, user_id: UUID | None = None) -> Sequence[Address]:
    """
    Retrieves a list of addresses optionally filtered by a specific user ID.

    Args:
        session (Session): The database session used to execute the query.
        user_id (UUID | None): An optional unique identifier of the user whose
            addresses are being fetched. If not provided, all addresses are retrieved.

    Returns:
        Sequence[Address]: A sequence of Address objects fetched from the database.
    """
    query = select(Address)

    if user_id:
        query = query.where(Address.user_id == user_id)

    return session.execute(query).scalars().all()


def find_address_by_id(session: Session, address_id: int) -> Address | None:
    """
    Retrieve an address entity from the database by its unique identifier.

    This function performs a query to fetch an Address object from the database
    using its unique `address_id`. If no matching address is found, it returns
    None.

    Args:
        session (Session): Database session used to execute the query.
        address_id (int): Unique identifier of the address to retrieve.

    Returns:
        Address | None: The Address object matching the given identifier, or
        None if no match is found.
    """
    query = select(Address).where(Address.id == address_id)

    return session.execute(query).scalar_one_or_none()


def create_address(session: Session, payload: AddressCreate) -> Address:
    """
    Creates a new address entry in the database based on the provided payload.

    Args:
        session (Session): Database session used for the operation.
        payload (AddressCreate): Data required to create a new address.

    Returns:
        The created Address model instance.
    """
    db_address = Address(**payload.model_dump())

    session.add(db_address)
    session.commit()
    session.refresh(db_address)

    return db_address


def update_address(
    session: Session,
    address_id: int,
    payload: AddressUpdate,
    *,
    owner: UUID
) -> Address | None:
    """
    Updates an existing address in the database with the provided data.

    The function looks for the address using the provided `address_id`. If the
    address is found, it updates the address with the new data from `payload`,
    commits the changes to the database, refreshes the address instance, and
    returns the updated address. If the address cannot be found, it returns None.

    Args:
        session (Session): The database session to be used for querying and
            committing changes.
        address_id (UUID): The unique identifier of the address to update.
        payload (AddressUpdate): The data used to update the address.
        owner (UUID): The unique identifier of the user who owns the address.
            Used for authorization checks.

    Returns:
        The updated address object if the address is found, otherwise None.
    """
    address = find_address_by_id(session, address_id)
    if not address:
        return None

    if address.user_id != owner:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this address")

    address.update(payload)
    session.commit()
    session.refresh(address)

    return address


def delete_address(session: Session, address_id: int, *, owner: UUID) -> None:
    """
    Deletes an address record from the database corresponding to the given address ID.

    This function interacts with the database session to remove the address specified by the
    address ID. It ensures the proper handling of database operations and maintains data integrity.

    Args:
        session: The active database session to be used for executing the delete operation.
        address_id: The unique identifier of the address to be deleted.
        owner: Must be the identifier of the user who owns the address.
    Returns:
        None
    """
    address = find_address_by_id(session, address_id)
    if not address:
        return

    if address.user_id != owner:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this address")

    session.delete(address)
    session.commit()
