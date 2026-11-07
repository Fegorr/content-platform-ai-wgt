from src.models.content import AudioFile, DocumentFile, ImageFile, VideoFile

CONTENT_TYPES = {
    "video": VideoFile,
    "image": ImageFile,
    "audio": AudioFile,
    "document": DocumentFile,
}
