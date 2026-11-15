import importlib
from unittest.mock import MagicMock, patch

import certifi
import pytest
from pymongo.server_api import ServerApi


@pytest.fixture(autouse=True)
def clear_client_cache():
    """Clear the get_client cache before and after each test."""
    from src.db import database

    database.get_client.cache_clear()
    yield
    database.get_client.cache_clear()


def test_import_database_creates_no_client():
    """Importing src.db.database does not create a MongoClient."""
    from src.db import database

    with patch("pymongo.MongoClient") as mock_client:
        importlib.reload(database)
        mock_client.assert_not_called()
    importlib.reload(database)


def test_get_client_arguments(monkeypatch):
    """get_client builds MongoClient with the URI, ServerApi 1 and certifi CA file."""
    from src.db import database

    monkeypatch.setenv("MONGODB_URI", "mongodb://example")
    with patch("src.db.database.MongoClient") as mock_client:
        database.get_client()
    mock_client.assert_called_once()
    args, kwargs = mock_client.call_args
    assert args == ("mongodb://example",)
    assert set(kwargs) == {"server_api", "tlsCAFile"}
    assert kwargs["tlsCAFile"] == certifi.where()
    assert isinstance(kwargs["server_api"], ServerApi)
    assert kwargs["server_api"].version == "1"


def test_get_client_is_cached(monkeypatch):
    """Two get_client calls return the same client and create it once."""
    from src.db import database

    monkeypatch.setenv("MONGODB_URI", "mongodb://example")
    with patch("src.db.database.MongoClient") as mock_client:
        first = database.get_client()
        second = database.get_client()
    assert first is second
    mock_client.assert_called_once()


def test_get_client_missing_uri(monkeypatch):
    """get_client without MONGODB_URI raises RuntimeError and creates no client."""
    from src.db import database

    monkeypatch.delenv("MONGODB_URI", raising=False)
    with patch("src.db.database.MongoClient") as mock_client:
        with pytest.raises(RuntimeError, match="MONGODB_URI is not set"):
            database.get_client()
    mock_client.assert_not_called()


def test_get_content_collection_uses_content_platform_content():
    """get_content_collection returns the content collection of the content-platform database."""
    from src.db import database

    client = MagicMock()
    with patch("src.db.database.get_client", return_value=client):
        result = database.get_content_collection()
    assert result is client["content-platform"]["content"]
