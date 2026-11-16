from src.models.content import ContentStatus


class ContentRepository:
    """The only class that touches the content collection."""

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

    def get_by_id(self, content_id: str) -> dict | None:
        """Return the document with this id, or None if it doesn't exist."""
        document = self._collection.find_one({"id": content_id})
        if document is None:
            return None
        return self._strip_mongo_id(document)

    def list_visible(self, media_type: str, user_id: str) -> list[dict]:
        """Return published items of this type plus this user's drafts of this type."""
        cursor = self._collection.find(
            {
                "media_type": media_type,
                "$or": [
                    {"status": ContentStatus.PUBLISHED.value},
                    {"author_id": user_id},
                ],
            }
        )
        return [self._strip_mongo_id(document) for document in cursor]

    def list_all(self) -> list[dict]:
        """Return every content document of every type and user."""
        return [self._strip_mongo_id(document) for document in self._collection.find({})]

    def update(self, content_id: str, updates: dict) -> int:
        """Apply the updates and return the matched count (0 if no such id)."""
        result = self._collection.update_one({"id": content_id}, {"$set": updates})
        return result.matched_count

    def delete(self, content_id: str) -> int:
        """Delete the document and return the deleted count (0 if no such id)."""
        result = self._collection.delete_one({"id": content_id})
        return result.deleted_count
