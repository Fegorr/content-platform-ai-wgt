# Task5: Auth service, /login and get_current_user

Branch: task5/auth-service-and-login

## Description
Add the first HTTP layer: AuthService (authenticate_user, get_user_by_id), POST /login
(OAuth2 form, so the Authorize button in /docs works), get_current_user for protected
routes, the collection -> repository -> service wiring, src/main.py, and the shared
tests/conftest.py with a FakeUserRepository.

## Input
- Built on task4/hashing-and-jwt (PR not merged yet). Rebase onto main once it's merged.
- Already exists: src/config.py (get_mongodb_uri, get_jwt_secret_key),
  src/auth/hashing.py (hash_password, verify_password), src/auth/jwt.py
  (create_access_token, decode_access_token, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES),
  src/db/database.py (get_client, get_users_collection), src/db/user_repository.py
  (UserRepository: create, get_by_id, get_by_email, update), src/models/user.py.
- Does not exist yet: src/main.py, src/services/auth_service.py, src/routers/auth.py,
  src/auth/dependencies.py, src/utils/dependencies.py, src/schemas/auth.py,
  tests/conftest.py.
- Source of truth: CLAUDE.md "Auth" and docs/domain-spec.md "Auth service", "Schemas",
  "API". If this brief and the domain spec disagree, the domain spec wins.

## Output
- src/services/auth_service.py: AuthService                        ← implementer
- src/schemas/auth.py: TokenResponse                               ← implementer
- src/routers/auth.py: POST /login                                 ← implementer
- src/auth/dependencies.py: oauth2_scheme, get_current_user        ← implementer
- src/utils/dependencies.py: get_user_repository, get_auth_service ← implementer
- src/main.py: app, includes only the auth router                  ← implementer
- tests/conftest.py: test secret, FakeUserRepository, users, header fixtures ← test-writer
- tests/test_auth_service.py                                       ← test-writer
- tests/test_auth.py (/login)                                      ← test-writer
- tests/test_auth_dependencies.py (get_current_user)               ← test-writer
- tests/test_utils_dependencies.py (wiring)                        ← test-writer

## Roles involved
- test-writer, test-runner (red, then green), implementer, code-reviewer

## Rules / behaviour
Every public function and class has a one-line docstring (python-conventions).

AuthService (src/services/auth_service.py). Test with a Mock() repository.
1. AuthService(user_repository) takes only the user repository. Its methods in this
   task are authenticate_user and get_user_by_id. Task 11 adds the revoked-token check
   to this service.
2. authenticate_user(email, password) lowercases the email before calling
   get_by_email: "Louise@Test.com" -> get_by_email.assert_called_once_with("louise@test.com").
3. Right password -> returns the dict get_by_email returned.
4. Unknown email (get_by_email returns None) -> still calls verify_password once, against
   a fixed dummy argon2 hash (a module constant), then returns None. An unknown email and
   a wrong password take about the same time, so timing can't reveal which emails exist.
   Test: patch src.services.auth_service.verify_password and assert it was called once.
5. Wrong password -> None (verify_password called once, with the stored hash).
6. get_user_by_id(user_id) calls get_by_id(user_id) and returns the user without
   hashed_password (id, name, email, role), or None if get_by_id returns None. It does
   not change the dict the repository returned.

Schema (src/schemas/auth.py)
7. TokenResponse(access_token: str, token_type: str).

Wiring (src/utils/dependencies.py)
8. get_user_repository() returns UserRepository(get_users_collection()).
   get_auth_service(user_repository = Depends(get_user_repository)) returns
   AuthService(user_repository). Test by patching get_users_collection: no real client.
9. Importing src.utils.dependencies, src.routers.auth or src.main with no MONGODB_URI set
   does not open a connection (get_client is not called at import).

POST /login (src/routers/auth.py). Test with TestClient and the conftest fakes.
10. Takes OAuth2PasswordRequestForm (form data: username = email, password) and calls
    AuthService.authenticate_user. The route uses response_model=TokenResponse.
11. Correct credentials -> 200 {"access_token": ..., "token_type": "bearer"}. The token
    decodes with decode_access_token and its sub is the user's id.
