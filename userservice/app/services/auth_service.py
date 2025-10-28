from sqlalchemy.orm import Session

from app.core import security
from app.models import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email).first()

def authenticate(session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)

    if not db_user:
        return None
    if not security.verify_password(password, db_user.password):
        return None
    return db_user
