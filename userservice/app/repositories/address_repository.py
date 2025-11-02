from app.models import Address

from .base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self) -> None:
        super().__init__(Address)
