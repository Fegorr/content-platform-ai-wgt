---
name: python-conventions
description: How Python code is named, structured, typed and commented in this project. Use when writing, changing or reviewing Python code.
paths: "**/*.py"
---
These are project rules, not style preferences. CLAUDE.md wins if the two ever disagree.
Examples cite a file and a name (not a line number), so they stay valid when code moves. Labels:
- no label: real code, as it is now
- "(before the conventions refactor)": real code as it was before it was fixed to follow this skill
- "(example, not from our code)": made up to show the rule

## 1. Naming
- Follow PEP 8: `PascalCase` classes, `snake_case` functions, methods and variables, `UPPER_CASE` constants and enum members.
- Booleans start with `is_`, `has_` or `can_` (`can_edit`, `is_revoked`).
- A name says what the thing does or holds without needing the docstring. Say *what* is changed, not just that something happens.

Good (`src/models/content.py` `MediaType` and `BaseContent.get_preview`, `src/models/registry.py` `CONTENT_TYPES`):
```python
class MediaType(str, Enum):
    """The four kinds of content the platform stores."""

    VIDEO = "video"
    ...

CONTENT_TYPES = MappingProxyType({...})

def get_preview(self) -> str:
```

Good (`src/db/content_repository.py` `ContentRepository._strip_mongo_id`): the name says what is removed.
```python
@staticmethod
def _strip_mongo_id(document: dict) -> dict:
    """Return a copy of the document without Mongo's _id."""
```

Bad (before the conventions refactor): `_clean` doesn't say what it cleans; only the docstring did.
```python
@staticmethod
def _clean(document: dict) -> dict:
```

## 2. Classes and accessibility
- One job per class. If the class docstring joins two jobs with "and", split the class. (A list of fields joined by "and" is fine.)
- Public methods and attributes have no underscore. Internal helpers and attributes start with one `_`.
- No double-underscore (`__name`) names unless needed to avoid a name clash in a subclass.
- Use `@property` for a read-only value calculated from other fields.
- Exception: methods named in CLAUDE.md or `docs/domain-spec.md` (`get_preview`, `compress`, `append_text`) stay methods, even when they only calculate a value.

Good (`src/db/content_repository.py` `ContentRepository`): one job, said in one line; the public methods are the names from CLAUDE.md; the collection is internal.
```python
class ContentRepository:
    """The only class that touches the content collection."""

    def __init__(self, collection):
        self._collection = collection

    def create(self, document: dict) -> str: ...
    def get_by_id(self, content_id: str) -> dict | None: ...
```

Bad (before the conventions refactor): the collection was public, so any caller could reach the database past the repository.
```python
def __init__(self, collection):
    self.collection = collection
```

Good (example, not from our code): a read-only computed value.
```python
@property
def width(self) -> int:
    """The image width in pixels, read from resolution."""
    return int(self.resolution.split("x")[0])
```

Bad (example, not from our code): a getter method for a computed value, and a double underscore with no subclass clash.
```python
def get_width(self) -> int: ...
def __parse_resolution(self) -> tuple[int, int]: ...
```

## 3. Enums
- Inherit from `str` and `Enum`, so members compare and serialize as their value.
- Members are `UPPER_CASE`; values are lowercase and match the stored data exactly.
- Compare and assign with members, never with typed strings. In a database query use `Member.value`.
- When turning a member into text (f-string, `str()`, a URL path, an error message) use `Member.value`. On Python 3.11+ `f"{MediaType.VIDEO}"` gives `"MediaType.VIDEO"`, not `"video"`. This matters when looping over `CONTENT_TYPES`, whose keys are members.

Good (`src/models/content.py` `ContentStatus` and `BaseContent.publish`):
```python
class ContentStatus(str, Enum):
    """Whether a content item is visible to everyone or only its author."""

    DRAFT = "draft"
    PUBLISHED = "published"

def publish(self) -> None:
    """Set the status to published."""
    self.status = ContentStatus.PUBLISHED
```

Good (`src/db/content_repository.py` `ContentRepository.list_visible`):
```python
{"status": ContentStatus.PUBLISHED.value}
```

Bad (before the conventions refactor, excerpt): a typed string. A typo here returns wrong results with no error.
```python
{..., "$or": [{"status": "published"}, {"author_id": user_id}]}
```

## 4. Interfaces
- A base class that subclasses must complete is an `ABC`, with each required method marked `@abstractmethod`. Then a subclass that forgets a method fails when it is created, not when it is called.
- A contract that unrelated classes must meet (such as a repository and its test fake) is a `typing.Protocol`. The real class and the fake both follow it, so they can't drift apart. The fake doesn't inherit from the real class.

