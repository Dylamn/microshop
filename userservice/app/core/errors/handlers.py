import logging
from datetime import UTC, datetime

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from .exceptions import ApiException, AuthorizationException
from .schemas import ApiError, ApiErrorDetail

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: ApiException) -> ORJSONResponse:
    """
    Handler for API custom exceptions.
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content=exc.tojson(request)
    )


async def api_authorization_exception_handler(_: Request, exc: AuthorizationException) -> ORJSONResponse:
    """
    Handler for authorization errors.
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content=exc.tojson(None)
    )

async def api_validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    """
    Handler for Pydantic errors occurring on request validation.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(
            ApiErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"]
            )
        )

    problem = ApiError(
        type="validation_error",
        title="Validation error",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="The given data is not valid.",
        instance=str(request.url.path),
        timestamp=datetime.now(UTC),
        errors=errors
    )

    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(mode="json", exclude_none=True)
    )


async def api_generic_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    Handler for non-handled exceptions.
    """
    logger.exception(exc)

    problem = ApiError(
        type="internal_error",
        title="Internal server error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later or contact support if the problem persists.",
        instance=str(request.url.path),
        timestamp=datetime.now(UTC)
    )

    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.model_dump(mode="json", exclude_none=True)
    )
