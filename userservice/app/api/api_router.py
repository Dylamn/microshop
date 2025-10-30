from fastapi import APIRouter

from .routes import addresses, auth, healthcheck, users

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(addresses.router)
router.include_router(healthcheck.router)
