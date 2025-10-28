from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    data = user_in.model_dump(exclude_unset=True, exclude_defaults=True)
    data["password"] = hash_password(user_in.password.get_secret_value())

    db_user = User(**data)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
