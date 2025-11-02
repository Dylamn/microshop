from datetime import datetime

from pydantic import BaseModel, Field


class ApiErrorDetail(BaseModel):
    """
    Specific error detail, especially related to validation errors.
    """
    field: str
    message: str
    code: str | None = None


class ApiError(BaseModel):
    """
    Error response schema, based on RFC 7807.
    """
    type: str = Field(
        ...,
        description="Identifier of the problem type",
        examples=["validation_error", "not_found", "authentication_error"]
    )
    title: str = Field(
        ...,
        description="Short and concise summary of the problem"
    )
    status: int = Field(
        ...,
        description="HTTP status code associated with this problem",
        ge=400,
        le=599
    )
    detail: str = Field(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem"
    )
    instance: str | None = Field(
        ...,
        description="The URI of the resource associated with the error",
        exclude_if=lambda field_: field_ is None
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of when the problem occurred"
    )
    errors: list[ApiErrorDetail] | None = Field(
        None,
        description="A list of errors associated with this problem"
    )
