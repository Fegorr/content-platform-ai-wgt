# Chore: shared strip_mongo_id helper

Branch: chore/shared-strip-mongo-id

## Description
ContentRepository and UserRepository each have an identical private `_strip_mongo_id`.
Replace both with one shared function, `strip_mongo_id(document) -> dict`, in a new
module `src/db/mongo_utils.py`. This is a refactor: behaviour doesn't change, and the
existing repository tests stay unchanged and green. CLAUDE.md, the python-conventions
skill and the roadmap are updated to match.

## Input
- Built on task3/user-repository (PR #6, not merged yet). Rebase onto main once #6 is merged.
- Already exists: src/db/content_repository.py (ContentRepository._strip_mongo_id),
  src/db/user_repository.py (UserRepository._strip_mongo_id), tests/test_content_repository.py,
  tests/test_user_repository.py, the python-conventions skill (§1 cites ContentRepository._strip_mongo_id),
  docs/roadmap.md "Notes for later tasks" (entry "After task 3 (chore/shared-strip-mongo-id)").
- Does not exist yet: src/db/mongo_utils.py, tests/test_mongo_utils.py.
- Source of truth: CLAUDE.md "Architecture" (_id never leaves a repository) and the python-conventions skill.

## Output
- src/db/mongo_utils.py (new): strip_mongo_id(document) -> dict
- src/db/content_repository.py: use strip_mongo_id; remove _strip_mongo_id
- src/db/user_repository.py: use strip_mongo_id; remove _strip_mongo_id
- tests/test_mongo_utils.py (new)
- CLAUDE.md: "Where things live", add mongo_utils.py under src/db/
- .claude/skills/python-conventions/SKILL.md: §1 example
- docs/roadmap.md: remove this chore's entry from "Notes for later tasks"

## Roles involved
- test-writer: tests/test_mongo_utils.py
- test-runner: red check, then green check
- implementer: src/db/mongo_utils.py, src/db/content_repository.py, src/db/user_repository.py
- main session: CLAUDE.md, the python-conventions skill, docs/roadmap.md (docs only, no code)
- code-reviewer: reviews the diff

## Rules / behaviour
strip_mongo_id (`src/db/mongo_utils.py`)

1. `strip_mongo_id(document)` returns a dict with every key and value of `document` except `"_id"`.
2. It returns a new dict, not the object it received, even when `document` has no `"_id"` (result equal to the input, but `is not` the input).
3. It never changes the dict it receives: after the call, the input still has its `"_id"` and all its other keys.
4. An empty dict returns an empty dict.
5. Importing src.db.mongo_utils opens no connection and creates no client. It has no pymongo import (it only works on plain dicts). Test it in a subprocess, like the Task 1 purity test `test_import_models_without_database_or_http` in tests/test_models.py: run `import src.db.mongo_utils` with `sys.executable -c`, then assert `pymongo` is not in `sys.modules`. A subprocess is needed because other tests already import pymongo in the same pytest session.
6. The function has a one-line docstring (python-conventions §7). The code-reviewer checks this; there is no test for it.

Repositories (refactor, no behaviour change)

7. ContentRepository and UserRepository import and call `strip_mongo_id` from src.db.mongo_utils wherever they used `self._strip_mongo_id`.
8. Both private `_strip_mongo_id` static methods are removed. The code-reviewer checks this; there is no test for private names.
9. tests/test_content_repository.py and tests/test_user_repository.py are not changed and still pass.

Docs (main session)

10. CLAUDE.md "Where things live", `src/db/` line: add `mongo_utils.py (strip_mongo_id, shared by the repositories)`.
11. python-conventions skill §1: replace the "Good (`src/db/content_repository.py` `ContentRepository._strip_mongo_id`)" example with:
    Good (`src/db/mongo_utils.py` `strip_mongo_id`): the name says what is removed.
    ```python
    def strip_mongo_id(document: dict) -> dict:
        """Return a copy of the document without Mongo's _id."""
    ```
    The "Bad (before the conventions refactor)" `_clean` example stays as it is.
12. docs/roadmap.md: remove the "After task 3 (chore/shared-strip-mongo-id)" entry from "Notes for later tasks".

## Out of scope
- The "Chore (test cleanup)" roadmap entry (task 2 test rewrite and the task 3 test nits).
- Anything else in "Notes for later tasks".
- No other change to the repositories' behaviour, method names or signatures.
- No changes to existing tests.
- Never read, create or edit .env.

## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Existing tests unchanged and green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues (incl. both `_strip_mongo_id` copies gone and the docstring on `strip_mongo_id`)
- [ ] New packages added to requirements.txt (none expected)
- [ ] No .env or secrets in the diff
- [ ] PR opened with `gh pr create --base main` as soon as it's ready; the description says it includes PR #6's commits (and the chore/coding-conventions commits) until those PRs are merged
- [ ] After those merges: `git pull origin main --rebase`, tests still pass, push
