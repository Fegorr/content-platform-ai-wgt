import inspect
from unittest.mock import Mock, patch

import pytest

from src.db.user_repository import UserRepository


@pytest.fixture
def collection():
    """A Mock stand-in for the Mongo users collection."""
    return Mock()


@pytest.fixture
def repo(collection):
    """A UserRepository over the Mock collection."""
    return UserRepository(collection)


@pytest.fixture
def user_document():
    """A stored user document without _id."""
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Louise",
        "email": "louise@test.com",
        "hashed_password": "hashed-secret",
        "role": "user",
    }


def with_id(document, mongo_id="mongo-1"):
    """Return a copy of the document with a Mongo _id added."""
    return {**document, "_id": mongo_id}


def test_create_user_repository_takes_collection(collection):
    """The repository is built from a collection and nothing else."""
    UserRepository(collection)
    assert list(inspect.signature(UserRepository.__init__).parameters) == ["self", "collection"]


def test_use_user_repository_never_calls_get_client(collection, user_document):
    """Building the repository and calling its methods never calls get_client."""
    collection.find_one.return_value = with_id(user_document)
    collection.update_one.return_value = Mock(matched_count=1, modified_count=1)
    with patch("src.db.database.get_client") as client_in_database, patch(
        "src.db.user_repository.get_client", create=True
    ) as client_in_repository:
        repo = UserRepository(collection)
        repo.create(user_document)
        repo.get_by_id("u1")
        repo.get_by_email("louise@test.com")
        repo.update("u1", {"name": "New"})
    client_in_database.assert_not_called()
    client_in_repository.assert_not_called()


def test_create_user_inserts_document(repo, collection, user_document):
    """create calls insert_one once with a dict equal to the document."""
    repo.create(user_document)
    collection.insert_one.assert_called_once_with(user_document)


def test_create_user_returns_document_id(repo, collection, user_document):
    """create returns the document id, not Mongo's inserted_id."""
    collection.insert_one.return_value.inserted_id = "mongo-object-id"
    assert repo.create(user_document) == user_document["id"]


def test_create_user_does_not_change_caller_dict(repo, collection, user_document):
    """create leaves the caller's dict without _id even if insert_one adds it."""
    collection.insert_one.side_effect = lambda doc: doc.update({"_id": "mongo-1"})
    original = dict(user_document)
    repo.create(user_document)
    assert "_id" not in user_document
    assert user_document == original
    collection.insert_one.assert_called_once()


def test_get_user_by_id(repo, collection, user_document):
    """get_by_id queries by the id field and returns the user."""
    collection.find_one.return_value = with_id(user_document)
    result = repo.get_by_id(user_document["id"])
    collection.find_one.assert_called_once_with({"id": user_document["id"]})
    assert result == user_document


def test_get_user_by_id_strips_underscore_id(repo, collection, user_document):
    """get_by_id removes _id from the returned user."""
    collection.find_one.return_value = with_id(user_document)
    assert "_id" not in repo.get_by_id(user_document["id"])


def test_get_user_by_id_not_found(repo, collection):
    """get_by_id returns None when nothing is found."""
    collection.find_one.return_value = None
    assert repo.get_by_id("missing") is None
    collection.find_one.assert_called_once_with({"id": "missing"})


def test_get_user_by_email(repo, collection, user_document):
    """get_by_email queries by the email field and returns the user."""
    collection.find_one.return_value = with_id(user_document)
    result = repo.get_by_email("louise@test.com")
    collection.find_one.assert_called_once_with({"email": "louise@test.com"})
    assert result == user_document


def test_get_user_by_email_keeps_email_as_given(repo, collection):
    """get_by_email does not lowercase the email; that is the service's job."""
    collection.find_one.return_value = None
    repo.get_by_email("Louise@Test.com")
    collection.find_one.assert_called_once_with({"email": "Louise@Test.com"})


def test_get_user_by_email_strips_underscore_id(repo, collection, user_document):
    """get_by_email removes _id from the returned user."""
    collection.find_one.return_value = with_id(user_document)
    assert "_id" not in repo.get_by_email("louise@test.com")


def test_get_user_by_email_not_found(repo, collection):
    """get_by_email returns None when nothing is found."""
    collection.find_one.return_value = None
    assert repo.get_by_email("nobody@test.com") is None


def test_get_user_by_id_returns_new_dict(repo, collection, user_document):
    """get_by_id returns a new dict and leaves the stored one with its _id."""
    stored = with_id(user_document)
    collection.find_one.return_value = stored
    result = repo.get_by_id(user_document["id"])
    assert result is not stored
    assert "_id" not in result
    assert stored["_id"] == "mongo-1"


def test_get_user_by_email_returns_new_dict(repo, collection, user_document):
    """get_by_email returns a new dict and leaves the stored one with its _id."""
    stored = with_id(user_document)
    collection.find_one.return_value = stored
    result = repo.get_by_email("louise@test.com")
    assert result is not stored
    assert "_id" not in result
    assert stored["_id"] == "mongo-1"


def test_update_user(repo, collection):
    """update calls update_one with the id filter and a $set of the updates."""
    collection.update_one.return_value = Mock(matched_count=1, modified_count=1)
    result = repo.update("u1", {"name": "New"})
    collection.update_one.assert_called_once_with({"id": "u1"}, {"$set": {"name": "New"}})
    assert result == 1


def test_update_user_same_values_counts_as_found(repo, collection):
    """update returns matched_count, so setting the same values still returns 1."""
    collection.update_one.return_value = Mock(matched_count=1, modified_count=0)
    assert repo.update("u1", {"name": "Louise"}) == 1


def test_update_user_unknown_id(repo, collection):
    """update returns 0 for an unknown id."""
    collection.update_one.return_value = Mock(matched_count=0, modified_count=0)
    assert repo.update("missing", {"name": "New"}) == 0


def test_get_user_by_id_keeps_hashed_password(repo, collection, user_document):
    """get_by_id returns hashed_password, which login needs."""
    collection.find_one.return_value = with_id(user_document)
    assert repo.get_by_id(user_document["id"])["hashed_password"] == "hashed-secret"


def test_get_user_by_email_keeps_hashed_password(repo, collection, user_document):
    """get_by_email returns hashed_password, which login needs."""
    collection.find_one.return_value = with_id(user_document)
    assert repo.get_by_email("louise@test.com")["hashed_password"] == "hashed-secret"
