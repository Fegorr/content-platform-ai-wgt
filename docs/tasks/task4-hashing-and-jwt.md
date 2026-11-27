# Task4: JWT secret, password hashing and tokens

Branch: task4/hashing-and-jwt

## Description
Add the JWT secret to config, password hashing with pwdlib, and creating and
checking access tokens with PyJWT. Pure functions only: no routes, no services,
no database.

## Input
- On main: src/config.py (get_mongodb_uri), src/auth/__init__.py, the
  python-conventions skill. PyJWT and pwdlib[argon2] are in requirements.txt.
- Source of truth: CLAUDE.md "Auth" (token payload, 30 minutes, HS256) and
  docs/domain-spec.md "Auth helpers" (function names, signatures, return types,
  constants). If this brief and the domain spec disagree, the domain spec wins.

## Output
- src/config.py: add get_jwt_secret_key()        ← implementer
- src/auth/hashing.py                             ← implementer
- src/auth/jwt.py                                 ← implementer
- tests/test_config.py: add tests                 ← test-writer
- tests/test_hashing.py                           ← test-writer
- tests/test_jwt.py                               ← test-writer

## Roles involved
- test-writer, test-runner (red, then green), implementer, code-reviewer

## Rules / behaviour
Signatures are in docs/domain-spec.md "Auth helpers". Every public function has
a one-line docstring (python-conventions §7).

Config
1. get_jwt_secret_key() returns os.environ["JWT_SECRET_KEY"], read when called
   (a changed value is picked up by the next call).
2. If JWT_SECRET_KEY is missing or an empty string, it raises
   RuntimeError("JWT_SECRET_KEY is not set"). An empty key would let anyone
   forge tokens. get_mongodb_uri stays as it is.
3. Importing src.config works without JWT_SECRET_KEY set.

Hashing (src/auth/hashing.py)
4. hash_password(password) returns an argon2 hash (starts with "$argon2") that
   is not the plain password.
5. Hashing the same password twice gives two different hashes.
6. verify_password(password, hashed_password) returns True for the right
   password and False for a wrong one.
7. verify_password returns False, never raises, when the stored hash is
   malformed: "not-a-hash" and "" (empty string).

Tokens (src/auth/jwt.py)
8. ACCESS_TOKEN_EXPIRE_MINUTES = 30 and ALGORITHM = "HS256" are module constants.
9. create_access_token(user_id) returns a token whose payload has exactly the
   keys sub, jti and exp, and no others (no iat):
   - sub = user_id
   - jti = a new UUID string (uuid.UUID(jti) parses it)
   - exp = now (UTC) + 30 minutes
10. Two tokens for the same user have different jti values.
11. The secret is read from config.get_jwt_secret_key() when a token is created
    or decoded, never at import:
    - importing src.auth.jwt works without JWT_SECRET_KEY set
    - a token created under secret A, decoded after JWT_SECRET_KEY changes to
      secret B, returns None
12. decode_access_token(token) returns the payload dict for a valid token,
    decoded with algorithms=[ALGORITHM] (a list). A token signed with the same
    secret but a different algorithm (HS512) returns None.
13. decode_access_token requires sub, jti and exp
    (options={"require": ["sub", "jti", "exp"]}), not with manual key checks.
14. decode_access_token returns None, never raises, for: an expired token, a
    token signed with another secret, a malformed string, and a token missing
    sub, a token missing jti, a token missing exp (one test each). Only PyJWT
    errors (jwt.PyJWTError) are caught.
15. A missing or empty JWT_SECRET_KEY still raises RuntimeError from both
    create_access_token and decode_access_token. That is a server
    misconfiguration, not an invalid token, so it must not turn into None.

## Testing notes
- There is no tests/conftest.py yet (it comes in Task 5). Each test sets
  JWT_SECRET_KEY itself with monkeypatch, at least 32 characters long. Never .env.
- An expired token, a token missing a claim, and an HS512 token are built
  directly with jwt.encode. Never time.sleep.
- exp check: the decoded exp is within a few seconds of
  now(UTC) + 30 minutes. Don't compare exactly.

## Out of scope
- No AuthService, get_current_user, /login or /logout (Tasks 5 and 11).
- No token blocklist check (Task 11); jti is only created here.
- No load_dotenv().
- No change to get_mongodb_uri.

## Acceptance criteria
- [ ] New tests were red first, then green
- [ ] Full suite passes: pytest -q
- [ ] code-reviewer: no blocking issues
- [ ] New packages: none (PyJWT and pwdlib[argon2] are already in requirements.txt)
- [ ] No .env or secrets in the diff
- [ ] git pull origin main --rebase done, tests still pass
- [ ] This brief is committed on task4/hashing-and-jwt with the task
- [ ] I can explain every changed file in my own words
- [ ] PR opened with gh pr create --base main --fill
