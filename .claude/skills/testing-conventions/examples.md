# Example: router tests for videos

Copy the patterns, not the exact values. The other content routers follow the same shape.

## tests/conftest.py (the shared stand-ins)

```python
import os

# Must run before importing the app: tests never read .env
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

import pytest
from src.main import app
from src.auth.hashing import hash_password
from src.auth.jwt import create_access_token
from src.utils.dependencies import (
    get_content_repository,
    get_user_repository,
    get_token_blocklist_repository,
)

TEST_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
OTHER_USER_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
ADMIN_USER_ID = "c3d4e5f6-a7b8-9012-cdef-123456789012"


class FakeContentRepository:
    def __init__(self):
        self.documents = {}

    def create(self, document: dict) -> str:
        self.documents[document["id"]] = dict(document)
        return document["id"]

    def get_by_id(self, content_id: str):
        item = self.documents.get(content_id)
        return dict(item) if item else None

    def list_visible(self, media_type: str, user_id: str) -> list:
        return [
            dict(d) for d in self.documents.values()
            if d["media_type"] == media_type
            and (d["status"] == "published" or d["author_id"] == user_id)
        ]

    def list_all(self) -> list:
        return [dict(d) for d in self.documents.values()]

    def update(self, content_id: str, updates: dict) -> int:
        if content_id not in self.documents:
            return 0
        self.documents[content_id].update(updates)
        return 1

    def delete(self, content_id: str) -> int:
        return 1 if self.documents.pop(content_id, None) else 0


class FakeUserRepository:
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


class FakeTokenBlocklistRepository:
    def __init__(self):
        self.revoked = {}

    def add(self, jti: str, expires_at) -> None:
        self.revoked[jti] = expires_at

    def is_revoked(self, jti: str) -> bool:
        return jti in self.revoked


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


@pytest.fixture
def test_user():
    return make_user(TEST_USER_ID, "Louise", "louise@test.com", "louise_pass_1")


@pytest.fixture
def other_user():
    return make_user(OTHER_USER_ID, "Sylvie", "sylvie@test.com", "sylvie_pass_1")


@pytest.fixture
def admin_user():
    return make_user(ADMIN_USER_ID, "Ada", "ada@test.com", "ada_pass_123", role="admin")


@pytest.fixture(autouse=True)
def fake_repositories(test_user, other_user, admin_user):
    """A fresh fake per test, so tests never share data."""
    content_repo = FakeContentRepository()
    user_repo = FakeUserRepository([test_user, other_user, admin_user])
    blocklist_repo = FakeTokenBlocklistRepository()
    app.dependency_overrides[get_content_repository] = lambda: content_repo
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_token_blocklist_repository] = lambda: blocklist_repo
    yield content_repo, user_repo, blocklist_repo
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
```

## tests/test_videos.py

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


@pytest.fixture
def video_data():
    """Valid create payload. No id, author_id, media_type, created_at or status: the server sets those."""
    return {
        "title": "Test Video",
        "url": "https://example.com/test_video.mp4",
        "file_name": "test_video.mp4",
        "duration": 120,
        "resolution": "1920x1080",
        "frame_rate": 30.0,
    }


@pytest.fixture
def image_data():
    return {
        "title": "Test Image",
        "url": "https://example.com/test_image.jpeg",
        "file_name": "test_image.jpeg",
        "resolution": "1200x2050",
    }


def create_video(video_data, auth_headers):
    return client.post("/videos", json=video_data, headers=auth_headers).json()["id"]


def create_published_video(video_data, auth_headers):
    video_id = create_video(video_data, auth_headers)
    client.patch(f"/videos/{video_id}", json={"status": "published"}, headers=auth_headers)
    return video_id


# ---------- POST ----------

