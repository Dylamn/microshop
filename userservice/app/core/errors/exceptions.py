from typing import Any

from fastapi import Request, status

from app.core.errors.schemas import ApiError, ApiErrorDetail


class ApiException(Exception):
    """
    Base class for all API exceptions.
    """

    def __init__(
        self,
        type_: str,
        title: str,
        status_code: int,
        detail: str,
        errors: list[dict[str, Any]] | None = None,
    ):
        self.type = type_
        self.title = title
        self.status_code = status_code
        self.detail = detail
        self.errors = errors
        super().__init__(detail)

    def to_api_error(self, request: Request | None = None) -> ApiError:
        instance = str(request.url.path) if request else None
        errors = (
            [ApiErrorDetail.model_validate(error) for error in self.errors]
            if self.errors
            else None
        )

        return ApiError(
            type=self.type,
            title=self.title,
            status=self.status_code,
            detail=self.detail,
            instance=instance,
            errors=errors,
        )

    def tojson(self, request: Request | None = None) -> dict[str, Any]:
        api_error = self.to_api_error(request)

        return api_error.model_dump(exclude_none=True)


class ValidationException(ApiException):
    """
    Validation error.
    """

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "A validation error occurred.",
        errors: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            type_="validation_error",
            title="Validation error",
            status_code=status_code,
            detail=detail,
            errors=errors,
        )


class NotFoundException(ApiException):
    """
    Error raised when a resource is not found.
    """

    def __init__(self, detail: str):
        super().__init__(
            type_="not_found",
            title="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class AuthorizationException(ApiException):
    """
    Error raised when authorization fails (for codes 400 and 401)

    If you want to raise this error for a permission-denied error,
    please use the `ApiPermissionException`.
    """

    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: str = "You are not logged in.",
    ):
        super().__init__(
            type_="authorization",
            title="Authorization",
            status_code=status_code,
            detail=detail,
        )


class PermissionException(ApiException):
    """
    Error raised when a user does not have the required permissions
    to perform an action on a specific resource.
    """

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            type_="permission",
            title="Permission error",
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
