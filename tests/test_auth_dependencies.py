import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, oauth2_scheme
from src.auth.jwt import ALGORITHM, create_access_token
from src.utils.dependencies import get_user_repository

COULD_NOT_VALIDATE = "Could not validate credentials"


@pytest.fixture
def client(fake_user_repository):
    """A client for a small app with one route that returns get_current_user."""
    small_app = FastAPI()

    @small_app.get("/whoami")
    def whoami(current_user: dict = Depends(get_current_user)):
        return current_user

    small_app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    return TestClient(small_app)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def encode(payload, secret):
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def assert_could_not_validate(response):
    assert response.status_code == 401
    assert response.json()["detail"] == COULD_NOT_VALIDATE
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_current_user(client, auth_headers, test_user):
    """A valid token returns the user with id, name, email and role."""
    response = client.get("/whoami", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": test_user["id"],
        "name": "Louise",
        "email": "louise@test.com",
        "role": "user",
    }


def test_get_current_user_has_no_hashed_password(client, auth_headers):
    """The returned user never includes hashed_password."""
    response = client.get("/whoami", headers=auth_headers)
    assert "hashed_password" not in response.json()


def test_get_current_user_without_header(client):
    """No Authorization header returns 401 'Not authenticated' with the Bearer header."""
    response = client.get("/whoami")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_current_user_malformed_token(client):
    """A malformed token returns 401 'Could not validate credentials'."""
    assert_could_not_validate(client.get("/whoami", headers=bearer("not-a-real-token")))


def test_get_current_user_other_secret(client, test_user):
    """A token signed with another secret returns 401."""
    token = encode(
        {
            "sub": test_user["id"],
            "jti": "some-jti",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        "another-secret-key-at-least-32-characters-long",
    )
    assert_could_not_validate(client.get("/whoami", headers=bearer(token)))


def test_get_current_user_expired_token(client, test_user):
    """An expired token returns 401."""
    token = encode(
        {
            "sub": test_user["id"],
            "jti": "some-jti",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        os.environ["JWT_SECRET_KEY"],
    )
    assert_could_not_validate(client.get("/whoami", headers=bearer(token)))


def test_get_current_user_unknown_user(client):
    """A valid token whose sub is not a known user returns 401."""
    token = create_access_token("00000000-0000-0000-0000-000000000000")
    assert_could_not_validate(client.get("/whoami", headers=bearer(token)))


def test_oauth2_scheme_points_at_login():
    """The OAuth2 scheme sends clients to the login route for a token."""
    assert oauth2_scheme.model.flows.password.tokenUrl == "login"
