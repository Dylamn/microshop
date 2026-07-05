import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SettingsDep
from app.db import engine
from app.schemas.healthcheck import (
    HealthContextResponse,
    LivenessProbeResponse,
    ReadinessProbeResponse,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=LivenessProbeResponse)
async def live() -> JSONResponse:
    """
    Liveness probe

    Basic check to confirm the API process is running.
    """
    status = LivenessProbeResponse()

    return JSONResponse(status.model_dump())


@router.get("/ready", response_model=ReadinessProbeResponse)
async def ready() -> JSONResponse:
    """
    Readiness probe

    Checks connections to critical dependencies.
    """
    status = ReadinessProbeResponse()

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        status.database = ServiceStatus.OK
    except SQLAlchemyError as e:
        logger.error("Database connection error.", exc_info=e)
        status.database = ServiceStatus.UNAVAILABLE

    http_status = 200 if status.is_ready else 503

    return JSONResponse(content=status.model_dump(), status_code=http_status)


@router.get("/details", response_model=HealthContextResponse)
async def details(settings: SettingsDep) -> JSONResponse:
    """Returns internal service metadata (non-sensitive)."""
    health_ctx = HealthContextResponse.model_validate(
        {
            "service": "userservice",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": int(asyncio.get_event_loop().time()),
        }
    )

    return JSONResponse(health_ctx.model_dump())