def test_create_video(video_data, auth_headers, test_user):
    """Creating a valid video returns 201 with server-set fields."""
    response = client.post("/videos", json=video_data, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == video_data["title"]
    assert "id" in body
    assert body["status"] == "draft"
    assert body["media_type"] == "video"
    assert body["author_id"] == test_user["id"]
    assert body["preview"] == "Duration: 120 seconds\nResolution: 1920x1080\nFrame rate: 30.0"
    assert "_id" not in body


def test_create_video_ignores_server_fields(video_data, auth_headers, test_user):
    """media_type, author_id and status sent by the client are ignored."""
    video_data.update({"media_type": "audio", "author_id": "someone-else", "status": "published"})
    body = client.post("/videos", json=video_data, headers=auth_headers).json()
    assert body["media_type"] == "video"
    assert body["author_id"] == test_user["id"]
    assert body["status"] == "draft"


def test_create_video_missing_title(video_data, auth_headers):
    """Creating a video without a title returns 422."""
    del video_data["title"]
    response = client.post("/videos", json=video_data, headers=auth_headers)
    assert response.status_code == 422


def test_create_video_invalid_duration(video_data, auth_headers):
    """Creating a video with a negative duration returns 422."""
    video_data["duration"] = -10
    response = client.post("/videos", json=video_data, headers=auth_headers)
    assert response.status_code == 422


# ---------- GET one ----------

def test_get_video(video_data, auth_headers):
    """Getting an existing video returns 200 and its data."""
    video_id = create_video(video_data, auth_headers)
    response = client.get(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == video_data["title"]
    assert response.json()["can_edit"] is True
    assert response.json()["can_delete"] is True
    assert "_id" not in response.json()


def test_get_video_not_found(auth_headers):
    """Getting an unknown id returns 404."""
    response = client.get("/videos/non-existent-id", headers=auth_headers)
    assert response.status_code == 404


def test_get_video_wrong_type(image_data, auth_headers):
    """Getting an image's id from /videos returns 404."""
    image_id = client.post("/images", json=image_data, headers=auth_headers).json()["id"]
    response = client.get(f"/videos/{image_id}", headers=auth_headers)
    assert response.status_code == 404


# ---------- GET list ----------

def test_list_videos_only_videos(video_data, image_data, auth_headers):
    """Listing videos returns only videos, without Mongo's _id."""
    create_video(video_data, auth_headers)
    client.post("/images", json=image_data, headers=auth_headers)
    response = client.get("/videos", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert all(item["media_type"] == "video" for item in items)
    assert all("_id" not in item for item in items)


def test_list_videos_empty(auth_headers):
    """Listing videos when none exist returns an empty list."""
    response = client.get("/videos", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


# ---------- PATCH ----------

def test_update_video(video_data, auth_headers):
    """Updating a title returns 200 and keeps the other fields."""
    video_id = create_video(video_data, auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"title": "New Title"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Video updated"
    item = client.get(f"/videos/{video_id}", headers=auth_headers).json()
    assert item["title"] == "New Title"
    assert item["duration"] == video_data["duration"]


def test_update_video_refreshes_preview(video_data, auth_headers):
    """After changing the duration, the preview shows the new duration."""
    video_id = create_video(video_data, auth_headers)
    client.patch(f"/videos/{video_id}", json={"duration": 90}, headers=auth_headers)
    item = client.get(f"/videos/{video_id}", headers=auth_headers).json()
    assert item["preview"].startswith("Duration: 90 seconds")


def test_publish_video(video_data, auth_headers):
    """Setting status to published publishes the video."""
    video_id = create_video(video_data, auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"status": "published"}, headers=auth_headers)
    assert response.status_code == 200
    assert client.get(f"/videos/{video_id}", headers=auth_headers).json()["status"] == "published"


def test_update_video_not_found(auth_headers):
    """Updating an unknown id returns 404."""
    response = client.patch("/videos/non-existent-id", json={"title": "X"}, headers=auth_headers)
    assert response.status_code == 404


def test_update_video_invalid_duration(video_data, auth_headers):
    """Updating duration to 0 returns 422."""
    video_id = create_video(video_data, auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"duration": 0}, headers=auth_headers)
    assert response.status_code == 422


def test_update_video_invalid_status(video_data, auth_headers):
    """Updating status to an unknown value returns 422."""
    video_id = create_video(video_data, auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"status": "random"}, headers=auth_headers)
    assert response.status_code == 422


def test_update_video_empty_body(video_data, auth_headers):
    """An empty PATCH body returns 200 with 'No changes made'."""
    video_id = create_video(video_data, auth_headers)
    response = client.patch(f"/videos/{video_id}", json={}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "No changes made"


# ---------- DELETE ----------

def test_delete_video(video_data, auth_headers):
    """Deleting a video returns 200 and it can't be fetched afterwards."""
    video_id = create_video(video_data, auth_headers)
    response = client.delete(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Video deleted"
    assert client.get(f"/videos/{video_id}", headers=auth_headers).status_code == 404


def test_delete_video_not_found(auth_headers):
    """Deleting an unknown id returns 404."""
    response = client.delete("/videos/non-existent-id", headers=auth_headers)
    assert response.status_code == 404


# ---------- Ownership and draft privacy ----------

def test_get_video_other_users_draft(video_data, other_auth_headers, auth_headers):
    """Another user's draft is hidden: 404."""
    video_id = create_video(video_data, other_auth_headers)
    response = client.get(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 404


def test_get_video_other_users_published(video_data, other_auth_headers, auth_headers):
    """Another user's published video can be read."""
    video_id = create_published_video(video_data, other_auth_headers)
    response = client.get(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["can_edit"] is False
    assert response.json()["can_delete"] is False


def test_list_videos_hides_other_users_drafts(video_data, other_auth_headers, auth_headers):
    """The list shows my drafts and others' published videos, not others' drafts."""
    my_draft = create_video(video_data, auth_headers)
    their_published = create_published_video(video_data, other_auth_headers)
    their_draft = create_video(video_data, other_auth_headers)
    ids = [item["id"] for item in client.get("/videos", headers=auth_headers).json()]
    assert my_draft in ids
    assert their_published in ids
    assert their_draft not in ids


def test_update_video_other_users_published(video_data, other_auth_headers, auth_headers):
    """Changing another user's published video returns 403 and changes nothing."""
    video_id = create_published_video(video_data, other_auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"title": "Hacked"}, headers=auth_headers)
    assert response.status_code == 403
    item = client.get(f"/videos/{video_id}", headers=auth_headers).json()
    assert item["title"] == video_data["title"]


def test_update_video_other_users_draft(video_data, other_auth_headers, auth_headers):
    """Changing another user's draft returns 404."""
    video_id = create_video(video_data, other_auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"title": "X"}, headers=auth_headers)
    assert response.status_code == 404


def test_delete_video_other_users_published(video_data, other_auth_headers, auth_headers):
    """Deleting another user's published video returns 403 and it still exists."""
    video_id = create_published_video(video_data, other_auth_headers)
    response = client.delete(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 403
    assert client.get(f"/videos/{video_id}", headers=auth_headers).status_code == 200


def test_delete_video_other_users_draft(video_data, other_auth_headers, auth_headers):
    """Deleting another user's draft returns 404."""
    video_id = create_video(video_data, other_auth_headers)
    response = client.delete(f"/videos/{video_id}", headers=auth_headers)
    assert response.status_code == 404


# ---------- Admin ----------

def test_get_video_admin_reads_other_users_draft(video_data, other_auth_headers, admin_auth_headers):
    """An admin can read another user's draft."""
    video_id = create_video(video_data, other_auth_headers)
    response = client.get(f"/videos/{video_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["can_edit"] is False
    assert response.json()["can_delete"] is True


def test_update_video_admin_forbidden(video_data, other_auth_headers, admin_auth_headers):
    """An admin can't edit another user's video: 403, nothing changes."""
    video_id = create_published_video(video_data, other_auth_headers)
    response = client.patch(f"/videos/{video_id}", json={"title": "Admin edit"}, headers=admin_auth_headers)
    assert response.status_code == 403
    item = client.get(f"/videos/{video_id}", headers=admin_auth_headers).json()
    assert item["title"] == video_data["title"]


def test_delete_video_admin_deletes_other_users_video(video_data, other_auth_headers, admin_auth_headers):
    """An admin can delete another user's video."""
    video_id = create_published_video(video_data, other_auth_headers)
    response = client.delete(f"/videos/{video_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert client.get(f"/videos/{video_id}", headers=admin_auth_headers).status_code == 404


# ---------- Auth ----------

ROUTES = [
    ("POST", "/videos"),
    ("GET", "/videos"),
    ("GET", "/videos/some-id"),
    ("PATCH", "/videos/some-id"),
    ("DELETE", "/videos/some-id"),
]


@pytest.mark.parametrize("method,path", ROUTES)
def test_videos_without_token(method, path, video_data):
    """Every video route returns 401 without a token."""
    response = client.request(method, path, json=video_data)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ROUTES)
def test_videos_with_invalid_token(method, path, video_data):
    """Every video route returns 401 with a made-up token."""
    headers = {"Authorization": "Bearer not-a-real-token"}
    response = client.request(method, path, json=video_data, headers=headers)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ROUTES)
def test_videos_with_logged_out_token(method, path, video_data, auth_headers):
    """After logout, the same token gets 401 on every video route."""
    client.post("/logout", headers=auth_headers)
    response = client.request(method, path, json=video_data, headers=auth_headers)
    assert response.status_code == 401
```
