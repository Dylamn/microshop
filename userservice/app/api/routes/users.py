import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AuthUser, SessionDep
from app.models import User
from app.schemas.user import UserCreate, UserDB
from app.services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserDB])
async def index(
    session: SessionDep,
    current_user: AuthUser
) -> Any:
    logger.debug("Fetching all users.", extra={"actor": current_user.id})
    # TODO: encapsulates the logic in the ``user_service``
    stmt = select(User)
    result = session.execute(stmt)

    return result.scalars().all()


@router.post("", response_model=UserDB)
async def create(
    session: SessionDep,
    payload: UserCreate,
    current_user: AuthUser
) -> Any:
    logger.info("Creating a new user.", extra={"actor": current_user.id, "payload": payload})
    new_user = user_service.create_user(session, payload)

    return new_user


@router.get("/{user_id}", response_model=UserDB)
async def show(
    session: SessionDep,
    current_user: AuthUser,
    user_id: int
) -> Any:
    logger.debug(f"Fetching user with id: {user_id}", extra={"actor": current_user.id})
    # TODO: encapsulates the logic in the ``user_service``
    stmt = select(User).where(User.id == user_id)

    user = session.execute(stmt).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

