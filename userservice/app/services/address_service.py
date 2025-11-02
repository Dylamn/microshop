import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Address
from app.repositories.address_repository import AddressRepository
from app.schemas.address import (
    AddressCreate,
    AddressQueryParams,
    AddressResource,
    AddressUpdate,
)
from app.schemas.pagination import PaginationResponse

logger = logging.getLogger(__name__)


def get_address_service() -> "AddressService":
    return AddressService()


AddressServiceDep = Annotated["AddressService", Depends(get_address_service)]


class AddressService:
    def __init__(self) -> None:
        self.repository = AddressRepository()

    def paginate(
        self,
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
            query = query.where(Address.user_id == criteria.user_id)

        addresses, total = self.repository.paginate(session, criteria, query)

        return criteria.to_response(addresses, total)


    def find_by_id(self, session: Session, address_id: int) -> Address | None:
        return self.repository.find_by_id(session, address_id)


    def create(self, session: Session, payload: AddressCreate) -> Address:
        """
        Creates a new address entry in the database based on the provided payload.

        Args:
            session (Session): Database session used for the operation.
            payload (AddressCreate): Data required to create a new address.

        Returns:
            The created Address model instance.
        """
        db_address = Address(**payload.model_dump())
        return self.repository.create(session, db_address)


    def update(
        self,
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
        address = self.repository.find_by_id(session, address_id)
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

    def delete(
        self, session: Session, address_id: int, *, owner: UUID) -> None:
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
        address = self.repository.find_by_id(session, address_id)
        if not address:
            return

        if address.user_id != owner:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this address")

        session.delete(address)
        session.commit()
