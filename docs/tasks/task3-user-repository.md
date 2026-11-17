# Task3: UserRepository

Branch: task3/user-repository

## Description
Add the users collection getter and UserRepository, the only class that touches
the users collection. It works with plain dicts, queries by the id and email
fields (never Mongo's _id) and never returns _id.

## Input
- Built on chore/coding-conventions (PR pending). Rebase onto main once it's merged.
- Already exists: src/config.py, src/db/database.py (get_client, get_content_collection),
  src/db/content_repository.py (ContentRepository with its private _strip_mongo_id),
  src/models/user.py (User, UserRole), the python-conventions skill.
- Does not exist yet: get_users_collection(), src/db/user_repository.py, tests/test_user_repository.py.
- Source of truth: CLAUDE.md "Architecture" (Repository method names) and
  docs/domain-spec.md "User model".

## Output
- src/db/database.py: add get_users_collection()
- src/db/user_repository.py: UserRepository
- tests/test_database.py: add tests for the new getter
- tests/test_user_repository.py

## Roles involved
- test-writer: tests/test_user_repository.py, new tests in tests/test_database.py
- test-runner: red check, then green check
- implementer: src/db/database.py, src/db/user_repository.py
- code-reviewer: reviews the diff

## Rules / behaviour
Database (`src/db/database.py`)

1. `get_users_collection()` returns `get_client()["content-platform"]["users"]` (database `content-platform`, collection `users`). Test it the same way as `get_content_collection`, by patching `get_client`.

UserRepository (`src/db/user_repository.py`)

2. `UserRepository(collection)` takes the collection in its constructor and never calls get_client(). Test: patch `get_client`, build the repository with a `Mock()` collection, call its methods, and assert `get_client` was not called.
3. `create(document) -> str`: calls `insert_one` once with a dict equal to `document`. It does not change the caller's dict: if `insert_one` adds `_id` to the dict it receives, the caller's `document` still has no `_id`. Returns `document["id"]`, not Mongo's `inserted_id`.
4. `get_by_id(user_id) -> dict | None`: calls `find_one({"id": user_id})` (exact query). Returns the user without `_id`, or None when `find_one` returns None.
5. `get_by_email(email) -> dict | None`: calls `find_one({"email": email})` with the email exactly as given (test with `"Louise@Test.com"` and assert the query was not lowercased). Returns the user without `_id`, or None. Lowercasing is the service's job (Task 5).
6. `get_by_id` and `get_by_email` return a new dict, not the object `find_one` returned (test with Mock return values that include `_id`; the Mock's dict keeps its `_id` after the call).
7. `update(user_id, updates) -> int`: calls `update_one({"id": user_id}, {"$set": updates})` and returns the result's `matched_count`, so an update that sets the same values still counts as found (matched_count 1, modified_count 0 -> returns 1). An unknown id returns 0.
8. Returned users include `hashed_password`: login needs it. Removing it from API responses is the router's job (response_model).

## Out of scope
- No shared _id-stripping helper and no change to ContentRepository: UserRepository has its own private `_strip_mongo_id`, like ContentRepository. A shared helper is a separate chore (it also needs CLAUDE.md and the python-conventions skill updated).
- No unique email index (Task 15), no AuthService, no hashing, no routers, no Protocol (Task 5).
- No `get_revoked_tokens_collection()` or TokenBlocklistRepository (Task 11).
- No src/utils/dependencies.py wiring or tests/conftest.py fakes (Task 5).
- Tests use Mock() collections: never a real database, .env or the network.
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Existing tests unchanged and green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues
- [ ] New packages added to requirements.txt (none expected)
- [ ] No .env or secrets in the diff
- [ ] `git pull origin main --rebase` done, tests still pass
- [ ] PR opened with `gh pr create --base main --fill`
