import logging
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AuthUser, SessionDep
from app.schemas.address import (
    AddressCreate,
    AddressQueryParams,
    AddressResource,
    AddressUpdate,
)
from app.schemas.pagination import PaginationResponse
from app.services.address_service import AddressServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=PaginationResponse[AddressResource])
async def index(
    session: SessionDep,
    current_user: AuthUser,
    address_service: AddressServiceDep,
    query_params: Annotated[AddressQueryParams, Query()]
) -> Any:
    """
    Fetches a list of addresses related to the current authenticated user.

    \f

    Args:
        session: Dependency-injected database session used to query the database.
        current_user: The authenticated user for whom the addresses will be fetched.
        address_service: Dependency-injected service instance for address operations.
        query_params: Pagination and filtering parameters for the query.
    Returns:
        list[AddressResource]: A list of serialized address resources.
    """
    logger.debug(f"Fetching addresses for user {current_user.id}", extra={"actor": current_user.id})
    return address_service.paginate(session, query_params)


@router.post("", response_model=AddressResource, status_code=status.HTTP_201_CREATED)
async def create(
    session: SessionDep,
    current_user: AuthUser,
    address_service: AddressServiceDep,
    payload: AddressCreate
) -> Any:
    logger.info(f"Creating address for user {current_user.id}", extra={"actor": current_user.id, "payload": payload})

    if current_user.id != payload.user_id:
        # Currently, as there's no permission mechanism,
        # we simply disallow the creation of addresses for other users.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="User cannot create address for another user")

    new_address = address_service.create(session, payload)

    return new_address


@router.get("/{address_id}", response_model=AddressResource)
async def show(
    session: SessionDep,
    current_user: AuthUser,
    address_service: AddressServiceDep,
    address_id: int
) -> Any:
    """
    Fetches and returns details of a specific address based on the provided address ID.
    """
    logger.debug(f"Fetching address with id: {address_id}", extra={"actor": current_user.id})
    address = address_service.find_by_id(session, address_id)

    if address is None or address.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Address not found")

    return address


@router.patch("/{address_id}", response_model=AddressResource)
@router.put("/{address_id}", response_model=AddressResource)
async def update(
    session: SessionDep,
    current_user: AuthUser,
    address_service: AddressServiceDep,
    address_id: int,
    payload: AddressUpdate
) -> Any:
    """
    Updates the details of an existing address resource identified by the given address ID.
    """
    logger.info(f"Updating address with id: {address_id}", extra={"actor": current_user.id, "payload": payload})

    address = address_service.update(session, address_id, payload, owner=current_user.id)

    if address is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Address not found")

    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    session: SessionDep,
    current_user: AuthUser,
    address_service: AddressServiceDep,
    address_id: int
) -> None:
    """
    Deletes a specific address belonging to the authenticated user.
    """
    logger.info(f"Deleting address with id: {address_id}", extra={"actor": current_user.id})

    address_service.delete(session, address_id, owner=current_user.id)
