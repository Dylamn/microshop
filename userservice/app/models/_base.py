from typing import Any, Self

from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def update(
        self,
        data: BaseModel | dict[str, Any],
        *,
        overrides: dict[str, Any] | None = None,
    ) -> Self:
        """
        Updates the attributes of the current instance using the data provided in
        the input. This method takes into account keys from a dictionary or a
        BaseModel instance.

        It also allows for overrides to supersede the specified data fields.
        Only attributes already defined on the instance will be updated.

        This method does not commit any changes to the database.

        Args:
            data: A dictionary or BaseModel containing fields to update the current
                instance with.
            overrides: An optional dictionary of key-value pairs to override or
                supplement the `data` argument.

        Example:
            >>> model_data = {"username": "john", "email": "john@example.com", "password": "plain123"}
            >>> model_extra = {"password": "hashed_password")}
            >>> Base.update(model_data, overrides=model_extra)

        Returns:
            Self: The instance with updated attributes.
        """
        overrides = (overrides or {}).copy()

        if isinstance(data, BaseModel):
            data = data.model_dump()

        merged_data = {**data, **overrides}

        for key, value in merged_data.items():
            if hasattr(self, key):
                setattr(self, key, value)

        return self

    def todict(self) -> dict[str, Any]:
        """
        A to `dict` method that extend relationships only if they're loaded.
        """
        result: dict[str, Any] = {}

        state = inspect(self)

        for attr in state.mapper.column_attrs:
            result[attr.key] = getattr(self, attr.key)

        for relationship in state.mapper.relationships:
            if (
                relationship.key in state.dict
                and relationship.key not in state.unloaded
            ):
                result[relationship.key] = getattr(self, relationship.key)

                if isinstance(result[relationship.key], list):
                    result[relationship.key] = [
                        item.todict() if hasattr(item, "todict") else item
                        for item in result[relationship.key]
                    ]
                # If it's a single object, convert it recursively'
                elif result[relationship.key] is not None and hasattr(
                    result[relationship.key], "todict"
                ):
                    result[relationship.key] = result[relationship.key].todict()

        return result
