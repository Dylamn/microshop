import factory

from app.models.address import Address
from tests.factories.user import UserFactory


class AddressFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Address
        sqlalchemy_session_persistence = "commit"

    street = factory.Faker("street_address")
    city = factory.Faker("city")
    state = factory.Faker("state")
    zipcode = factory.Faker("postcode")

    user = factory.SubFactory(UserFactory)
