from sqlalchemy.orm import Session

from app.models import Address

from .base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: Session) -> None:
        super().__init__(Address, session)
