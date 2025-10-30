from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination import PaginationParams


class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    zipcode: str


class AddressCreate(AddressBase):
    user_id: UUID


class AddressUpdate(AddressBase):
    pass


class AddressDB(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., gt=0)
    user_id: UUID


class AddressQueryParams(PaginationParams):
    user_id: UUID | None = None


class AddressResource(AddressBase):
    id: int