12. The email is case-insensitive: username "Louise@Test.com" logs in Louise.
13. Wrong password -> 401 "Invalid email or password". Unknown email -> 401 with the
    same detail. Both carry WWW-Authenticate: Bearer.
14. Missing username or missing password -> 422.
15. POST /login with a JSON body returns 422, because login takes form data.
16. The response never contains hashed_password or password.

get_current_user (src/auth/dependencies.py)
17. oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login").
18. get_current_user(token = Depends(oauth2_scheme), auth_service =
    Depends(get_auth_service)) decodes the token and returns
    auth_service.get_user_by_id(payload["sub"]): a dict with id, name, email, role and
    no hashed_password. Router -> Service -> Repository: it never touches the
    repository itself.
19. 401 with WWW-Authenticate: Bearer for:
    - no Authorization header (detail "Not authenticated", FastAPI's default)
    - a malformed token, a token signed with another secret, an expired token
    - a valid token whose sub is not a known user
    For all but the first, the detail is "Could not validate credentials". One test each.
20. get_current_user does not check for revoked tokens (Task 11).

src/main.py
21. app = FastAPI(); app.include_router(auth router). No content routers.
    In app.openapi(), POST /login takes form data (application/x-www-form-urlencoded)
    with username and password fields. The Authorize button only appears once a route
    depends on oauth2_scheme, so checking it moves to Task 7.

tests/conftest.py
22. Sets os.environ["JWT_SECRET_KEY"] (direct assignment, not setdefault, at least 32
    characters) before importing src.main.
23. FakeUserRepository has exactly UserRepository's method names (create, get_by_id,
    get_by_email, update), stores copies (dict(document)) and matches the email exactly
    as given (no lowercasing, like the real repository).
24. The test_user, other_user and admin_user fixtures use the ids, names, emails,
    passwords and roles from the testing-conventions table. Passwords are hashed once
    per test session (module level), not per test: argon2 is slow and the autouse
    fixture runs for every test.
25. An autouse fixture puts a fresh FakeUserRepository with the three users into
    app.dependency_overrides[get_user_repository] and clears the overrides after each test.
26. auth_headers, other_auth_headers and admin_auth_headers fixtures.
    No Protocol (CLAUDE.md open decision 2). No FakeContentRepository or
    FakeTokenBlocklistRepository yet.

## Testing notes
- get_current_user tests: tests/test_auth_dependencies.py builds its own small FastAPI()
  app with one GET route that depends on get_current_user and returns the user. It
  overrides get_user_repository on that app with the conftest fake (the autouse fixture
  only overrides on src.main.app). No test-only route goes into src/.
- An expired token is built with jwt.encode and an exp in the past. Never time.sleep.
- Login posts form data: client.post("/login", data={"username": ..., "password": ...}).
- tests/test_database.py uses importlib.reload (see roadmap notes). If a database test
  breaks once conftest imports src.main, check this first.
- Existing Task 4 tests that monkeypatch JWT_SECRET_KEY must stay green with the
  conftest value set.

## Out of scope
- No /register, register_user or UserCreate/UserResponse (Task 9).
- No /users/me or change_password (Task 10).
- No /logout, TokenBlocklistRepository, revoked check or get_revoked_tokens_collection (Task 11).
- No require_admin (Task 12). No content routers in main.py (Task 7).
- No Protocol for the repositories (open decision 2).
- No load_dotenv() anywhere in src/. The server starts with --env-file.
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Existing tests unchanged and green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues
- [ ] New packages: none expected (python-multipart and httpx are already in requirements.txt)
- [ ] No .env or secrets in the diff
- [ ] Manual check (`uvicorn src.main:app --env-file .env --reload`): /docs shows POST /login as a form, and Try it out with any email and password returns 401 Invalid email or password (proves the real database connection). Logging in with a real user is checked in Task 9.
- [ ] After task4 merges: `git pull origin main --rebase`, tests still pass
- [ ] This brief is committed on task5/auth-service-and-login with the task
- [ ] PR opened with `gh pr create --base main --fill`
