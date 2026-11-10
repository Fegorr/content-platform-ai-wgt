from functools import lru_cache

import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from src import config


@lru_cache
def get_client() -> MongoClient:
    """Create the MongoDB client on first call and reuse it afterwards."""
    return MongoClient(
        config.get_mongodb_uri(),
        server_api=ServerApi("1"),
        tlsCAFile=certifi.where(),
    )


def get_content_collection():
    """Return the content collection of the content-platform database."""
    return get_client()["content-platform"]["content"]
