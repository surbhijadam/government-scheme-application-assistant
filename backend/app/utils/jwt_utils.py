import os
from datetime import datetime, timedelta, timezone

import jwt

ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 24


def generate_token(user_id, role):
    """Create a signed JWT that identifies this user."""
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is not set")

    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_LIFETIME_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_token(token):
    """Verify a JWT and return its payload, or raise jwt exceptions if invalid."""
    secret_key = os.getenv("SECRET_KEY")
    return jwt.decode(token, secret_key, algorithms=[ALGORITHM]) #type: ignore