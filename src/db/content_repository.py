class ContentRepository:
    """The only class that touches the content collection."""

    def __init__(self, collection):
        self.collection = collection

    @staticmethod
    def _clean(document: dict) -> dict:
        """Return a copy of the document without Mongo's _id."""
        return {key: value for key, value in document.items() if key != "_id"}

    def create(self, document: dict) -> str:
        self.collection.insert_one(dict(document))
        return document["id"]

    def get_by_id(self, content_id: str) -> dict | None:
        document = self.collection.find_one({"id": content_id})
        if document is None:
            return None
        return self._clean(document)

    def list_visible(self, media_type: str, user_id: str) -> list[dict]:
        cursor = self.collection.find(
            {
                "media_type": media_type,
                "$or": [{"status": "published"}, {"author_id": user_id}],
            }
        )
        return [self._clean(document) for document in cursor]

    def list_all(self) -> list[dict]:
        return [self._clean(document) for document in self.collection.find({})]

    def update(self, content_id: str, updates: dict) -> int:
        result = self.collection.update_one({"id": content_id}, {"$set": updates})
        return result.matched_count

    def delete(self, content_id: str) -> int:
        result = self.collection.delete_one({"id": content_id})
        return result.deleted_count
