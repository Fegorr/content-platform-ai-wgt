---
name: testing-conventions
description: How tests are written and organized in this project. Use when writing, changing or reviewing tests.
paths: tests/**
---
## Stand-ins by layer
- Routers: `TestClient(app)` + the fake repositories in `tests/conftest.py`, plugged in with `app.dependency_overrides` by an autouse fixture. A fresh fake per test, cleared after. Log in with the `auth_headers` fixture. 
- Services: a `Mock()` repository. Check the return value AND the call (`assert_called_once_with(...)`). For "not found" and "forbidden" paths also check the write method was not called (`assert_not_called()`).
- Repository: a `Mock()` collection. Check the exact query (`find_one.assert_called_once_with({"id": "1"})`) and that `_id` is stripped from what comes back.
- Auth (hashing, jwt): real functions, no stand-ins. For an expired token, build one with `exp` in the past using the same secret.
- Models: real objects, no stand-ins.
- Never: real MongoDB, `.env`, files on disk, the network, `time.sleep`.

## Fakes in conftest.py
- `FakeContestRepository`, `FakeUserRepository` and `FakeTokenBlocklistRepository` have exactly the method names listed in CLAUDE.md.
- They store copies of dicts (`dict(document)`) so a test can't change stored data by accident.
- Three users, all in the fake user repo, passwords stored hashed:

| Fixture | id | name | email | password | role |
|---|---|---|---|---|---|
| `test_user` | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` | Louise | louise@test.com | louise_pass_1 | user |
| `other_user` | `b2c3d4e5-f6a7-8901-bcde-f12345678901` | Sylvie | sylvie@test.com | sylvie_pass_1 | user |
| `admin_user` | `c3d4e5f6-a7b8-9012-cdef-123456789012` | Ada | ada@test.com | ada_pass_123 | admin |

- Header fixtures: `auth_headers` (Louise), `other_auth_headers` (Sylvie), `admin_auth_headers` (Ada). Each is `{"Authorization": f"Bearer {create_access_token(user['id'])}"}`.
- Use `other_auth_headers` for ownership and privacy tests, `admin_auth_headers` for admin tests.

## Naming
- Files: `tests/test_<module>.py` for modules (`test_content_service.py`), `tests/test_<resource>.py` for routers (`test_videos.py`). One file per module or router.
- Tests: `test_<action>_<subject>[_<condition>]`
  - actions: `create`, `get`, `list`, `update`, `publish`, `delete`, `login`, ...
  - examples: `test_create_video`, `test_create_video_missing_title`, `test_get_video_wrong_type`, `test_update_video_empty_body`, `test_delete_video_without_token`
- Payload fixtures: `<type>_data` (e.g `video_data`), a valid create payload. Sad tests copy it and change ONE thing.

## Required tests for every endpoint
| Endpoint | Test | Expect |
|---|---|---|
| POST | valid payload | 201, body has `id`, `status == "draft"`, right `media_type`, `author_id` == test user id, the exact `preview` string, no `_id` |
| POST | client sends `media_type` / `author_id` / `status` | ignored: server values win |
| POST | missing required field | 422 |
| POST | invalid value (e.g. `duration` 0 or negative, bad `resolution`) | 422 |
| GET one | existing id | 200 + matching fields |
| GET one | unknown id | 404 |
| GET one | id of another content type (POST that item first) | 404 |
| GET one | another user's draft | 404 |
| GET one | another user's published item | 200 |
| GET one | my own item | `can_edit` and `can_delete` are true |
| GET one | another user's published item | `can_edit` and `can_delete` are false |
| GET one | another user's item, as admin | `can_edit` false, `can_delete` true |
| GET list | after posting this type AND another type | 200, only this type, no `_id` |
| GET list | nothing created | 200, `[]` |
| GET list | another user has a draft and a published item | only their published item appears, plus my own drafts |
| PATCH | valid change | 200 `"<Type> updated"` + follow-up GET shows the change and unchanged fields kept |
| PATCH | change a field the preview uses (e.g. `duration`) | follow-up GET shows the new `preview` |
| PATCH | `{"status": "published"}` | 200 + follow-up GET shows `published` |
| PATCH | unknown id | 404 |
| PATCH | invalid value | 422 |
| PATCH | invalid status (e.g. `"random"`) | 422 |
| PATCH | empty body `{}` | 200 `"No changes made"` |
| PATCH | another user's published item | 403 + follow-up GET shows it unchanged |
| PATCH | another user's draft | 404 |
| DELETE | existing id | 200 `"<Type> deleted"` + follow-up GET is 404 |
| DELETE | unknown id | 404 |
| DELETE | another user's published item | 403 + follow-up GET still 200 |
| DELETE | another user's draft | 404 |
| GET one | admin reads another user's draft | 200 |
| PATCH | admin edits another user's item | 403 + follow-up GET shows it unchanged |
| DELETE | admin deletes another user's published item | 200 + follow-up GET is 404 |
| DELETE | admin deletes another user's draft | 200 |
| every route | no token | 401 |
| every route | invalid token | 401 |
| every route | logged-out token | 401 |

## Required tests for auth
- `/register`: valid → 201 with id, name, email, `role == "user"` and NO `hashed_password`/`password`; then `/login` with those details works; client sends `"role": "admin"` → still created as `user`; email already used → 409; same email in different capitals → 409; invalid email → 422; password under 8 characters → 422; missing field → 422.
- `/logout`: valid → 200 `"Logged out"` and the same token then gets 401 on any route; a new login afterwards gives a token that works; no token → 401.
- `/users/me`: → 200 with the logged-in user (no `hashed_password`); no token → 401.
- `/users/me/password`: valid → 200 and the new password logs in, the old one doesn't; wrong current password → 400; new password same as old → 400; no token → 401.
- `/login`: correct credentials → 200 + `access_token` + `token_type == "bearer"`; wrong password → 401; unknown email → 401; missing field → 422.
- token: expired → 401; token for a user id that doesn't exist → 401.
- hashing: correct password verifies; wrong password doesn't; same password hashed twice gives different hashes.

## Required tests for admin
- `/admin/content` as admin: → 200 with items of every type from every user, drafts included, each with `preview` and no `_id`.
- `/admin/content` as a normal user → 403 `"Admin access required"`; no token → 401.
- `scripts/create_admin.py`: test the `create_admin(...)` function with a fake user repository: saves a user with role `admin` and a hashed password; email already used → returns None and saves nothing. Never test the terminal prompts.

## Required tests for models
- valid object; missing required field → `ValidationError`; each constraint in `docs/domain-spec.md` → one test.
- `get_preview()` exact string for each type.
- `publish()` / `unpublish()` change status; domain methods (`compress`, `append_text`) happy + sad paths.
- `User`: role defaults to `user`; an unknown role → `ValidationError`.

## Style
- Every test has a one-line docstring saying the behaviour in plain English ("Getting an image id from /videos returns 404.").
- No Arrange/Act/Assert comments. Keep tests short instead: build input, call once, assert.
- Use `pytest.raises(..., match="...")` when the message matters.
- Use `@pytest.mark.parametrize` for the 401 checks across routes.

For a complete example of a router test file (and the conftest it relies on), see examples.md.