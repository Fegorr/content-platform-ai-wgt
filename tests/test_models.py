import os
import subprocess
import sys
from datetime import timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.models.content import (
    AudioFile,
    BaseContent,
    ContentStatus,
    DocumentFile,
    ImageFile,
    MediaFile,
    MediaType,
    VideoFile,
)
from src.models.registry import CONTENT_TYPES
from src.models.user import User, UserRole

AUTHOR_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def video_data():
    """Valid kwargs for a VideoFile."""
    return {
        "title": "Intro",
        "author_id": AUTHOR_ID,
        "media_type": "video",
        "url": "https://example.com/v.mp4",
        "file_name": "v.mp4",
        "duration": 72,
        "resolution": "1920x1080",
        "frame_rate": 30.0,
    }


@pytest.fixture
def audio_data():
    """Valid kwargs for an AudioFile."""
    return {
        "title": "Song",
        "author_id": AUTHOR_ID,
        "media_type": "audio",
        "url": "https://example.com/a.mp3",
        "file_name": "a.mp3",
        "duration": 180,
    }


@pytest.fixture
def image_data():
    """Valid kwargs for an ImageFile."""
    return {
        "title": "Photo",
        "author_id": AUTHOR_ID,
        "media_type": "image",
        "url": "https://example.com/i.png",
        "file_name": "i.png",
        "resolution": "1200x2050",
    }


@pytest.fixture
def document_data():
    """Valid kwargs for a DocumentFile."""
    return {
        "title": "Notes",
        "author_id": AUTHOR_ID,
        "media_type": "document",
        "url": "https://example.com/d.txt",
        "file_name": "d.txt",
        "body": "Hello world",
    }


@pytest.fixture
def user_data():
    """Valid kwargs for a User."""
    return {
        "name": "Louise",
        "email": "louise@test.com",
        "hashed_password": "hashed-secret",
    }


# Rules 1-3: enums


def test_create_content_status_values():
    """ContentStatus has exactly draft and published."""
    assert issubclass(ContentStatus, str)
    assert {s.value for s in ContentStatus} == {"draft", "published"}


def test_create_media_type_values():
    """MediaType has exactly video, image, audio and document."""
    assert issubclass(MediaType, str)
    assert {m.value for m in MediaType} == {"video", "image", "audio", "document"}


def test_create_user_role_values():
    """UserRole has exactly user and admin."""
    assert issubclass(UserRole, str)
    assert {r.value for r in UserRole} == {"user", "admin"}


# Rules 4-9: BaseContent behaviour (through a concrete type)


def test_create_video_default_id_and_created_at(video_data):
    """A valid item gets a UUID id and a timezone-aware UTC created_at."""
    video = VideoFile(**video_data)
    assert isinstance(video.id, UUID)
    assert video.created_at.tzinfo is not None
    assert video.created_at.utcoffset() == timedelta(0)


def test_create_video_unique_ids(video_data):
    """Two items get different ids."""
    assert VideoFile(**video_data).id != VideoFile(**video_data).id


def test_create_video_default_status_draft(video_data):
    """A new item has status draft."""
    assert VideoFile(**video_data).status == ContentStatus.DRAFT


def test_create_video_missing_title(video_data):
    """A missing title raises ValidationError."""
    del video_data["title"]
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


@pytest.mark.parametrize("title", ["", "   "])
def test_create_video_empty_title(video_data, title):
    """An empty or whitespace-only title raises ValidationError."""
    video_data["title"] = title
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_strips_title(video_data):
    """Whitespace around the title is stripped."""
    video_data["title"] = "  Intro  "
    assert VideoFile(**video_data).title == "Intro"


def test_create_video_missing_author_id(video_data):
    """A missing author_id raises ValidationError."""
    del video_data["author_id"]
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_author_id_not_uuid(video_data):
    """An author_id that is not a UUID raises ValidationError."""
    video_data["author_id"] = "not-a-uuid"
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_media_type_text(video_data):
    """media_type 'text' raises ValidationError."""
    video_data["media_type"] = "text"
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_invalid_status(video_data):
    """An invalid status raises ValidationError."""
    video_data["status"] = "random"
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


# Rule 10: abstract classes


def test_create_base_content_abstract():
    """BaseContent cannot be instantiated."""
    with pytest.raises(TypeError, match="abstract"):
        BaseContent(title="x", author_id=AUTHOR_ID, media_type="video")


