# Domain spec

The single source of truth for names, fields, rules and API behaviour. CLAUDE.md has the architecture rules; this file has the details. If code and this file disagree, ask which one is right.

## Content models (`src/models/content.py`)

### ContentStatus (str Enum)
`draft`, `published`

### MediaType (str Enum)
`video`, `image`, `audio`, `document`

### BaseContent (abstract, Pydantic BaseModel + ABC)
Model config: `str_strip_whitespace=True` (so a title of `"   "` fails `min_length=1`).

| Field | Type | Rule | Set by |
|---|---|---|---|
| id | UUID | default `uuid4()` | server |
| title | str | min_length 1 | client |
| author_id | UUID | required | server (from token) |
| created_at | datetime | default `datetime.now(timezone.utc)` | server |
| status | ContentStatus | default `draft` | server on create, PATCH after |
| media_type | MediaType | required | server (from endpoint) |

Methods:
- `publish()` -> sets status to `published`
- `unpublish()` -> sets status to `draft`
- `get_preview()` -> str -> abstract, no body

### MediaFile (abstract, extends BaseContent)
| Field | Type | Rule |
|---|---|---|
| url | str | min_length 1 |
| file_name | str | min_length 1 |

Does not implement `get_preview()`.

### Concrete types

| Type | Extra fields | `get_preview()` returns |
|---|---|---|
| VideoFile | duration: int > 0 (seconds), resolution: str `^\d+x\d+$`, frame_rate: float > 0 | `"Duration: {duration} seconds\nResolution: {resolution}\nFrame rate: {frame_rate}"` |
| AudioFile | duration: int > 0 (seconds) | `"Duration: {duration} seconds"` |
| ImageFile | resolution: str `^\d+x\d+$` | `"Resolution: {resolution}"` |
| DocumentFile | body: str min_length 1 | first 100 characters of `body` |

Extra domain methods:
- `ImageFile.compress(percentage: float) -> str`: if `percentage <= 0` or `percentage >= 100` raise `ValueError("Invalid compression size")`. Otherwise return the new resolution string, each side `int(side * (1 - percentage / 100))`. Does not change the model. Example: `1200x2050` at 50 -> `600x1025`.
- `DocumentFile.append_text(text: str) -> str`: if `text == ""` raise `ValueError("No changes have been made")`. Otherwise append to `body` and return the new body.

### Registry (`src/models/registry.py`)
`CONTENT_TYPES = {"video": VideoFile, "image": ImageFile, "audio": AudioFile, "document": DocumentFile}`
Adding a content type = new model + schemas + router + one line here.

## User model (`src/models/user.py`)

### UserRole (str Enum)
`user`, `admin`

| Field | Type | Rule |
|---|---|---|
| id | UUID | default `uuid4()` |
| name | str | min_length 1 |
| email | EmailStr | required, stored lowercase |
| hashed_password | str | min_length 1 |
| role | UserRole | default `user` |

No file reads or DB calls in the model. To find a content item's author, use `UserRepository.get_by_id(author_id)`.

## Stored documents (MongoDB)
Saved with `model_dump(mode="json")`. Example in `content`:
```json
{
  "id": "6f1c...-uuid",
  "title": "Intro",
  "author_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-10-25T10:00:00Z",
  "status": "draft",
  "media_type": "video",
  "url": "https://example.com/v.mp4",
  "file_name": "v.mp4",
  "duration": 72,
  "resolution": "1920x1080",
  "frame_rate": 30.0
}
```
Example in `revoked_tokens`: `{"jti": "9b2e...-uuid", "expires_at": "2026-10-25T10:30:00Z"}`
 
Mongo adds `_id`. Repositories remove it before returning.

