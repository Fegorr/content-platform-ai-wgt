# Content Publishing Platform (AI-built version)

## Project
TODO: what the app does + stack (FastAPI, MongoDB/pymongo, Pydantic v2, pytest, JWT)

## Architecture (required, not optional)
- Requests go Router → Service → Repository. Only repositories touch the database.
- TODO: models stay pure (no file reads, no DB calls)
- TODO: payload models (Create/Update) are flat and separate from domain models
- TODO: the server sets media_type, never the client
- TODO: connect to MongoDB inside get_collection(), never at import

## Commands
- Run tests: TODO
- Start the API: TODO

## Testing
- Tests never touch real MongoDB or real files. Use fakes/mocks.
- Follow the testing-conventions skill.

## Workflow
- TODO: branch naming, one PR per task, Maria reviews
- Never commit .env

## Compact instructions
When compacting, keep the list of changed files and the test command.