def test_create_media_file_abstract():
    """MediaFile cannot be instantiated."""
    with pytest.raises(TypeError, match="abstract"):
        MediaFile(
            title="x",
            author_id=AUTHOR_ID,
            media_type="video",
            url="https://example.com/x",
            file_name="x",
        )


# Rule 11: publish / unpublish


def test_publish_video_sets_status_published(video_data):
    """publish() sets status to published."""
    video = VideoFile(**video_data)
    video.publish()
    assert video.status == ContentStatus.PUBLISHED


def test_unpublish_video_sets_status_draft(video_data):
    """unpublish() sets status back to draft."""
    video = VideoFile(**video_data)
    video.publish()
    video.unpublish()
    assert video.status == ContentStatus.DRAFT


# Rule 12: MediaFile url / file_name on every concrete type


@pytest.fixture(params=["video_data", "audio_data", "image_data", "document_data"])
def media_case(request):
    """Pair of (class, valid kwargs) for each concrete type."""
    classes = {
        "video_data": VideoFile,
        "audio_data": AudioFile,
        "image_data": ImageFile,
        "document_data": DocumentFile,
    }
    return classes[request.param], request.getfixturevalue(request.param)


@pytest.mark.parametrize("field", ["url", "file_name"])
def test_create_media_missing_field(media_case, field):
    """A missing url or file_name raises ValidationError on every type."""
    cls, data = media_case
    del data[field]
    with pytest.raises(ValidationError):
        cls(**data)


@pytest.mark.parametrize("field", ["url", "file_name"])
def test_create_media_empty_field(media_case, field):
    """An empty url or file_name raises ValidationError on every type."""
    cls, data = media_case
    data[field] = ""
    with pytest.raises(ValidationError):
        cls(**data)


@pytest.mark.parametrize(
    "cls, fixture_name, expected",
    [
        (VideoFile, "video_data", MediaType.VIDEO),
        (ImageFile, "image_data", MediaType.IMAGE),
        (AudioFile, "audio_data", MediaType.AUDIO),
        (DocumentFile, "document_data", MediaType.DOCUMENT),
    ],
)
def test_create_content_default_media_type(request, cls, fixture_name, expected):
    """Creating a content class without media_type sets its own media_type."""
    data = request.getfixturevalue(fixture_name)
    del data["media_type"]
    assert cls(**data).media_type == expected


@pytest.mark.parametrize(
    "cls, fixture_name, wrong",
    [
        (VideoFile, "video_data", "audio"),
        (ImageFile, "image_data", "video"),
        (AudioFile, "audio_data", "document"),
        (DocumentFile, "document_data", "image"),
    ],
)
def test_create_content_wrong_media_type(request, cls, fixture_name, wrong):
    """Creating a content class with another valid media_type raises ValidationError."""
    data = request.getfixturevalue(fixture_name)
    data["media_type"] = wrong
    with pytest.raises(ValidationError):
        cls(**data)


# Rules 13-14: VideoFile


def test_create_video_valid(video_data):
    """A valid VideoFile keeps its fields."""
    video = VideoFile(**video_data)
    assert video.duration == 72
    assert video.resolution == "1920x1080"
    assert video.frame_rate == 30.0


@pytest.mark.parametrize("duration", [0, -1])
def test_create_video_invalid_duration(video_data, duration):
    """A video duration of zero or less raises ValidationError."""
    video_data["duration"] = duration
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


@pytest.mark.parametrize("resolution", ["1920", "1920x", "axb"])
def test_create_video_invalid_resolution(video_data, resolution):
    """A malformed video resolution raises ValidationError."""
    video_data["resolution"] = resolution
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_resolution_non_ascii_digits(video_data):
    """A video resolution written with non-ASCII digits raises ValidationError."""
    video_data["resolution"] = "١٩٢٠x١٠٨٠"
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_create_video_resolution_with_spaces(video_data):
    """A video resolution with spaces around it raises ValidationError."""
    video_data["resolution"] = " 1920x1080 "
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


@pytest.mark.parametrize("frame_rate", [0, -30.0])
def test_create_video_invalid_frame_rate(video_data, frame_rate):
    """A video frame_rate of zero or less raises ValidationError."""
    video_data["frame_rate"] = frame_rate
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


@pytest.mark.parametrize("frame_rate", [float("inf"), float("nan")])
def test_create_video_frame_rate_not_finite(video_data, frame_rate):
    """A video frame_rate of inf or nan raises ValidationError."""
    video_data["frame_rate"] = frame_rate
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


