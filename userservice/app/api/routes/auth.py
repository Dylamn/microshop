import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.services import auth_service, user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/access-token")
async def login(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    # TODO: Protect against timing attacks
    logger.debug(f"Authentication request for user `{form_data.username}`")

    user = auth_service.authenticate(
        session,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, access_token_expires)

    return Token(access_token=token, token_type="bearer")


@router.post("/register")
async def register(session: SessionDep, payload: UserCreate) -> Token:
    logger.debug(f"Registering user: {payload.model_dump_json()}")
    user = user_service.create_user(session, payload)
    access_token_expires = timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, access_token_expires)

    return Token(access_token=token, token_type="bearer")


@router.get("/logout")
async def logout() -> dict[str, str]:
    logger.debug("Logging out user...")
    return {"message": "Goodbye World"}