## Schemas (`src/schemas/`)
- `<Type>Create`: only client fields (title + the type's fields), same constraints as the domain model. Extra fields are ignored.
- `<Type>Update`: same fields as Create plus `status: ContentStatus | None`, all optional, same constraints.
- `<Type>REsponse`: every domain field (incl. id, author_id, created_at, status, media_type) plus `preview: str`, `can_edit: bool`, `can_delete: bool`.
- `ContentResponse`: ussed by `/admin/content`. The base fields (id,title, author_id, created_at, status, media_type, preview, can_edit, can_delete) plus any type-specific fields the item has.
- `UserCreate`: name (min 1), email (EmailStr), password (min 8). No `role`. Used by `/register`.
- `PasswordChange`: current_password (min 1), new_password (min 8).
- `UserResponse`: id, name, email, role (never hashed_password).
- `TokenResponse`: access_token, token_type.
- `MessageResponse`: message.

## Content service (`src/services/content_service.py`)
`ContentService(repository)`. `user` is always the logged-in user as a dict with at least `id` and `role`.

Every method that returns content returns it with a `preview` key added: turn the stored dict back into its model with `CONTENT-TYPES[media_type]` and call `get_preview()`. `preview` is never passed to the repository.

The same methods also add, for the user asking:
- `can_edit`: `author_id == user["id"]`
- `can_delete`: `author_id == user["id"]` or `user["role"] == "admin"`

These are never passed to the repository either. `create_content` and `list_all_content` take the user too, so they can add them.

"Visible to the user" means: the item exists, has this media_type, and is `published`, OR authored by the user, OR the user is an admin. Anything not visible is treated as not found.

- `create_content(content: BaseContent, user: dict) -> dict`: saves `content.model_dump(mode="json")`, returns the stored dict with `preview`, `can_edit`, `can_delete` added.
- `list_content(media_type: str, user: dict) -> list[dict]`: calls `repository.list_visible(media_type, user["id"])` (same for admins).
- `list_all_content(user: dict) -> list[dict]`: calls `repository.list_all()`. Only reached through the admin route.
- `get_content(media_type: str, content_id: str, user: dict) -> dict | None`: None if not visible to the user.
- `update_content(media_type: str, content_id: str, changes: dict, user: dict) -> ChangeResult`, checked in this order:
  1. not visible → `NOT_FOUND`
  2. visible but `author_id != user["id"]` → `FORBIDDEN` (admins included: admins never edit others' content)
  3. drop keys whose value is None; nothing left → `NO_CHANGES`
  4. merge existing + changes, re-validate with the class from `CONTENT_TYPES`
  5. `status` published → `publish()`, draft → `unpublish()`
  6. save the changed fields → `UPDATED`
- `delete_content(media_type: str, content_id: str, user: dict) -> ChangeResult`:
  1. not visible → `NOT_FOUND`
  2. not the author AND not an admin → `FORBIDDEN`
  3. delete → `DELETED`
- `ChangeResult` is a str Enum: `NOT_FOUND`, `FORBIDDEN`, `NO_CHANGES`, `UPDATED`, `DELETED`.

### Who can do what (summary)
| Item is… | GET one | in GET list | PATCH | DELETE |
|---|---|---|---|---|
| mine (draft or published) | 200 | yes | 200 | 200 |
| someone else's, published | 200 | yes | 403 | 403 (admin: 200) |
| someone else's, draft | 404 (admin: 200) | no | 404 (admin: 403) | 404 (admin: 200) |
 
## Auth service (`src/services/auth_service.py`)
`AuthService(user_repository, token_blocklist_repository)`:
- `register_user(name, email, password) -> dict | None`: lowercases the email; if `get_by_email` finds it, return None (router → 409) without saving. Otherwise build a `User` (role `user`) with `hash_password(password)`, save it, return the stored dict.
- `authenticate_user(email, password) -> dict | None`: lowercases the email; None for unknown email or wrong password.
- `change_password(user_id, current_password, new_password) -> PasswordResult` (str Enum), checked in this order:
  1. `current_password` doesn't verify → `WRONG_CURRENT` (router → 400 `"Current password is incorrect"`)
  2. `new_password` verifies against the current hash (same as the old one) → `SAME_AS_OLD` (router → 400 `"New password must be different"`)
  3. save `hash_password(new_password)` with `user_repository.update` → `CHANGED`
- `logout(jti, expires_at) -> None`: calls `token_blocklist_repository.add(jti, expires_at)`.
- `is_token_revoked(jti) -> bool`: used by `get_current_user`.

## Admin seed script (`scripts/create_admin.py`)
- Run by hand: `python scripts/create_admin.py`. Asks for name, email and password in the terminal (password hidden with `getpass`).
- Uses the real `UserRepository` and `hash_password`. Saves a user with role `admin`.
- Email already registered → prints `"Email already registered"` and saves nothing.
- Keep the logic in a function `create_admin(user_repository, name, email, password) -> dict | None` so it can be tested with a fake repository. The terminal prompts only call that function.

## API
 
| Method | Path | Auth | Success | Errors |
|---|---|---|---|---|
| POST | /register | public | 201 UserResponse | 409, 422 |
| POST | /login | public | 200 TokenResponse | 401, 422 |
| POST | /logout | token | 200 `{"message": "Logged out"}` | 401 |
| GET | /users/me | token | 200 UserResponse | 401 |
| PATCH | /users/me/password | token | 200 `{"message": "Password changed"}` | 400, 401, 422 |
| GET | /admin/content | admin token | 200 list[ContentResponse] | 401, 403 |
| POST | /videos | token | 201 VideoResponse | 401, 422 |
| GET | /videos | token | 200 list[VideoResponse] | 401 |
| GET | /videos/{video_id} | token | 200 VideoResponse | 401, 404 |
| PATCH | /videos/{video_id} | token | 200 `{"message": "Video updated"}` or `{"message": "No changes made"}` | 401, 403, 404, 422 |
| DELETE | /videos/{video_id} | token | 200 `{"message": "Video deleted"}` | 401, 403, 404 |
 
Same for `/images` (Image), `/audios` (Audio), `/documents` (Document). 404 detail: `"<Type> not found"`. 403 detail: `"You can only change your own content"`. Admin-route 403 detail: `"Admin access required"`.
 