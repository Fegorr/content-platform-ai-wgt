# Content Publishing Platform (AI-built version)

## Before you start (every agent and session)
1. Read this whole file first. These rules override any pattern you find in code or examples.
2. This repo is built from scratch with TDD. Don't assume a file, class or route exists: check first.
3. Work only on the task you were given. If the task is unclear, conflicts with this file, or needs a decision this file doesn't make or needs a decision that hasn't been made yet, stop and ask. Don't guess or invent names. Undecided questions are listed in the "Open decisions" section of this file.
4. Before changing anything, state your plan in a few lines: which files, what changes, how you'll verify it.
5. Never read, edit or commit .env. The variable names are in .env.example.
6. Finish by reporting what you changed and the exact pytest command you ran with its result.

## Project
A REST API for a content publishing platform. People sign up, log in and log out. Users create, read, update, delete and publish their own content. An admin can see and delete all content. There are four content types: video, image, audio and document. They all extend one abstract base content model.

### Content
- Every content item has:id (UUID), title, author_id, created_at, status(draft/published), media_type. New content starts as draft.
- media_type values are exactly: video, image, audio, document (not text).
- Type-specific fields:
  - Video: url, file_name, duration, resolution, frame_rate
  - Audio: url, file_name, duration
  - Image: url, file_name, resolution (WIDTHxHEIGHT)
  - Document: url, file_name, body
