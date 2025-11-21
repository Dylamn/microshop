import factory

from app.models.address import Address
from tests.factories.user import UserFactory
from .base import BaseFactory


class AddressFactory(BaseFactory):
    class Meta:
        model = Address

    street = factory.Faker("street_address")
    city = factory.Faker("city")
    state = factory.Faker("state")
    zipcode = factory.Faker("postcode")

    user = factory.SubFactory(UserFactory)
