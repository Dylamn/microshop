import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import AuthUser
from app.core.errors.exceptions import NotFoundException
from app.schemas.pagination import PaginationParams, PaginationResponse
from app.schemas.user import (
    UserCollectionResource,
    UserCreate,
    UserResource,
    UserUpdate,
)
from app.services.user_service import UserServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginationResponse[UserCollectionResource])
async def index(
    current_user: AuthUser,
    user_service: UserServiceDep,
    pagination: Annotated[PaginationParams, Query()]
) -> Any:
    """
    Gets a list of all registered users.
    """
    logger.debug("Fetching all users.", extra={"actor": current_user.id})

    result = user_service.paginate(pagination)

    return result


@router.post("", response_model=UserResource, status_code=status.HTTP_201_CREATED)
async def create(
    current_user: AuthUser,
    user_service: UserServiceDep,
    payload: UserCreate
) -> Any:
    """
    Creates a new user based on the provided information.
    """
    logger.info("Creating a new user.", extra={"actor": current_user.id, "payload": payload})
    new_user = user_service.create(payload)

    return new_user.todict()


@router.get("/{user_id}", response_model=UserResource)
async def show(
    current_user: AuthUser,
    user_service: UserServiceDep,
    user_id: UUID
) -> Any:
    """
    Fetches a specific user resource based on their unique identifier.
    """
    logger.debug(f"Fetching user with id: {user_id}", extra={"actor": current_user.id})
    user = user_service.find_by_id(user_id)

    if user is None:
        raise NotFoundException(detail="User not found")

    return user


@router.patch("/{user_id}", response_model=UserResource)
@router.put("/{user_id}", response_model=UserResource)
async def update(
    current_user: AuthUser,
    user_service: UserServiceDep,
    user_id: UUID,
    payload: UserUpdate
) -> Any:
    """
    Updates a specific user resource based on their unique identifier.

    This endpoint does not handle password updates. Rather, use the `/auth/password` endpoint.
    """
    logger.info(f"Updating user with id: {user_id}", extra={"actor": current_user.id, "payload": payload})
    updated_user = user_service.update(user_id, payload)

    if updated_user is None:
        raise NotFoundException(detail="User not found")

    return updated_user.todict()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    user_service: UserServiceDep,
    current_user: AuthUser,
    user_id: UUID
) -> None:
    """
    Deletes a specific user resource based on their unique identifier.

    \f

    If the user does not exist, its action is a no-op.
    """
    logger.info(f"Deleting user with id: {user_id}", extra={"actor": current_user.id})

    user_service.delete(user_id)
