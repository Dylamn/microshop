from collections.abc import Callable, Sequence
from typing import TypedDict

from pydantic import AliasChoices, BaseModel, Field


class PaginationMetadata(TypedDict):
    total: int
    per_page: int
    current_page: int
    last_page: int
    from_: int
    to: int


class PaginationResponse[T](BaseModel):
    total: int
    per_page: int
    current_page: int
    last_page: int
    from_: int = Field(..., validation_alias=AliasChoices('from', 'from_'), serialization_alias="from")
    to: int

    data: Sequence[T]


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)

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

    def to_response[TSource, TTarget](
        self,
        data: Sequence[TSource],
        total: int,
        *,
        transform_fn: Callable[[TSource], TTarget]
    ) -> PaginationResponse[TTarget]:
        """
        Transforms a sequence of source objects (Models)
        into a paginated response containing target objects (Resources).

        Args:
            data (Sequence[TSource]): The data sequence to be transformed into resources.
            total (int): The total number of available items.
            transform_fn (Callable[[TSource], TTarget]):
                A function to transform each source object into a target object.
                Primarily used for converting Models (SQLAlchemy) to Resources (Pydantic).

        Returns:
            PaginationResponse[TTarget]: A paginated response including metadata and transformed data.
        """
        transformed_data = [transform_fn(item) for item in data]

        return PaginationResponse(**self.get_pagination_metadata(total), data=transformed_data)

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
        to = from_ + self.per_page - 1

        if to > total:
            to = total

        return {
            "total": total,
            "per_page": self.per_page,
            "current_page": self.page,
            "last_page": (total // self.per_page + (1 if total % self.per_page else 0)) or 1,
            "from_": from_,
            "to": to
        }
