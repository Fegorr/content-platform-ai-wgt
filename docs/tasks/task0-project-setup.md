# Task0: Project setup

Branch: task0/project-setup

## Description
Set up the empty project skeleton so later tasks can be built with TDD: dependencies, pytest configuration, ignored files, an example env file, the `src/` package layout from CLAUDE.md "Where things live", and one smoke test that proves `pytest` runs green. No application code yet.

## Input
- Already exists: CLAUDE.md, docs/ (domain-spec.md, roadmap.md, task-template.md), .claude/ (agents, skills, settings.json), .gitignore (already lists .env, .venv/, __pycache__/, .pytest_cache/, CLAUDE.local.md, .claude/settings.local.json).
- Does not exist yet: src/, tests/, requirements.txt, pytest.ini, .env.example.

## Output
- requirements.txt
- pytest.ini
- .env.example
- .gitignore (only if something is missing; keep existing entries)
- src/__init__.py
- src/models/__init__.py
- src/schemas/__init__.py
- src/db/__init__.py
- src/services/__init__.py
- src/auth/__init__.py
- src/routers/__init__.py
- src/utils/__init__.py
- tests/test_smoke.py

## Roles involved
- test-writer: writes tests/test_smoke.py
- test-runner: red check, then green check
- implementer: requirements.txt, pytest.ini, .env.example, .gitignore, the src/ packages
- code-reviewer: reviews the diff

## Rules / behaviour
1. Each of these packages can be imported: `src`, `src.models`, `src.schemas`, `src.db`, `src.services`, `src.auth`, `src.routers`, `src.utils`. (Test this with one parametrized smoke test.)
2. All `__init__.py` files are empty. Importing them opens no network connection and reads no files.
3. pytest.ini is exactly:
   ```ini
   [pytest]
   pythonpath = .
   testpaths = tests
   ```
4. requirements.txt lists at least: fastapi, uvicorn[standard], pydantic[email], email-validator, pymongo, certifi, python-dotenv, PyJWT, pwdlib[argon2], python-multipart, pytest, httpx. One package per line.
5. .env.example holds names only, no real values:
   ```
   MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>/
   JWT_SECRET_KEY=<a long random string>
   ```
6. .env is git-ignored; .env.example is not. (Checked by hand with `git check-ignore`, not by a test: tests never touch real files.)

## Out of scope
- No src/main.py, config.py, models, schemas, repositories, services, routers or auth code.
- No tests/conftest.py yet (task 5 adds the fakes).
- No scripts/ folder (task 13).
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Full suite passes: `pytest -q`
- [ ] `git check-ignore .env` prints `.env`; `git check-ignore .env.example` prints nothing
- [ ] code-reviewer: no blocking issues
- [ ] New packages added to requirements.txt
- [ ] No .env or secrets in the diff
- [ ] `git pull origin main --rebase` done, tests still pass
- [ ] PR opened with `gh pr create --base main --fill`
