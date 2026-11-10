import importlib

import pytest


def test_get_mongodb_uri_returns_env_value(monkeypatch):
    """get_mongodb_uri returns the MONGODB_URI environment value."""
    from src.config import get_mongodb_uri

    monkeypatch.setenv("MONGODB_URI", "mongodb://first")
    assert get_mongodb_uri() == "mongodb://first"


def test_get_mongodb_uri_reads_at_call_time(monkeypatch):
    """A changed MONGODB_URI is picked up by the next call."""
    from src.config import get_mongodb_uri

    monkeypatch.setenv("MONGODB_URI", "mongodb://first")
    assert get_mongodb_uri() == "mongodb://first"
    monkeypatch.setenv("MONGODB_URI", "mongodb://second")
    assert get_mongodb_uri() == "mongodb://second"


def test_get_mongodb_uri_missing(monkeypatch):
    """A missing MONGODB_URI raises RuntimeError."""
    from src.config import get_mongodb_uri

    monkeypatch.delenv("MONGODB_URI", raising=False)
    with pytest.raises(RuntimeError, match="MONGODB_URI is not set"):
        get_mongodb_uri()


def test_import_config_does_not_read_environment(monkeypatch):
    """Importing config works without MONGODB_URI, so nothing is read at import."""
    import src.config

    monkeypatch.delenv("MONGODB_URI", raising=False)
    importlib.reload(src.config)


def test_config_does_not_use_dotenv():
    """config.py does not import dotenv or load_dotenv."""
    import src.config

    assert not hasattr(src.config, "load_dotenv")
    assert not hasattr(src.config, "dotenv")