- The base model declares an abstract get_preview(). Each type implements it differently (polymorphism).
- Every content response includes a preview field: the result of that item's get_preview(). It is calculated every time, never saved in the database, so it is always up to date after a PATCH.
- Publishing is done with PATCH by setting status to published (the service calls the model's publish(); draft calls unpublish()). There is no separate publish endpoint.
- Adding a new content type should not require changing existing types (only a new model, schemas, router and one registry line).

### Users and roles
- Every user has a role: user or admin. Sign-up always creates user. The client can never set or change role.
- The only way to create an admin is the seed script scripts/create_admin.py, run by hand. The API has no route that makes someone an admin.
- A user is an author and can own many items (linked by author_id).

### Who can do what
| Item is... | GET one | in GET list | PATCH | DELETE |
|------------|---------|-------------|-------|--------|
| mine (draft or published) | 200 | yes | 200 | 200 |
| someone else's published | 200 | yes | 403 | 403(admin:200)
| someone else's draft | 404(admin:200) | no | 404(admin: 403) | 404(admin:200) |

- A normal user can never edit or delete someone's content, whether it is published or a draft. Only the author edits; only the author or an admin deletes.
- Every content response includes can_edit and can_delete(true/false) for the logged-in user, so a website only shows Edit/Delete buttons where they're allowed. can_edit is true only for the author. can_delete is true for the author or an admin. Like preview, they are calculated every time and never saved.
- The buttons are only the screen. The server still checks every PATCH and DELETE, because anyone can send a request without the website.
- 403 detail: "You can only change your own content".
- A content list (GET /videos etc.) returns everyone's published items plus the logged-in user's own drafts. An admin's list is the same; the admin uses /admin/content to see everything.
- Admin can never edit someone else's content(PATCH), only delete it.
- GET /admin/content: admin only. Returns every content item of every type and every user, drafts included, with preview. A non-admin gets 403 "Admin access required".

### More detail
- Exact fields, constraints, preview strings, endpoints and stored-document shape: docs/domain-spec.md. Read it before writing models, schemas, routers or their tests.
- Task order and the finished-platform picture: docs/roadmap.md

Stack: Python, FastAPI, MongoDB via pymongo, Pydantic v2, pytest, JWT auth (PyJWT HS256+pwdlib[argon2] password hashing. OAuth2password bearer login). Access tokens expire after 30 minutes. Secrets (MONGODB_URI, JWT_SECRET_KEY) come from .env.

## Where things live
- `src/main.py`: created the app and includes the routers
- `src/config.py`: reads settings from the environment when called, not at import
- `src/models/`: content.py (domain models), user.py (User, UserRole), registry.py (media_type -> model class)
- `src/schemas/`: payloads: <Type>Create, <Type>Update, <Type>Response, UserCreate, UserResponse, TokenResponse
- `src/db/`: database.py (get_client and the get_..._collection functions), content_repository.py, user_repository.py, token_blocklist_repository.py
- `src/services/`: content_service.py, auth_service.py
- `src/auth/`: hashing.py, jwt.py, dependencies.py (get_current_user, require_admin)
- `src/routers/`: auth.py (register, login, logout), users.py, admin.py, videos.py, images.py, audios.py, documents.py
- `src/utils/dependencies.py`: wiring: collection -> repository -> service
- `scripts/create_admin.py`: run by hand to create an admin; never imported by the app
- `tests/conftest.py`: fake repositories, test users, auth headers, dependency overrides
- `tests/test_<module>.py`: one test file per module or router
- `docs/`: domain-spec.md, roadmap.md, task-template.md


## Architecture (required, not optional)
- Requests go Router → Service → Repository. Only repositories touch the database.
- Models stay pure: no file reads, no DB calls, no HTTP. Only fields, validation and domain behaviour (publish(), unpublish(), get_preview(), compress(), append_text()).
- Payload models (Create/Update/Response) live in src/schemas/, are flat and separate from domain models. Update models make every field optional. Routers convert payloads into domain models.
- The server sets these fields, never the client, and they are not on Create?Update payloads:
  - media_type: from the endpoint (e.g /videos -> video)
  - author_id: from the logged-in user's token
  - id and created_at: generated by the server
  - status: always drafts on create; only PATCH can change it
  - role: always user on sign-up
- Database:
  - Database content-platform, collections content (all four types, told apart by media_type), users and revoked_tokens.
  - Documents are stored with model_dump(mode="json"), so id and author_id are strings. Queries use the id field, never Mongo's _id.
  - _id never leaves a repository: repositories strip it before returning.
  - Connect to MongoDB inside get_client() (cached), never at import. Importing any module must not open a network connection.
- Repository method names (use exactly these):
  - ContentRepository: create(document) -> str, get_by_id(content_id) -> dict | None, list_visible(media_type, user_id) -> list[dict] (published items of this type + this user's drafts of this type, filtered in the database query), list_all() -> list[dict], update(content_id, updates) -> int, delete(content_id) -> int
  - UserRepository: create(document) -> str, get_by_id(user_id) -> dict | None, get_by_email(email) -> dict | None, update(user_id, updates) -> int
  - TokenBlocklistRepository: add(jti, expires_at) -> None, is_revoked(jti) -> bool
- Users are stored and read through UserRepository, never from a JSON file.
- The service owns business rules: wrong media_type counts as not found, the "Who can do what" table, ignoring unset/None fields on PATCH, calling publish()/unpublish(), re-validating the merged item before saving, adding preview. Routers pass the logged-in user (dict with id and role) to the service and only turn the result into a status code.
- Every layer is wired with FastAPI Depends (collection->repository->service), so tests can override any layer.
- Path ids are typed str, so an unknown or malformed id returns 404, not 422.
- Responses never include _id or hashed_password. Use response_model on every route.

## Auth
- POST /register and POST /login are the only public routes. Everything else needs a token.
- Sign-up: POST /register with JSON {name, email, password} -> 201 UserResponse (id, name, email, role). The service hashes the password before saving; the plain password is never stored, returned or logged.
  - Emails are stored lowercase, so Louise@Test.com and louise@test.com are the same account.
  - Email already registered -> 409 "Email already registered".
  - Invalid email, empty name, or password shorter than 8 characters -> 422.
  - A role sent by the client is ignored.
- Login: POST /login takes OAuth2 form data (username = email, password) via  OAuth2PasswordRequestForm (needs python-multipart), so the Authorize button in /docs works.
  - Success -> {"access_token": "...", "token_type": "bearer"}. Unknown email or wrong password -> 401 "Invalid email or password" (same message for both).
- Token payload: sub = user id (string), jti = a new UUID per token (the token's own id), exp = now (UTC) + 30 minutes. Decode with algorithms=["HS256"].
- Logout: POST /logout(needs a token) saves the token's jti and exp with TokenBlocklistRepository.add -> 200 {"message": "Logged out"}. From then on that token gets 401, even before it expires. Other tokens of the same user keep working.
- get_current_user returns 401 with header WWW-Authenticate: Bearer when the token is missing, invalid, expired, revoked (logged out), or belongs to a user that no longer exists.
- require_admin builds on get_current_user: not an admin -> 403 "Admin access required".
- Every content router uses dependencies=[Depends(get_current_user)], plus current_user as a parameter where the service needs it.

## Open decisions
These questions have no answer yet. If your task depends on one of them, stop and ask. Don't pick an answer yourself.
  1. File uploads: should the API accept real files (video, image, audio) and store them, or keep taking a url that points to a file stored somewhere else? Until decided, content is created with a url only.

## Commands
- Install: pip install -r requirements.txt
- Run tests: pytest (pytest.ini sets pythonpath = . and testpaths = tests)
- Start the API: uvicorn src.main:app --reload, then open http://127.0.0.1:8000/docs
- Create an admin (on your own computer, with .env set): python scripts/create_admin.py

## Testing
- Tests never touch real MongoDB, real files, .env or the network. Use fakes in tests/conftest.py or Mock().
- tests/conftest.py sets a test JWT_SECRET_KEY before importing the app.
- Follow the testing-conventions skill for stand-ins, naming, style and the required test cases.
- Every endpoint gets tests for: success, validation error (422), not found (404), missing/invalid token (401), and forbidden (403) where the "Who can do what" table says so.

## Agent pipeline (one task)
1. Main session: plan the task with the user and write the brief using docs/task-template.md. Create the branch.
2. test-writer: writes failing tests from the brief.
3. test-runner (red check): confirms they fail for the right reason.
4. implementer: writes code in src/ (and scripts/) until the tests pass. Never edits tests/.
5. test-runner (green check): new tests and the full suite pass.
6. code-reviewer: reviews the diff. Blocking issues go back to step 4 (or step 2 if a test is wrong).
7. Main session: commit, git pull origin main --rebase, pytest, push, open the PR. Maria reviews and merges. Subagents never commit, push, open or merge PRs. If the remote branch doesn't exist, do git push and create pr

## Workflow
- We use TDD: red -> green -> refactor. The test-writer writes tests first; the implementer never changes tests.
- One branch per task: taskN/short-description (e.g. task7/video-router).
- Commit messages: taskN: short summary.
- One PR per task. Before pushing, run git pull origin main --rebase and make sure pytest passes.
- Open the PR task. Before pushing, run git origin main --rebase and make sure pytest passes.
- Never commit .env.
- Every package you import goes in requirements.txt (including pymongo, PyJWT, pwdlib[argon2], python-multipart, email-validator, httpx).

## Compact instructions
When compacting, keep: the current task and branch, the list of changed files, open questions, and the last test command with its result.