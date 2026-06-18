from typing import Any
import uuid
import factory

from app.core.security import hash_password
from app.models.user import User
from .base import BaseFactory


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id: uuid.UUID = factory.LazyFunction(uuid.uuid4)

    username: str = factory.Faker("first_name")
    email: str = factory.LazyAttributeSequence(
        lambda obj, n: f"{obj.username.lower()}{n}@example.com"
    )

    password: str = factory.LazyFunction(
       lambda: hash_password("password")
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs: Any):
        # Handle the password argument before creating the user
        if "password" in kwargs:
            kwargs["password"] = hash_password(kwargs.pop("password"))

        return super()._create(model_class, *args, **kwargs)