Good (`src/models/content.py` `BaseContent`):
```python
class BaseContent(BaseModel, ABC):
    """Abstract base for every content item."""

    @abstractmethod
    def get_preview(self) -> str:
        """Return a short text preview, calculated on every call."""
```

Good (example, not from our code): a repository contract.
```python
class ContentRepositoryContract(Protocol):
    """What every content repository (real or fake) provides."""

    def get_by_id(self, content_id: str) -> dict | None: ...
    def delete(self, content_id: str) -> int: ...
```

Bad (example, not from our code): a missing method is only noticed when it's called.
```python
class BaseContent(BaseModel):
    def get_preview(self) -> str:
        raise NotImplementedError
```

## 5. Polymorphism
- Call the shared method; don't check the type with `isinstance` or `media_type` and branch.
- Choose a class through the registry (`CONTENT_TYPES`), not an `if`/`elif` chain. A new type is then one registry line, as CLAUDE.md requires.
- An override keeps the base method's arguments and return type.
- A subclass may narrow a field's type, like `media_type: Literal[MediaType.VIDEO]` (`src/models/content.py` `VideoFile`).

Good (`src/models/content.py` `VideoFile.get_preview` and `AudioFile.get_preview`): same signature as the base.
```python
class VideoFile(MediaFile):
    """A video with duration, resolution and frame rate."""

    def get_preview(self) -> str: ...

class AudioFile(MediaFile):
    """An audio file with a duration."""

    def get_preview(self) -> str: ...
```

Good (example, not from our code): picking the class through the registry.
```python
model_class = CONTENT_TYPES[media_type]
```

Bad (example, not from our code):
```python
if isinstance(item, VideoFile):
    preview = f"Duration: {item.duration} seconds"
elif item.media_type == "image":
    preview = f"Resolution: {item.resolution}"

def get_preview(self, max_length: int) -> list[str]: ...  # changes the base signature
```

## 6. Data types and mutability
- Values that never change use immutable types: `tuple`, `frozenset`, `str`, or `MappingProxyType` for a fixed mapping.
- Never use a mutable default argument (`[]`, `{}`, `set()`). Use `None` and create the value inside, or `Field(default_factory=...)` in Pydantic.
- Copy a dict or list before passing it to code that may change it, and return copies of stored data.
- If something must stay mutable, explain why in a comment.

Good (`src/db/content_repository.py` `ContentRepository.create`): `insert_one` adds `_id` to the dict it receives, so it gets a copy and the caller's dict stays clean.
```python
self._collection.insert_one(dict(document))
```

Good (`src/models/content.py` `BaseContent.id`):
```python
id: UUID = Field(default_factory=uuid4)
```

Good (`src/models/registry.py` `CONTENT_TYPES`): a fixed lookup table that no import can change.
```python
CONTENT_TYPES = MappingProxyType(
    {
        MediaType.VIDEO: VideoFile,
        ...
    }
)
```

Bad (before the conventions refactor): a plain dict with typed-string keys; any import could change it.
```python
CONTENT_TYPES = {
    "video": VideoFile,
    ...
}
```

Bad (example, not from our code): the same list is shared by every call.
```python
def add_tags(item, tags: list[str] = []): ...
```

## 7. Comments
- Every public class, method and function has a docstring: one line saying what it does or returns.
- Exception: an override that keeps the base method's meaning may skip its docstring (`VideoFile.get_preview`). All other public methods need one. The exception covers methods only, never the class.
- Exception: special methods (`__init__`, `__eq__` and so on) are exempt from the docstring rule.
- Comments explain *why* (a reason, a trap, a decision), never *what* the next line does.

Good (`src/config.py` `get_mongodb_uri`): the docstring says the one non-obvious thing, when the value is read.
```python
def get_mongodb_uri() -> str:
    """Return the MongoDB URI, read from the environment when called."""
```

Good (`src/models/user.py` `User.lowercase_email`): a Pydantic validator, so the docstring says why it exists.
```python
@model_validator(mode="after")
def lowercase_email(self) -> "User":
    """Store the email lowercase so differently-cased emails are one account."""
```

Bad (before the conventions refactor): the same validator with no docstring; the name doesn't say when it runs or why.
```python
@model_validator(mode="after")
def lowercase_email(self):
    self.email = self.email.lower()
    return self
```

Bad (example, not from our code): a comment that repeats the code.
```python
# set status to published
self.status = ContentStatus.PUBLISHED
```
