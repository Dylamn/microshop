import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def auth() -> dict[str, str]:
    logger.debug("Authenticating user...")
    return {"message": "Hello World"}


@router.get("/logout")
async def logout() -> dict[str, str]:
    logger.debug("Logging out user...")
    return {"message": "Goodbye World"}
