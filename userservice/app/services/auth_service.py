from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import security
from app.models import User
from app.schemas.user import UserUpdatePassword, UserDB


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email).first()

def authenticate(session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)

    if not db_user:
        return None
    if not security.verify_password(password, db_user.password):
        return None
    return db_user


def update_user_password(session: Session, user: UserDB, passwords: UserUpdatePassword) -> None:
    if user.password is None:
        # User can have no password if they are using external authentication.
        # In a further version, a user authentication source will be introduced.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User does not have a password")

    if not security.verify_password(passwords.current_password, user.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid current password")
    elif passwords.new_password != passwords.confirm_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    elif passwords.current_password == passwords.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password")

    stmt = text("UPDATE users SET password = :password WHERE id = :id")

    hash_password = security.hash_password(passwords.new_password)
    params = {"id": user.id, "password": hash_password}

    session.execute(stmt, params)
    session.commit()
