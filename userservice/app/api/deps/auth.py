from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.errors import InvalidTokenError
from sqlalchemy import select

from app.core.config import settings
from app.models import User
from app.schemas.token import TokenClaims
from app.schemas.user import UserDB

from .db import SessionDep

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/login/access-token"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> UserDB:
    try:
        decoded_token = jwt.decode(
            token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        claims = TokenClaims(**decoded_token.claims)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    stmt = select(User).where(User.id == claims.sub)
    user = session.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserDB.model_validate(user)


AuthUser = Annotated[UserDB, Depends(get_current_user)]
