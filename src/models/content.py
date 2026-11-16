from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, StringConstraints


class ContentStatus(str, Enum):
    """Whether a content item is visible to everyone or only its author."""

    DRAFT = "draft"
    PUBLISHED = "published"


class MediaType(str, Enum):
    """The four kinds of content the platform stores."""

    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class BaseContent(BaseModel, ABC):
    """Abstract base for every content item."""

    id: UUID = Field(default_factory=uuid4)
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    author_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ContentStatus = ContentStatus.DRAFT
    media_type: MediaType

    def publish(self) -> None:
        """Set the status to published."""
        self.status = ContentStatus.PUBLISHED

    def unpublish(self) -> None:
        """Set the status back to draft."""
        self.status = ContentStatus.DRAFT

    @abstractmethod
    def get_preview(self) -> str:
        """Return a short text preview, calculated on every call."""


class MediaFile(BaseContent, ABC):
    """Abstract content that points to a file by url."""

    url: str = Field(min_length=1)
    file_name: str = Field(min_length=1)


class VideoFile(MediaFile):
    """A video with duration, resolution and frame rate."""

    media_type: Literal[MediaType.VIDEO] = MediaType.VIDEO
    duration: int = Field(gt=0)
    resolution: str = Field(pattern=r"^[0-9]+x[0-9]+$")
    frame_rate: float = Field(gt=0, allow_inf_nan=False)

    def get_preview(self) -> str:
        return (
            f"Duration: {self.duration} seconds\n"
            f"Resolution: {self.resolution}\n"
            f"Frame rate: {self.frame_rate}"
        )


class AudioFile(MediaFile):
    """An audio file with a duration."""

    media_type: Literal[MediaType.AUDIO] = MediaType.AUDIO
    duration: int = Field(gt=0)

    def get_preview(self) -> str:
        return f"Duration: {self.duration} seconds"


class ImageFile(MediaFile):
    """An image with a WIDTHxHEIGHT resolution."""

    media_type: Literal[MediaType.IMAGE] = MediaType.IMAGE
    resolution: str = Field(pattern=r"^[0-9]+x[0-9]+$")

    def get_preview(self) -> str:
        return f"Resolution: {self.resolution}"

    def compress(self, percentage: float) -> str:
        """Return the resolution after compressing; the model is unchanged."""
        if percentage <= 0 or percentage >= 100:
            raise ValueError("Invalid compression size")
        width, height = self.resolution.split("x")
        return f"{int(int(width) * (100 - percentage) / 100)}x{int(int(height) * (100 - percentage) / 100)}"


class DocumentFile(MediaFile):
    """A text document with a body."""

    media_type: Literal[MediaType.DOCUMENT] = MediaType.DOCUMENT
    body: str = Field(min_length=1)

    def get_preview(self) -> str:
        return self.body[:100]

    def append_text(self, text: str) -> str:
        """Append text to the body and return the new body."""
        if text == "":
            raise ValueError("No changes have been made")
        self.body = self.body + text
        return self.body
