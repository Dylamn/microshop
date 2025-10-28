import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AuthUser, SessionDep
from app.models import User
from app.schemas.user import UserCreate, UserResource, UserUpdate
from app.services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResource])
async def index(session: SessionDep, current_user: AuthUser) -> Any:
    """
    Gets a list of all registered users.
    """
    logger.debug("Fetching all users.", extra={"actor": current_user.id})

    return user_service.get_all(session)


@router.post("", response_model=UserResource, status_code=status.HTTP_201_CREATED)
async def create(session: SessionDep, current_user: AuthUser, payload: UserCreate) -> Any:
    """
    Creates a new user based on the provided information.
    """
    logger.info("Creating a new user.", extra={"actor": current_user.id, "payload": payload})
    new_user = user_service.create_user(session, payload)

    return new_user


@router.get("/{user_id}", response_model=UserResource)
async def show(session: SessionDep, current_user: AuthUser, user_id: UUID) -> Any:
    """
    Fetches a specific user resource based on their unique identifier.
    """
    logger.debug(f"Fetching user with id: {user_id}", extra={"actor": current_user.id})
    user = user_service.find_user_by_id(session, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{user_id}", response_model=UserResource)
@router.put("/{user_id}", response_model=UserResource)
async def update(
    session: SessionDep,
    current_user: AuthUser,
    user_id: UUID,
    payload: UserUpdate
) -> Any:
    """
    Updates a specific user resource based on their unique identifier.

    This endpoint does not handle password updates. Rather, use the `/auth/password` endpoint.
    """
    logger.info(f"Updating user with id: {user_id}", extra={"actor": current_user.id, "payload": payload})
    updated_user = user_service.update_user(session, user_id, payload)

    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(session: SessionDep, current_user: AuthUser, user_id: UUID) -> None:
    """
    Deletes a specific user resource based on their unique identifier.

    \f

    If the user does not exist, its action is a no-op.
    """
    logger.info(f"Deleting user with id: {user_id}", extra={"actor": current_user.id})

    user_service.delete_user(session, user_id)
