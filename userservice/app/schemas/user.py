from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    email: EmailStr = Field(..., max_length=120)


class UserDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    password: str | None = Field(None, exclude=True)

    created_at: datetime
    updated_at: datetime | None
