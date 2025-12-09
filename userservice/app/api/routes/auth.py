import logging
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthUser, SessionDep
from app.core import security
from app.core.config import settings
from app.core.errors.exceptions import AuthorizationException
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResource, UserUpdatePassword
from app.services import auth_service
from app.services.user_service import UserServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/access-token")
async def login(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    logger.debug(f"Authentication request for user `{form_data.username}`")

    user = auth_service.authenticate(
        session,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise AuthorizationException(
            status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, access_token_expires)

    return Token(access_token=token, token_type="bearer")


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Token)
async def register(
    user_service: UserServiceDep,
    payload: UserCreate
) -> Token:
    logger.debug(f"Registering user: {payload.model_dump_json()}")
    new_user = user_service.create(payload)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(new_user.id, access_token_expires)

    return Token(access_token=token, token_type="bearer")


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    session: SessionDep,
    current_user: AuthUser,
    passwords: UserUpdatePassword
) -> None:
    logger.debug("User password update", extra={"actor": current_user.id})

    auth_service.update_user_password(
        session, current_user, passwords
    )

@router.get("/me", response_model=UserResource)
async def me(user: AuthUser) -> Any:
    return user


@router.post("/logout")
async def logout() -> dict[str, str]:
    logger.debug("Logging out user...")
    return {"message": "Goodbye World"}
