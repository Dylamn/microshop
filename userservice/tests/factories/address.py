from app.models import User
import factory

from app.models.address import Address
from tests.factories.user import UserFactory
from .base import BaseFactory


class AddressFactory(BaseFactory):
    class Meta:
        model = Address

    id: int = factory.Sequence(lambda n: n + 1)

    street: str = factory.Faker("street_address")
    city: str = factory.Faker("city")
    state: str = factory.Faker("state")
    zipcode: str = factory.Faker("postcode")

    user: User = factory.SubFactory(UserFactory)
