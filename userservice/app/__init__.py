from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .api import router
from .core.config import settings
from .core.errors.exceptions import ApiException, AuthorizationException
from .core.errors.handlers import (
    api_authorization_exception_handler,
    api_exception_handler,
    api_validation_exception_handler,
)
from .core.logging_config import setup_logging

setup_logging(settings.ENVIRONMENT)

app = FastAPI(
    title="Userservice API",
    description="API for managing users of the Microshop system",
    version=settings.VERSION,
)

# Add middlewares below...
app.add_middleware(CorrelationIdMiddleware, header_name='X-Request-ID')

# Register custom exception handlers here...
app.add_exception_handler(RequestValidationError, api_validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(AuthorizationException, api_authorization_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(ApiException, api_exception_handler)  # type: ignore[arg-type]

app.include_router(router)
