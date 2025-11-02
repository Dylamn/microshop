from typing import Annotated

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.errors import InvalidTokenError
from sqlalchemy.orm import lazyload

from app.api.deps.db import SessionDep
from app.core.config import settings
from app.core.errors.exceptions import AuthorizationException
from app.models import User
from app.schemas.token import TokenClaims

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/login/access-token"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        decoded_token = jwt.decode(
            token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        claims = TokenClaims(**decoded_token.claims)
    except InvalidTokenError:
        raise AuthorizationException(
            detail="Could not validate credentials",
        )

    user = session.get(User, claims.sub, options=[lazyload(User.addresses)])
    if not user:
        raise AuthorizationException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


AuthUser = Annotated[User, Depends(get_current_user)]
