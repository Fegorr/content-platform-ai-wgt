# Roadmap
 
Each task = one branch, one PR, one run of the agent pipeline. Write the full brief with `docs/task-template.md` when you start a task.
 
## Part 1: the core platform
 
| # | Task | Main outputs | Done when |
|---|---|---|---|
| 0 | Project setup | requirements.txt, pytest.ini, .gitignore, .env.example, empty `__init__.py` packages, one smoke test | `pytest` runs green; `.env` ignored |
| 1 | Content + user domain models (incl. `UserRole`) | src/models/content.py, user.py, registry.py, tests/test_models.py | every rule in domain-spec "Content models" + "User model" has a test |
| 2 | Lazy DB connection + ContentRepository | src/db/database.py, content_repository.py, tests | no connection at import; `_id` stripped; queries use `id`; `list_visible` filters in the query |
| 3 | UserRepository | src/db/user_repository.py, tests | get_by_id, get_by_email, create |
| 4 | Config, hashing, JWT | src/config.py, src/auth/hashing.py, jwt.py, tests | secret read at call time; expired/invalid token → None |
| 5 | Auth service, /login, get_current_user | src/services/auth_service.py, src/routers/auth.py, src/auth/dependencies.py, src/utils/dependencies.py, conftest fakes, tests | login form works in /docs; 401s carry WWW-Authenticate |
| 6 | ContentService (incl. ownership, draft privacy, admin delete, `preview`, `can_edit`, `can_delete` on returned items) | src/services/content_service.py, tests (Mock repo) | all service rules in domain-spec, incl. the "Who can do what" table |
| 7 | Video schemas + router | src/schemas/video.py, src/routers/videos.py, src/main.py, tests/test_videos.py | full required-test table passes |
| 8 | Image, audio, document routers | schemas + routers + tests | same table for each type |
 
Task 0 `requirements.txt` will need at least:
`fastapi`, `uvicorn[standard]`, `pydantic[email]`, `pymongo`, `certifi`, `python-dotenv`, `PyJWT`, `pwdlib[argon2]`, `python-multipart`, `pytest`, `httpx`
 
Task 0 `pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
```
 
Task 0 `.env.example` (names only, no real values):
```
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>/
JWT_SECRET_KEY=<a long random string>
```
 
## Part 2: finishing the platform (some of these depend on the "Open decisions" section of CLAUDE.md being answered first)
 
| # | Task | Why |
|---|---|---|
| 9 | Sign-up: `POST /register` + `AuthService.register_user` | real users can create accounts; duplicate emails are refused (409) |
| 10 | `GET /users/me` + `PATCH /users/me/password` | see who is logged in; change password (wrong current → 400, same as old → 400) |
| 11 | Logout: `jti` in tokens, `TokenBlocklistRepository`, `POST /logout`, `get_current_user` checks it | a logged-out token stops working straight away |
| 12 | Admin: `require_admin`, `ContentRepository.list_all`, `GET /admin/content` | the admin from the use-case diagram can see all content (admin delete is already in the service from task 6) |
| 13 | Admin seed script: `scripts/create_admin.py` | the only way to create an admin |
| 14 | `GET /users/me/content` (all my items, any type, drafts included) | shows the user → many content relationship over HTTP |
| 15 | MongoDB indexes: unique `id` in content, unique `email` in users, TTL index on `revoked_tokens.expires_at` | stops duplicates; the database deletes expired blocked tokens by itself |
| 16 | GitHub Actions: run `pytest` on every PR | tests run automatically, so a broken PR is caught before review |
| 17 | Pagination on list endpoints (`?skip=&limit=`) | lists won't stay small |
| 18 | `updated_at` field set on every PATCH | normal for publishing platforms |
| 19 | File uploads (waiting on the "Open decisions" answer) | the "Upload a file" use case from the diagram |
 
## Part 3: optional extras
- Generic router factory so a new content type is one line in main.py (refactor, only after task 8 is green)
- Integration tests against a separate test database, marked `@pytest.mark.integration` and skipped by default
- Deploy (e.g. a free hosting service + MongoDB Atlas) with secrets set in the host, not in code
- Hook in `.claude/settings.json` that blocks edits to `tests/` during the implementer step

## Definition of done for the whole platform
- A new user can sign up, log in in `/docs`, log out, and create, list, read, update, publish and delete all four content types.
- Only the author can change their content; only the author or an admin can delete it; drafts are private.
- An admin (created with the seed script) can list all content from all users.
- Every use case in the use-case diagram has a working endpoint (file upload once it's decided).
- Every endpoint has the required tests; CI runs them on every PR; nothing in tests touches real MongoDB.
- No secret in the repo; the app starts without a DB connection at import.