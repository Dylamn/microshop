from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ...models import User
from ...schemas.user import UserDB
from ..deps import SessionDep

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserDB])
async def index(session: SessionDep) -> Any:
    stmt = select(User)
    result = session.execute(stmt)

    return result.scalars().all()


@router.get("/{user_id}", response_model=UserDB)
async def get_user(session: SessionDep, user_id: int) -> Any:
    stmt = select(User).where(User.id == user_id)

    user = session.execute(stmt).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
