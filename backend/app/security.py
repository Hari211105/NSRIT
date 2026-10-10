"""
UPSKILL AI - Security helpers (Phase 7A)

Password hashing (bcrypt via the bcrypt package directly) and JWT creation /
validation (python-jose).

bcrypt is used directly rather than passlib because newer bcrypt releases
(4.1+) break passlib's bcrypt backend; direct usage has no such wrapper
dependency and is simpler to reason about.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


# ------------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the encoded hash."""
    # bcrypt handles passwords as bytes; bytes(password, 'utf-8') is required.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: Optional[str]) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Returns False (never raises) when the stored hash is missing or malformed,
    so a legacy account without a password simply cannot log in.
    """
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed stored hash / wrong input types.
        return False


# ------------------------------------------------------------------
# JWT tokens
# ------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT access token for the given user id.

    `sub` carries the user id as a string (JWT spec). `exp` is set so tokens
    expire after JWT_ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[int]:
    """
    Decode and verify a JWT access token.

    Returns the encoded user id (int) on success, or None if the token is
    invalid, expired, or malformed. The caller is responsible for turning a
    None into a 401.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError, TypeError):
        return None