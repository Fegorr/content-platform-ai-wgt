import os

# Must run before importing the app: tests never read .env.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-at-least-32-characters-long"

import pytest

from src.auth.hashing import hash_password
from src.auth.jwt import create_access_token
from src.main import app
from src.utils.dependencies import get_user_repository

TEST_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
OTHER_USER_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
ADMIN_USER_ID = "c3d4e5f6-a7b8-9012-cdef-123456789012"


class FakeUserRepository:
    """In-memory stand-in with the same method names as UserRepository."""

    def __init__(self, users=None):
        self.users = {u["id"]: dict(u) for u in (users or [])}

    def create(self, document: dict) -> str:
        self.users[document["id"]] = dict(document)
        return document["id"]

    def get_by_id(self, user_id: str):
        user = self.users.get(user_id)
        return dict(user) if user else None

    def get_by_email(self, email: str):
        for user in self.users.values():
            if user["email"] == email:
                return dict(user)
        return None

    def update(self, user_id: str, updates: dict) -> int:
        if user_id not in self.users:
            return 0
        self.users[user_id].update(updates)
        return 1


def make_user(user_id, name, email, password, role="user"):
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "hashed_password": hash_password(password),
        "role": role,
    }


def headers_for(user):
    return {"Authorization": f"Bearer {create_access_token(user['id'])}"}


# Hashed once per session: argon2 is slow and the autouse fixture runs for every test.
_TEST_USER = make_user(TEST_USER_ID, "Louise", "louise@test.com", "louise_pass_1")
_OTHER_USER = make_user(OTHER_USER_ID, "Sylvie", "sylvie@test.com", "sylvie_pass_1")
_ADMIN_USER = make_user(ADMIN_USER_ID, "Ada", "ada@test.com", "ada_pass_123", role="admin")


@pytest.fixture
def test_user():
    return dict(_TEST_USER)


@pytest.fixture
def other_user():
    return dict(_OTHER_USER)


@pytest.fixture
def admin_user():
    return dict(_ADMIN_USER)


@pytest.fixture(autouse=True)
def fake_user_repository(test_user, other_user, admin_user):
    """A fresh fake user repository per test, so tests never share data."""
    user_repo = FakeUserRepository([test_user, other_user, admin_user])
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    yield user_repo
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    return headers_for(test_user)


@pytest.fixture
def other_auth_headers(other_user):
    return headers_for(other_user)


@pytest.fixture
def admin_auth_headers(admin_user):
    return headers_for(admin_user)
