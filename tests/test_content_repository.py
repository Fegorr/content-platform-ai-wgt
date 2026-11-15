import inspect
from unittest.mock import Mock

import pytest

from src.db.content_repository import ContentRepository


@pytest.fixture
def collection():
    """A Mock stand-in for the Mongo content collection."""
    return Mock()


@pytest.fixture
def repo(collection):
    """A ContentRepository over the Mock collection."""
    return ContentRepository(collection)


@pytest.fixture
def video_document():
    """A stored video document without _id."""
    return {
        "id": "v1",
        "title": "Intro",
        "author_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "created_at": "2026-10-25T10:00:00Z",
        "status": "draft",
        "media_type": "video",
        "url": "https://example.com/v.mp4",
        "file_name": "v.mp4",
        "duration": 72,
        "resolution": "1920x1080",
        "frame_rate": 30.0,
    }


def with_id(document, mongo_id="mongo-1"):
    """Return a copy of the document with a Mongo _id added."""
    return {**document, "_id": mongo_id}


def test_repository_takes_collection(collection):
    """The repository keeps the collection it is given and needs no client."""
    repo = ContentRepository(collection)
    collection.assert_not_called()
    assert list(inspect.signature(ContentRepository.__init__).parameters) == ["self", "collection"]
    assert repo is not None


def test_create_content_inserts_document(repo, collection, video_document):
    """create calls insert_one once with a dict equal to the document."""
    repo.create(video_document)
    collection.insert_one.assert_called_once_with(video_document)


def test_create_content_returns_document_id(repo, collection, video_document):
    """create returns document id, not Mongo's inserted_id."""
    collection.insert_one.return_value.inserted_id = "mongo-object-id"
    assert repo.create(video_document) == "v1"


def test_create_content_does_not_change_caller_dict(repo, collection, video_document):
    """create leaves the caller's dict without _id even if insert_one adds it."""
    collection.insert_one.side_effect = lambda doc: doc.update({"_id": "mongo-1"})
    original = dict(video_document)
    repo.create(video_document)
    assert "_id" not in video_document
    assert video_document == original
    collection.insert_one.assert_called_once()


def test_get_content_by_id(repo, collection, video_document):
    """get_by_id queries by the id field and returns the document."""
    collection.find_one.return_value = with_id(video_document)
    result = repo.get_by_id("v1")
    collection.find_one.assert_called_once_with({"id": "v1"})
    assert result == video_document


def test_get_content_by_id_strips_underscore_id(repo, collection, video_document):
    """get_by_id removes _id from the returned document."""
    collection.find_one.return_value = with_id(video_document)
    assert "_id" not in repo.get_by_id("v1")


def test_get_content_by_id_not_found(repo, collection):
    """get_by_id returns None when nothing is found."""
    collection.find_one.return_value = None
    assert repo.get_by_id("missing") is None
    collection.find_one.assert_called_once_with({"id": "missing"})


def test_list_visible_content_query(repo, collection, video_document):
    """list_visible filters published or own items by type in the database query."""
    collection.find.return_value = [with_id(video_document)]
    repo.list_visible("video", "user-1")
    collection.find.assert_called_once_with(
        {
            "media_type": "video",
            "$or": [{"status": "published"}, {"author_id": "user-1"}],
        }
    )


def test_list_visible_content_returns_documents_without_id(repo, collection, video_document):
    """list_visible returns every document with _id stripped."""
    second = {**video_document, "id": "v2"}
    collection.find.return_value = [with_id(video_document, "m1"), with_id(second, "m2")]
    result = repo.list_visible("video", "user-1")
    assert result == [video_document, second]
    assert all("_id" not in doc for doc in result)


def test_list_visible_content_empty(repo, collection):
    """list_visible returns an empty list when nothing matches."""
    collection.find.return_value = []
    assert repo.list_visible("video", "user-1") == []


def test_list_all_content_query(repo, collection):
    """list_all calls find with an empty filter once."""
    collection.find.return_value = []
    repo.list_all()
    collection.find.assert_called_once_with({})


def test_list_all_content_returns_documents_without_id(repo, collection, video_document):
    """list_all returns every document with _id stripped."""
    image = {"id": "i1", "media_type": "image", "title": "Pic"}
    collection.find.return_value = [with_id(video_document, "m1"), with_id(image, "m2")]
    result = repo.list_all()
    assert result == [video_document, image]
    assert all("_id" not in doc for doc in result)


def test_list_all_content_empty(repo, collection):
    """list_all returns an empty list for an empty collection."""
    collection.find.return_value = []
    assert repo.list_all() == []


def test_update_content(repo, collection):
    """update calls update_one with the id filter and a $set of the updates."""
    collection.update_one.return_value = Mock(matched_count=1, modified_count=1)
    result = repo.update("v1", {"title": "New"})
    collection.update_one.assert_called_once_with({"id": "v1"}, {"$set": {"title": "New"}})
    assert result == 1


def test_update_content_same_values_counts_as_found(repo, collection):
    """update returns matched_count, so setting the same values still returns 1."""
    collection.update_one.return_value = Mock(matched_count=1, modified_count=0)
    assert repo.update("v1", {"title": "Intro"}) == 1


def test_update_content_unknown_id(repo, collection):
    """update returns 0 for an unknown id."""
    collection.update_one.return_value = Mock(matched_count=0, modified_count=0)
    assert repo.update("missing", {"title": "New"}) == 0


def test_delete_content(repo, collection):
    """delete calls delete_one by id and returns deleted_count."""
    collection.delete_one.return_value = Mock(deleted_count=1)
    result = repo.delete("v1")
    collection.delete_one.assert_called_once_with({"id": "v1"})
    assert result == 1


def test_delete_content_unknown_id(repo, collection):
    """delete returns 0 for an unknown id."""
    collection.delete_one.return_value = Mock(deleted_count=0)
    assert repo.delete("missing") == 0
