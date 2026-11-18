Create a new skill at .claude/skills/python-conventions/SKILL.md, for writing and reviewing Python code in this project. Sections, each with short rules and one good and one bad example taken from our codebase:
1. Naming: PEP 8 (PascalCase classes, snake_case functions and variables, UPPER_CASE constants and enum members, is_/has_/can_ for booleans). Names must say what they do without needing the docstring.
2. Classes and accessibility: one job per class; public methods have no underscore; internal helpers start with _; no double-underscore names unless needed for subclass clashes; @property for read-only computed values.
3. Enums: str + Enum, UPPER_CASE members, lowercase values matching stored data; compare with members, never with typed strings.
4. Interfaces: ABC with @abstractmethod for base classes; typing.Protocol for contracts like repositories, so fakes and real classes share one contract.
5. Polymorphism: call the shared method instead of checking types with isinstance; use a registry instead of if/elif chains; subclasses keep the base method's arguments and return type.
6. Data types and mutability: prefer immutable types (tuple, frozenset, str) for values that never change; never use a mutable default argument; copy a dict or list before passing it to code that may change it; explain any mutable choice with a comment.
7. Comments: a docstring on every public class and method; comments explain why, not what.

Also: add python-conventions to the skills list of the implementer, test-writer and code-reviewer agents; add a code-reviewer checklist item "code follows the python-conventions skill"; and add one line to CLAUDE.md: "Follow the python-conventions skill for naming, OOP, data types and comments." Show me the plan before writing.

## Scope added later
Decided with the user during this chore:
- Skill decisions: an override that keeps the base method's meaning may skip its docstring; special methods (`__init__`, `__eq__` and so on) are exempt from the docstring rule; a subclass may narrow a field's type (e.g. `media_type: Literal[MediaType.VIDEO]`); `Member.value` when turning an enum member into text; "split the class" only when its docstring joins two jobs with "and".
- Skill examples cite a file and a name instead of line numbers; fixed code is used as the good example and the old form is labelled "(before the conventions refactor)". Where the codebase has no example, a made-up one is used, labelled "(example, not from our code)".
- More skill rules: use `Member.value` in database queries; methods named in CLAUDE.md or the domain spec (`get_preview`, `compress`, `append_text`) stay methods rather than becoming `@property`; the docstring rule covers public classes, methods and functions.
- code-reviewer.md: besides the checklist item, a break of the python-conventions skill is ranked "should fix", not blocking, and the skill is described as project rules, not style nitpicks, so breaks are always reported.
- code-reviewer listed the violations in src/; these were fixed as a refactor (no behaviour change, tests unchanged):
  - src/db/content_repository.py: `_collection`, `_strip_mongo_id`, `ContentStatus.PUBLISHED.value`, docstrings on public methods
  - src/models/content.py: docstrings on the enums, `publish()`, `unpublish()` and the four content classes
  - src/models/registry.py: `CONTENT_TYPES` is a `MappingProxyType` keyed by `MediaType` members
  - src/models/user.py: docstrings on `UserRole`, `User`, `lowercase_email`; return type `"User"`
  - src/db/database.py: `get_content_collection` returns `Collection`
- CLAUDE.md Stack line: the minimum Python version is now recorded as Python 3.11+.
- docs/roadmap.md "Notes for later tasks": the compress rename note, the Task 6 `CONTENT_TYPES` annotation note and the Task 16 CI note.
- Left out on purpose: the repository Protocol (comes with the test fake in Task 5), changing the `list_visible` signature, a `width`/`height` property.
