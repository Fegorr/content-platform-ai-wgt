import uuid
from datetime import datetime, timedelta, timezone

import jwt

from src.config import get_jwt_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"


def create_access_token(user_id: str) -> str:
    """Return a signed token for the user that expires in 30 minutes."""
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the token payload, or None if the token is invalid."""
    # The secret is read outside the try so a missing secret raises RuntimeError.
    secret = get_jwt_secret_key()
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "jti", "exp"]},
        )
    except jwt.PyJWTError:
        return None
