from fastapi import APIRouter

from .routes import auth_routes

router = APIRouter()

router.include_router(auth_routes.router)
