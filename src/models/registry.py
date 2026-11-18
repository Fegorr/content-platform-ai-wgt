from types import MappingProxyType

from src.models.content import AudioFile, DocumentFile, ImageFile, MediaType, VideoFile

CONTENT_TYPES = MappingProxyType(
    {
        MediaType.VIDEO: VideoFile,
        MediaType.IMAGE: ImageFile,
        MediaType.AUDIO: AudioFile,
        MediaType.DOCUMENT: DocumentFile,
    }
)
