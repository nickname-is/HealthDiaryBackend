from datetime import datetime, timedelta, timezone

import secrets
import jwt
import bcrypt

from core.config import settings


ALGORITHM = "HS256"

TOKEN_TYPE_FIELD = "type"


def create_access_token(
        subject: int,
        expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        TOKEN_TYPE_FIELD: settings.ACCESS_TOKEN_KEY,
        "sub": subject,
        "exp": expire
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hash_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hash_password.decode("utf-8")