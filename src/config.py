import os


def get_mongodb_uri() -> str:
    """Return the MongoDB URI, read from the environment when called."""
    try:
        return os.environ["MONGODB_URI"]
    except KeyError:
        raise RuntimeError("MONGODB_URI is not set") from None


def get_jwt_secret_key() -> str:
    """Return the JWT secret, read from the environment when called."""
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret:
        # An empty key would let anyone forge tokens.
        raise RuntimeError("JWT_SECRET_KEY is not set")
    return secret
