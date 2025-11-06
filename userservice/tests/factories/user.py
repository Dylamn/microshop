import uuid
import factory

from app.core.security import hash_password
from app.models.user import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)

    username = factory.Faker("first_name")
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)

    password = factory.LazyFunction(
       lambda: hash_password("password")
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Handle the password argument before creating the user
        if "password" in kwargs:
            kwargs["password"] = hash_password(kwargs.pop("password"))
        return super()._create(model_class, *args, **kwargs)