---
name: testing-conventions
description: How tests are written and organized in this project. Use when writing, changing or reviewing tests.
paths: tests/**
---
## Stand-ins by layer
- Routers: TODO (fake repository via dependency_overrides, fresh per test)
- Services: TODO (Mock() repository; check result AND the call)
- Repository: TODO (mock collection; check the exact query)
- Models: TODO (real objects, no stand-ins)

## Naming
TODO (test_<action>_<subject>[_<condition>], one file per module/router)

## Required tests for every endpoint
TODO: your table. At minimum:
- POST: valid → 201 with id; missing field → 422; invalid value → 422
- GET one: → 200; unknown id → 404; id of another content type → 404 (POST that item first)
- GET list: only this type; no _id in the response
- PATCH: → 200 + follow-up GET; unknown id → 404; invalid value → 422; empty body → "No changes made"
- DELETE: → 200 + follow-up GET is 404; unknown id → 404
- No token or bad token → 401
Each sad test changes ONE thing.

## Style
TODO: docstrings OR Arrange/Act/Assert comments. Pick one.

For a complete example of a router test file, see examples.md.