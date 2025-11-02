from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from .api import router
from .core.config import settings
from .core.logging_config import setup_logging

setup_logging(settings.ENVIRONMENT)

app = FastAPI(
    title="Userservice API",
    description="API for managing users of the Microshop system",
    version=settings.VERSION,
)

app.add_middleware(CorrelationIdMiddleware, header_name='X-Request-ID')

app.include_router(router)
