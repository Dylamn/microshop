import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login/access-token")
async def login() -> dict[str, str]:
    logger.debug("Authenticating user...")
    return {"message": "Hello World"}


@router.post("/register")
async def register() -> dict[str, str]:
    logger.debug("Registering user...")
    return {"message": "Hello World"}


@router.get("/logout")
async def logout() -> dict[str, str]:
    logger.debug("Logging out user...")
    return {"message": "Goodbye World"}
