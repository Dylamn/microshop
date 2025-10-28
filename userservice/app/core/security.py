from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from joserfc import jwt

from .config import settings

pwd_context = PasswordHasher()


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """
    Creates a JSON Web Token (JWT) access token with an expiry time.

    This function generates a signed JWT token using the configured algorithm and secret key.
    The token includes an expiration time (`exp`) and a subject identifier (`sub`).

    Args:
        subject (str | Any): The subject identifier to include in the token payload.
        expires_delta (timedelta): A time duration indicating the validity period of the token.

    Returns:
        str: The encoded JWT as a string.
    """
    expires_at = datetime.now(UTC) + expires_delta
    jwt_header = {"alg": settings.JWT_ALGORITHM}
    jwt_payload = {"exp": expires_at, "sub": str(subject)}

    return jwt.encode(jwt_header, jwt_payload, key=settings.JWT_SECRET)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(hashed_password, password=plain_password)
    except VerifyMismatchError:
        return False


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
