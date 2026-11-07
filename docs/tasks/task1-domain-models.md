# Task1: Content and user domain models

Branch: task1/domain-models

## Description
Add the pure domain models the rest of the platform builds on: the abstract content base, the four content types, the media_type -> class registry, and the User model with UserRole. Models hold only fields, validation and domain behaviour (publish(), unpublish(), get_preview(), compress(), append_text()). No database, files, HTTP or schemas.

## Input
- Already exists (task 0): requirements.txt (incl. pydantic[email], email-validator), pytest.ini, empty packages src/ and src/models/, tests/test_smoke.py.
- Does not exist yet: src/models/content.py, user.py, registry.py, tests/test_models.py.
- Source of truth: docs/domain-spec.md, sections "Content models" and "User model".

## Output
- src/models/content.py: ContentStatus, MediaType, BaseContent, MediaFile, VideoFile, AudioFile, ImageFile, DocumentFile
- src/models/user.py: UserRole, User
- src/models/registry.py: CONTENT_TYPES
- tests/test_models.py

## Roles involved
- test-writer: writes tests/test_models.py
- test-runner: red check, then green check
- implementer: src/models/content.py, src/models/user.py, src/models/registry.py
- code-reviewer: reviews the diff

## Rules / behaviour
Enums
1. ContentStatus is a str Enum with exactly `draft`, `published`.
2. MediaType is a str Enum with exactly `video`, `image`, `audio`, `document` (no `text`).
3. UserRole is a str Enum with exactly `user`, `admin`.

BaseContent (Pydantic BaseModel + ABC; only `title` is whitespace-stripped, see rule 28)

4. A valid item gets a UUID `id` by default (different for two items) and a timezone-aware UTC `created_at` by default.
5. `status` defaults to `draft`.
6. `title` is required; `""` and `"   "` (whitespace only) raise ValidationError; surrounding whitespace is stripped.
7. `author_id` is required and must be a UUID (a non-UUID string raises ValidationError).
8. `media_type` must be a MediaType value (`"text"` raises ValidationError). Each concrete class fixes its own value (rule 31).
9. An invalid `status` (e.g. `"random"`) raises ValidationError.
10. BaseContent and MediaFile cannot be instantiated (TypeError: abstract `get_preview()`).
11. `publish()` sets status to `published`; `unpublish()` sets it back to `draft`.

MediaFile (abstract, extends BaseContent)

12. `url` and `file_name` are required, min_length 1 (`""` raises ValidationError), on every concrete type.

Concrete types

13. VideoFile: `duration` int > 0 (0 and negative raise), `resolution` matches `^[0-9]+x[0-9]+$` (e.g. `"1920"`, `"1920x"`, `"axb"` raise), `frame_rate` float > 0 (0 and negative raise).
14. VideoFile.get_preview() returns exactly `"Duration: {duration} seconds\nResolution: {resolution}\nFrame rate: {frame_rate}"` (e.g. `"Duration: 72 seconds\nResolution: 1920x1080\nFrame rate: 30.0"`).
15. AudioFile: `duration` int > 0; get_preview() returns exactly `"Duration: {duration} seconds"`.
16. ImageFile: `resolution` matches `^[0-9]+x[0-9]+$`; get_preview() returns exactly `"Resolution: {resolution}"`.
17. DocumentFile: `body` str min_length 1; get_preview() returns the first 100 characters of `body` (a 150-char body gives 100 chars; a short body is returned whole).
18. ImageFile.compress(percentage): `percentage <= 0` or `>= 100` raises ValueError("Invalid compression size") (test 0, -5, 100, 150). Otherwise returns the new resolution, each side calculated as in rule 30: `1200x2050` at 50 -> `"600x1025"`. The model's `resolution` is unchanged afterwards.
19. DocumentFile.append_text(text): `""` raises ValueError("No changes have been made"). Otherwise appends `text` to `body`, the model's `body` is the new value, and the new body is returned.
20. `model_dump(mode="json")` gives `id` and `author_id` as strings and matches the stored-document shape in domain-spec (e.g. video example keys).

Registry

21. `CONTENT_TYPES == {"video": VideoFile, "image": ImageFile, "audio": AudioFile, "document": DocumentFile}`, and each class rebuilds a valid item from its own `model_dump(mode="json")`.

User

22. A valid User gets a UUID `id` by default; `role` defaults to `user`; `role="admin"` is accepted.
23. An unknown role (e.g. `"superuser"`) raises ValidationError.
24. `name` is required, min_length 1; `hashed_password` is required, min_length 1.
25. `email` must be a valid email (`"not-an-email"` raises ValidationError) and is lowercased by the model: `"Louise@Test.com"` -> `"louise@test.com"`.

Purity

26. Importing src.models.content, user and registry opens no network connection and reads no files (no pymongo, no open(), no HTTP in these modules).

Float fields

27. Float fields (`frame_rate`) refuse `inf`, `-inf` and `nan`: each raises ValidationError.

Whitespace

28. Only `title` is whitespace-stripped. `body`, `url`, `file_name` and `resolution` keep their spaces and newlines exactly as given (e.g. a DocumentFile body `"  indented\n"` is stored unchanged).

Resolution digits

29. `resolution` (VideoFile and ImageFile) only accepts the ASCII digits 0–9 in the form `WIDTHxHEIGHT`. Other kinds of digits (e.g. Arabic-Indic `"١٩٢٠x١٠٨٠"`) raise ValidationError, on both types. A resolution with spaces around it (e.g. `" 1920x1080 "`) also raises ValidationError on both types, since `resolution` is not stripped (rule 28).

Compress formula

30. ImageFile.compress calculates each side as `int(side * (100 - percentage) / 100)`. `1200x2050` at 33 -> `"804x1373"`; at 50 -> `"600x1025"`.

Fixed media_type

31. Each content class fixes its own `media_type` with a default: VideoFile is always `video`, ImageFile `image`, AudioFile `audio`, DocumentFile `document`. Creating one without `media_type` sets it automatically; creating one with a different `media_type` (e.g. `VideoFile(media_type="audio")`) raises ValidationError.

## Out of scope
- No schemas (Create/Update/Response), repositories, services, routers, auth, config or main.py.
- No `preview`, `can_edit` or `can_delete` fields on the models (the service adds them, task 6).
- No tests/conftest.py fakes (task 5).
- No file uploads (open decision 1): content keeps a `url` string only.
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues
- [ ] New packages added to requirements.txt (none expected)
- [ ] No .env or secrets in the diff
- [ ] `git pull origin main --rebase` done, tests still pass
- [ ] PR opened with `gh pr create --base main --fill`
