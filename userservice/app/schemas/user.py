from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    email: EmailStr = Field(..., max_length=120)


class UserCreate(UserBase):
    password: SecretStr = Field(..., min_length=16, exclude=True)


class UserUpdate(UserBase):
    pass


class UserUpdatePassword(BaseModel):
    current_password: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=16)
    confirm_password: str = Field(..., min_length=16)


class UserDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    password: str | None = Field(None, exclude=True)

    created_at: datetime
    updated_at: datetime | None
