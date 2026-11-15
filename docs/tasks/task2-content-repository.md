# Task2: Config, lazy DB connection + ContentRepository

Branch: task2/content-repository

## Description
Add the database layer for content: a minimal config function for the MongoDB URI, a cached MongoDB client that connects only when first called (never at import), a getter for the `content` collection, and ContentRepository, the only class that touches the content collection. The repository stores and returns plain dicts, queries by the `id` field (never Mongo's `_id`) and strips `_id` from everything it returns.

## Input
- Already exists (task 0): requirements.txt (incl. pymongo, certifi), pytest.ini, empty packages src/ and src/db/, tests/test_smoke.py.
- Task 1 (domain models) is on its own branch and not merged yet. This task does not import src/models/: the repository works with plain dicts.
- Does not exist yet: src/config.py, src/db/database.py, src/db/content_repository.py and their tests.
- Source of truth: CLAUDE.md "Architecture" (Database, Repository method names) and docs/domain-spec.md "Stored documents".

## Output
- src/config.py: get_mongodb_uri()
- src/db/database.py: get_client(), get_content_collection()
- src/db/content_repository.py: ContentRepository
- tests/test_config.py
- tests/test_database.py
- tests/test_content_repository.py

## Roles involved
- test-writer: writes tests/test_config.py, tests/test_database.py, tests/test_content_repository.py
- test-runner: red check, then green check
- implementer: src/config.py, src/db/database.py, src/db/content_repository.py
- code-reviewer: reviews the diff

## Rules / behaviour
Config (`src/config.py`)

1. `get_mongodb_uri()` returns `os.environ["MONGODB_URI"]`, read when it is called, not at import. If the variable changes between two calls, the second call returns the new value (test with `monkeypatch.setenv`).
2. If `MONGODB_URI` is not set, `get_mongodb_uri()` raises `RuntimeError("MONGODB_URI is not set")` (test with `monkeypatch.delenv`).
3. src/config.py does not call `load_dotenv()` and does not read `.env`. Importing it reads nothing from the environment.

Database (`src/db/database.py`)

4. Importing src.db.database creates no MongoClient and opens no network connection (patch `pymongo.MongoClient` with a Mock, reload the module, assert the Mock was not called).
5. `get_client()` creates the client with exactly `MongoClient(config.get_mongodb_uri(), server_api=ServerApi("1"), tlsCAFile=certifi.where())` (`from pymongo.server_api import ServerApi`). Test: patch `MongoClient` in src.db.database with a Mock, call `get_client()`, and check the one call: `assert_called_once()`, the only positional arg is the URI, the keyword args are exactly `server_api` and `tlsCAFile`, `tlsCAFile == certifi.where()`, and `server_api` is a `ServerApi` with `.version == "1"`. (`ServerApi` has no `__eq__`, so `assert_called_once_with(..., server_api=ServerApi("1"), ...)` would always fail; compare the version instead.)
6. `get_client()` is cached with `functools.lru_cache`: two calls return the same object and MongoClient is created only once. Tests call `get_client.cache_clear()` before and after each test (fixture).
7. If `MONGODB_URI` is missing, `get_client()` raises `RuntimeError("MONGODB_URI is not set")` and MongoClient is not called.
8. `get_content_collection()` returns `get_client()["content-platform"]["content"]` (database `content-platform`, collection `content`).

ContentRepository (`src/db/content_repository.py`)

9. `ContentRepository(collection)` takes the collection in its constructor. It never creates a client or calls get_client() itself. Tests use a `Mock()` collection.
10. `create(document) -> str`: calls `insert_one` once with a dict equal to `document`. It does not change the caller's dict: if `insert_one` adds `_id` to the dict it receives, the caller's `document` still has no `_id`. Returns `document["id"]`, not Mongo's `inserted_id`.
11. `get_by_id(content_id) -> dict | None`: calls `find_one({"id": content_id})` (exact query). Returns the document without `_id`. Returns None when `find_one` returns None.
12. `list_visible(media_type, user_id) -> list[dict]`: calls `find` once with exactly `{"media_type": media_type, "$or": [{"status": "published"}, {"author_id": user_id}]}`, so the filter runs in the database query, not in Python. Returns every document without `_id`. Returns `[]` when nothing matches.
13. `list_all() -> list[dict]`: calls `find({})` once and returns every document without `_id`. Returns `[]` when the collection is empty.
14. `update(content_id, updates) -> int`: calls `update_one({"id": content_id}, {"$set": updates})` and returns the result's `matched_count`, so an update that sets the same values still counts as found (matched_count 1, modified_count 0 -> returns 1). An unknown id returns 0.
15. `delete(content_id) -> int`: calls `delete_one({"id": content_id})` and returns the result's `deleted_count` (1 when deleted, 0 for an unknown id).
16. `_id` never leaves the repository: every method that returns documents strips it (test with Mock return values that include `_id`).

## Out of scope
- No `get_users_collection()` (task 3) or `get_revoked_tokens_collection()` (task 11).
- No UserRepository or TokenBlocklistRepository.
- No JWT settings in config.py (task 4). No `load_dotenv()`.
- No src/utils/dependencies.py wiring, services, routers or tests/conftest.py fakes (task 5 onward).
- No indexes (task 15), pagination (task 17) or `updated_at` (task 18).
- No real MongoDB, `.env` or network in tests.
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues
- [ ] New packages added to requirements.txt (none expected: pymongo and certifi are already there)
- [ ] No .env or secrets in the diff
- [ ] `git pull origin main --rebase` done, tests still pass
- [ ] PR opened with `gh pr create --base main --fill`
