import importlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.auth import jwt as auth_jwt
from src.auth.jwt import create_access_token, decode_access_token

SECRET = "test-secret-key-at-least-32-characters-long"
OTHER_SECRET = "other-secret-key-at-least-32-characters-long"
USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    """Set the test secret for every test in this file."""
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)


def future(minutes=5):
    """Return a UTC time some minutes from now."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def test_token_constants():
    """The module constants are 30 minutes and HS256."""
    assert auth_jwt.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert auth_jwt.ALGORITHM == "HS256"


def test_create_access_token_payload_has_exact_keys():
    """The token payload has sub, jti and exp and nothing else."""
    token = create_access_token(USER_ID)
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert set(payload) == {"sub", "jti", "exp"}


def test_create_access_token_sub_is_user_id():
    """The sub claim is the user id."""
    payload = jwt.decode(create_access_token(USER_ID), SECRET, algorithms=["HS256"])
    assert payload["sub"] == USER_ID


def test_create_access_token_jti_is_uuid():
    """The jti claim is a UUID string."""
    payload = jwt.decode(create_access_token(USER_ID), SECRET, algorithms=["HS256"])
    assert isinstance(payload["jti"], str)
    uuid.UUID(payload["jti"])


def test_create_access_token_exp_is_30_minutes_from_now():
    """The exp claim is about 30 minutes from now (UTC)."""
    payload = jwt.decode(create_access_token(USER_ID), SECRET, algorithms=["HS256"])
    expected = datetime.now(timezone.utc) + timedelta(minutes=30)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert abs(exp - expected) < timedelta(seconds=10)


def test_create_access_token_two_tokens_have_different_jti():
    """Two tokens for the same user have different jti values."""
    first = decode_access_token(create_access_token(USER_ID))
    second = decode_access_token(create_access_token(USER_ID))
    assert first["jti"] != second["jti"]


def test_import_jwt_module_without_secret(monkeypatch):
    """Importing src.auth.jwt works without JWT_SECRET_KEY set."""
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    importlib.reload(auth_jwt)


def test_decode_access_token_valid():
    """A valid token decodes to its payload."""
    payload = decode_access_token(create_access_token(USER_ID))
    assert payload["sub"] == USER_ID
    assert set(payload) == {"sub", "jti", "exp"}


def test_decode_access_token_secret_changed(monkeypatch):
    """A token made under one secret decodes to None after the secret changes."""
    token = create_access_token(USER_ID)
    monkeypatch.setenv("JWT_SECRET_KEY", OTHER_SECRET)
    assert decode_access_token(token) is None


def test_decode_access_token_other_algorithm(monkeypatch):
    """A token signed with HS512 and the same secret returns None."""
    long_secret = "long-secret-key-for-hs512-" + "x" * 40
    monkeypatch.setenv("JWT_SECRET_KEY", long_secret)
    payload = {"sub": USER_ID, "jti": str(uuid.uuid4()), "exp": future()}
    token = jwt.encode(payload, long_secret, algorithm="HS512")
    assert decode_access_token(token) is None


def test_decode_access_token_expired():
    """An expired token returns None."""
    payload = {"sub": USER_ID, "jti": str(uuid.uuid4()), "exp": future(-5)}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    assert decode_access_token(token) is None


def test_decode_access_token_wrong_secret():
    """A token signed with another secret returns None."""
    payload = {"sub": USER_ID, "jti": str(uuid.uuid4()), "exp": future()}
    token = jwt.encode(payload, OTHER_SECRET, algorithm="HS256")
    assert decode_access_token(token) is None


def test_decode_access_token_malformed():
    """A malformed string returns None."""
    assert decode_access_token("not.a.token") is None


def test_decode_access_token_missing_sub():
    """A token without sub returns None."""
    payload = {"jti": str(uuid.uuid4()), "exp": future()}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    assert decode_access_token(token) is None


def test_decode_access_token_missing_jti():
    """A token without jti returns None."""
    payload = {"sub": USER_ID, "exp": future()}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    assert decode_access_token(token) is None


def test_decode_access_token_missing_exp():
    """A token without exp returns None."""
    payload = {"sub": USER_ID, "jti": str(uuid.uuid4())}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    assert decode_access_token(token) is None


@pytest.mark.parametrize("value", [None, ""])
def test_create_access_token_without_secret(monkeypatch, value):
    """A missing or empty secret makes create_access_token raise RuntimeError."""
    if value is None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET_KEY", value)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not set"):
        create_access_token(USER_ID)


@pytest.mark.parametrize("value", [None, ""])
def test_decode_access_token_without_secret(monkeypatch, value):
    """A missing or empty secret makes decode_access_token raise RuntimeError."""
    token = create_access_token(USER_ID)
    if value is None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET_KEY", value)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not set"):
        decode_access_token(token)
