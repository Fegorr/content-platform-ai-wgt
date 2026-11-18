def strip_mongo_id(document: dict) -> dict:
    """Return a copy of the document without Mongo's _id."""
    return {key: value for key, value in document.items() if key != "_id"}
