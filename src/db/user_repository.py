class UserRepository:
    """The only class that touches the users collection."""

    def __init__(self, collection):
        self._collection = collection

    @staticmethod
    def _strip_mongo_id(document: dict) -> dict:
        """Return a copy of the document without Mongo's _id."""
        return {key: value for key, value in document.items() if key != "_id"}

    def create(self, document: dict) -> str:
        """Insert the document and return its id."""
        self._collection.insert_one(dict(document))
        return document["id"]

    def get_by_id(self, user_id: str) -> dict | None:
        """Return the user with this id, or None if it doesn't exist."""
        document = self._collection.find_one({"id": user_id})
        if document is None:
            return None
        return self._strip_mongo_id(document)

    def get_by_email(self, email: str) -> dict | None:
        """Return the user with this email as given, or None if it doesn't exist."""
        document = self._collection.find_one({"email": email})
        if document is None:
            return None
        return self._strip_mongo_id(document)

    def update(self, user_id: str, updates: dict) -> int:
        """Apply the updates and return the matched count (0 if no such id)."""
        result = self._collection.update_one({"id": user_id}, {"$set": updates})
        return result.matched_count
