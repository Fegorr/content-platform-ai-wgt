# Task brief template
 
Copy this for every task. The main session fills it in with you before any agent starts. The test-writer and implementer work only from this brief + CLAUDE.md + domain-spec.md.
 
```markdown
# TaskN: <short title>
 
Branch: taskN/<short-description>
 
## Description
What this task adds and why, in 2–4 sentences.
 
## Input
What already exists that this task builds on (files, classes, routes).
 
## Output
Files to create or change, with exact names:
- src/...
- tests/...
 
## Roles involved
- test-writer: writes tests/test_<...>.py
- test-runner: red check, then green check
- implementer: src/<...>
- code-reviewer: reviews the diff
 
## Rules / behaviour
Numbered list. Each rule should become at least one test.
1. ...
2. ...
 
## Out of scope
What NOT to do in this task.
 
## Acceptance criteria (check before asking Maria to review)
- [ ] All new tests were red first, then green
- [ ] Full suite passes: `pytest -q`
- [ ] code-reviewer: no blocking issues
- [ ] New packages added to requirements.txt
- [ ] No .env or secrets in the diff
- [ ] `git pull origin main --rebase` done, tests still pass
- [ ] PR opened with `gh pr create --base main --fill`
```
