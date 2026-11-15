import os


def get_mongodb_uri() -> str:
    """Return the MongoDB URI, read from the environment when called."""
    try:
        return os.environ["MONGODB_URI"]
    except KeyError:
        raise RuntimeError("MONGODB_URI is not set") from None