@pytest.mark.parametrize("field", ["duration", "resolution", "frame_rate"])
def test_create_video_missing_field(video_data, field):
    """A missing duration, resolution or frame_rate raises ValidationError."""
    del video_data[field]
    with pytest.raises(ValidationError):
        VideoFile(**video_data)


def test_get_preview_video(video_data):
    """Video preview shows duration, resolution and frame rate."""
    assert VideoFile(**video_data).get_preview() == (
        "Duration: 72 seconds\nResolution: 1920x1080\nFrame rate: 30.0"
    )


# Rule 15: AudioFile


@pytest.mark.parametrize("duration", [0, -1])
def test_create_audio_invalid_duration(audio_data, duration):
    """An audio duration of zero or less raises ValidationError."""
    audio_data["duration"] = duration
    with pytest.raises(ValidationError):
        AudioFile(**audio_data)


def test_create_audio_missing_duration(audio_data):
    """A missing audio duration raises ValidationError."""
    del audio_data["duration"]
    with pytest.raises(ValidationError):
        AudioFile(**audio_data)


def test_get_preview_audio(audio_data):
    """Audio preview shows the duration."""
    assert AudioFile(**audio_data).get_preview() == "Duration: 180 seconds"


# Rule 16: ImageFile


@pytest.mark.parametrize("resolution", ["1920", "1920x", "axb"])
def test_create_image_invalid_resolution(image_data, resolution):
    """A malformed image resolution raises ValidationError."""
    image_data["resolution"] = resolution
    with pytest.raises(ValidationError):
        ImageFile(**image_data)


def test_create_image_resolution_non_ascii_digits(image_data):
    """An image resolution written with non-ASCII digits raises ValidationError."""
    image_data["resolution"] = "١٩٢٠x١٠٨٠"
    with pytest.raises(ValidationError):
        ImageFile(**image_data)


def test_create_image_resolution_with_spaces(image_data):
    """An image resolution with spaces around it raises ValidationError."""
    image_data["resolution"] = " 1920x1080 "
    with pytest.raises(ValidationError):
        ImageFile(**image_data)


def test_create_image_missing_resolution(image_data):
    """A missing image resolution raises ValidationError."""
    del image_data["resolution"]
    with pytest.raises(ValidationError):
        ImageFile(**image_data)


def test_get_preview_image(image_data):
    """Image preview shows the resolution."""
    assert ImageFile(**image_data).get_preview() == "Resolution: 1200x2050"


# Rule 17: DocumentFile


def test_create_document_empty_body(document_data):
    """An empty document body raises ValidationError."""
    document_data["body"] = ""
    with pytest.raises(ValidationError):
        DocumentFile(**document_data)


def test_create_document_missing_body(document_data):
    """A missing document body raises ValidationError."""
    del document_data["body"]
    with pytest.raises(ValidationError):
        DocumentFile(**document_data)


def test_create_document_keeps_body_whitespace(document_data):
    """A document body keeps its leading spaces and trailing newline."""
    document_data["body"] = "  indented text\n"
    assert DocumentFile(**document_data).body == "  indented text\n"


def test_get_preview_document_long_body(document_data):
    """Document preview is the first 100 characters of a long body."""
    document_data["body"] = "a" * 100 + "b" * 50
    preview = DocumentFile(**document_data).get_preview()
    assert preview == "a" * 100
    assert len(preview) == 100


def test_get_preview_document_short_body(document_data):
    """Document preview is the whole body when it is short."""
    assert DocumentFile(**document_data).get_preview() == "Hello world"


# Rule 18: ImageFile.compress


def test_compress_image(image_data):
    """Compressing 1200x2050 by 50 percent returns 600x1025."""
    assert ImageFile(**image_data).compress(50) == "600x1025"


def test_compress_image_rounds_down(image_data):
    """Compressing 1200x2050 by 33 percent returns 804x1373."""
    assert ImageFile(**{**image_data, "resolution": "1200x2050"}).compress(33) == "804x1373"


def test_compress_image_keeps_resolution(image_data):
    """compress() does not change the model's resolution."""
    image = ImageFile(**image_data)
    image.compress(50)
    assert image.resolution == "1200x2050"


@pytest.mark.parametrize("percentage", [0, -5, 100, 150])
def test_compress_image_invalid_percentage(image_data, percentage):
    """A percentage of 0 or less, or 100 or more, raises ValueError."""
    with pytest.raises(ValueError, match="Invalid compression size"):
        ImageFile(**image_data).compress(percentage)


