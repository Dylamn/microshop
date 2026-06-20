import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import SessionDep
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


def get_address_service(session: SessionDep) -> "AddressService":
    return AddressService(session)


AddressServiceDep = Annotated["AddressService", Depends(get_address_service)]


class AddressService:
    def __init__(self, session: Session) -> None:
        """
        Initialize `AddressService` with a database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.repository = AddressRepository(session)

    def paginate(
        self, criteria: AddressQueryParams
    ) -> PaginationResponse[AddressResource]:
        """
        Paginates a query of Address entities based on given filters and pagination parameters.

        Args:
            criteria (AddressQueryParams): Object containing pagination and filters.

        Returns:
            PaginationResponse[Address]: An object encapsulating pagination metadata and
                the list of Address records matching the query criteria.
        """
        query = select(Address)

        if criteria.user_id:
            query = query.where(Address.user_id == criteria.user_id)

        addresses, total = self.repository.paginate(criteria, query)

        return criteria.to_response(
            addresses, total, transform_fn=AddressResource.model_validate
        )

    def find_by_id(self, address_id: int) -> Address | None:
        return self.repository.find_by_id(address_id)

    def create(self, payload: AddressCreate) -> Address:
        """
        Creates a new address entry in the database based on the provided payload.

        Args:
            payload (AddressCreate): Data required to create a new address.

        Returns:
            The created Address model instance.
        """
        db_address = Address(**payload.model_dump())
        try:
            self.repository.create(db_address)
        except IntegrityError as exc:
            err_msg = str(exc.orig)

            if "23503" in err_msg or "FOREIGN KEY" in err_msg:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Unable to create address. The given user does not exist.",
                )

            raise

        return db_address

    def update(
        self, address_id: int, payload: AddressUpdate, *, owner: UUID
    ) -> Address | None:
        """
        Updates an existing address in the database with the provided data.

        The function looks for the address using the provided `address_id`. If the
        address is found, it updates the address with the new data from `payload`,
        commits the changes to the database, refreshes the address instance, and
        returns the updated address. If the address cannot be found, it returns None.

        Args:
            address_id (UUID): The unique identifier of the address to update.
            payload (AddressUpdate): The data used to update the address.
            owner (UUID): The unique identifier of the user who owns the address.
                Used for authorization checks.

        Returns:
            The updated address object if the address is found, otherwise None.
        """
        address = self.repository.find_by_id(address_id)
        if not address:
            return None

        if address.user_id != owner:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this address",
            )

        # Update address instance
        address.update(payload)

        return self.repository.update(address)

    def delete(self, address_id: int, *, owner: UUID) -> None:
        """
        Deletes an address record from the database corresponding to the given address ID.

        This function interacts with the database session to remove the address specified by the
        address ID. It ensures the proper handling of database operations and maintains data integrity.

        Args:
            address_id: The unique identifier of the address to be deleted.
            owner: Must be the identifier of the user who owns the address.
        Returns:
            None
        """
        address = self.repository.find_by_id(address_id)
        if not address:
            return

        if address.user_id != owner:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this address",
            )

        self.repository.delete(address)
