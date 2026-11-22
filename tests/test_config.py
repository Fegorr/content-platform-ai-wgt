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


def test_get_jwt_secret_key_returns_env_value(monkeypatch):
    """get_jwt_secret_key returns the JWT_SECRET_KEY environment value."""
    from src.config import get_jwt_secret_key

    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
    assert get_jwt_secret_key() == "a" * 32


def test_get_jwt_secret_key_reads_at_call_time(monkeypatch):
    """A changed JWT_SECRET_KEY is picked up by the next call."""
    from src.config import get_jwt_secret_key

    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
    assert get_jwt_secret_key() == "a" * 32
    monkeypatch.setenv("JWT_SECRET_KEY", "b" * 32)
    assert get_jwt_secret_key() == "b" * 32


def test_get_jwt_secret_key_missing(monkeypatch):
    """A missing JWT_SECRET_KEY raises RuntimeError."""
    from src.config import get_jwt_secret_key

    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not set"):
        get_jwt_secret_key()


def test_get_jwt_secret_key_empty(monkeypatch):
    """An empty JWT_SECRET_KEY raises RuntimeError."""
    from src.config import get_jwt_secret_key

    monkeypatch.setenv("JWT_SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not set"):
        get_jwt_secret_key()


def test_import_config_without_jwt_secret_key(monkeypatch):
    """Importing config works without JWT_SECRET_KEY set."""
    import src.config

    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    importlib.reload(src.config)
