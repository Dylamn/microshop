from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from .api import router
from .core.config import settings
from .core.logging_config import setup_logging

setup_logging(settings.ENVIRONMENT)

app = FastAPI()

app.add_middleware(CorrelationIdMiddleware, header_name='X-Request-ID')

app.include_router(router)
