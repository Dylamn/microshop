from collections.abc import Sequence
from typing import TypedDict

from pydantic import AliasChoices, BaseModel, Field


class PaginationMetadata(TypedDict):
    total: int
    per_page: int
    current_page: int
    last_page: int
    from_: int
    to: int


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1)

    @property
    def get_skip(self) -> int:
        """
        Gets the number of items to skip based on the current page and items per page.

        This property calculates the offset for paginated data retrieval.
        It is useful in scenarios such as database queries.

        Returns:
            int: Number of items to skip to get to the current page.
        """
        return (self.page - 1) * self.per_page

    def get_pagination_metadata(self, total: int = 0) -> PaginationMetadata:
        """
        Generates metadata for pagination based on the total number of records available.

        Args:
            total: The total number of records available (can be None).

        Returns:
            PaginationMetadata: A dictionary containing pagination metadata.
        """
        total = total or 0
        from_ = self.get_skip + 1 if total else 0

        return {
            "total": total,
            "per_page": self.per_page,
            "current_page": self.page,
            "last_page": (total // self.per_page + (1 if total % self.per_page else 0)) or 1,
            "from_": from_,
            "to": self.get_skip + self.per_page if self.get_skip + self.per_page < total else total
        }


class PaginationResponse[T](BaseModel):
    total: int
    per_page: int
    current_page: int
    last_page: int
    from_: int = Field(..., validation_alias=AliasChoices('from', 'from_'), serialization_alias="from")
    to: int

    data: Sequence[T]