# Rule 19: DocumentFile.append_text


def test_append_text_document(document_data):
    """append_text() adds the text to body and returns the new body."""
    document = DocumentFile(**document_data)
    result = document.append_text("!!")
    assert result == "Hello world!!"
    assert document.body == "Hello world!!"


def test_append_text_document_empty_text(document_data):
    """append_text('') raises ValueError and leaves body unchanged."""
    document = DocumentFile(**document_data)
    with pytest.raises(ValueError, match="No changes have been made"):
        document.append_text("")
    assert document.body == "Hello world"


# Rule 20: JSON dump shape


def test_dump_video_json_shape(video_data):
    """model_dump(mode='json') gives string ids and the stored-document keys."""
    dumped = VideoFile(**video_data).model_dump(mode="json")
    assert set(dumped) == {
        "id",
        "title",
        "author_id",
        "created_at",
        "status",
        "media_type",
        "url",
        "file_name",
        "duration",
        "resolution",
        "frame_rate",
    }
    assert isinstance(dumped["id"], str)
    assert dumped["author_id"] == AUTHOR_ID
    assert isinstance(dumped["created_at"], str)
    assert dumped["status"] == "draft"
    assert dumped["media_type"] == "video"
    assert dumped["frame_rate"] == 30.0


def test_dump_video_has_no_computed_fields(video_data):
    """The dump has no preview, can_edit or can_delete."""
    dumped = VideoFile(**video_data).model_dump(mode="json")
    assert not {"preview", "can_edit", "can_delete"} & set(dumped)


# Rule 21: registry


def test_get_registry_content_types():
    """CONTENT_TYPES maps each media_type string to its class."""
    assert CONTENT_TYPES == {
        "video": VideoFile,
        "image": ImageFile,
        "audio": AudioFile,
        "document": DocumentFile,
    }


@pytest.mark.parametrize("media_type", ["video", "image", "audio", "document"])
def test_create_registry_item_from_dump(
    media_type, video_data, image_data, audio_data, document_data
):
    """Each registered class rebuilds an equal item from its own JSON dump."""
    data = {
        "video": video_data,
        "image": image_data,
        "audio": audio_data,
        "document": document_data,
    }[media_type]
    cls = CONTENT_TYPES[media_type]
    original = cls(**data)
    rebuilt = cls(**original.model_dump(mode="json"))
    assert rebuilt == original


# Rules 22-25: User


def test_create_user_defaults(user_data):
    """A valid User gets a UUID id and role user."""
    user = User(**user_data)
    assert isinstance(user.id, UUID)
    assert user.role == UserRole.USER


def test_create_user_unique_ids(user_data):
    """Two users get different ids."""
    assert User(**user_data).id != User(**user_data).id


def test_create_user_admin_role(user_data):
    """role='admin' is accepted."""
    assert User(**user_data, role="admin").role == UserRole.ADMIN


def test_create_user_unknown_role(user_data):
    """An unknown role raises ValidationError."""
    with pytest.raises(ValidationError):
        User(**user_data, role="superuser")


@pytest.mark.parametrize("field", ["name", "hashed_password", "email"])
def test_create_user_missing_field(user_data, field):
    """A missing name, email or hashed_password raises ValidationError."""
    del user_data[field]
    with pytest.raises(ValidationError):
        User(**user_data)


@pytest.mark.parametrize("field", ["name", "hashed_password"])
def test_create_user_empty_field(user_data, field):
    """An empty name or hashed_password raises ValidationError."""
    user_data[field] = ""
    with pytest.raises(ValidationError):
        User(**user_data)


def test_create_user_invalid_email(user_data):
    """An invalid email raises ValidationError."""
    user_data["email"] = "not-an-email"
    with pytest.raises(ValidationError):
        User(**user_data)


def test_create_user_lowercases_email(user_data):
    """The model lowercases the email."""
    user_data["email"] = "Louise@Test.com"
    assert User(**user_data).email == "louise@test.com"


# Rule 26: purity


def test_import_models_without_database_or_http():
    """Importing the model modules does not load pymongo or an HTTP client."""
    code = (
        "import sys\n"
        "import src.models.content, src.models.user, src.models.registry\n"
        "bad = [m for m in ('pymongo', 'httpx', 'requests', 'fastapi')"
        " if m in sys.modules]\n"
        "assert not bad, bad\n"
    )
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
