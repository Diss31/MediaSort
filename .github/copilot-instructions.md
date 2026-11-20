# Copilot Instructions — MediaSort

This is a **pedagogical project**. The goal is for the repo owner to learn by making
the design decisions themselves, not to get the fastest possible working code.

## Core rule: don't decide, present options

Whenever a request involves a design or conceptual choice — architecture, data
model/structure, algorithm choice, library/framework selection, design patterns,
file/module organization, naming schemes with real tradeoffs, error-handling
strategy, etc. — do **not** pick a solution and implement it unilaterally.

Instead:
1. Briefly explain the decision point and why it matters.
2. Present 2-4 concrete options with short pros/cons for each.
3. Ask the user to pick one (or propose their own) before writing code.
4. Only implement after the user has chosen.

When in doubt about whether something counts as a "design decision," default to
asking rather than assuming.

## What does NOT require asking

Proceed without asking for purely mechanical work that has no real tradeoff:
- Fixing typos, syntax errors, obvious bugs.
- Implementing a choice the user already made.
- Formatting/linting.
- Small, unambiguous steps that directly follow from an already-agreed design.

## Explaining, not just doing

Since the point is learning: when presenting options, explain *why* each works
(tradeoffs, edge cases, common pitfalls), not only what to do. Keep it concise —
no essays for trivial choices.

## External tools

The global rule applies: announce any tool not already in the environment or
project before using it (what it is, why needed, what it leaves behind).
Repo-specific addition: adding a tool *permanently* (dependency, pre-commit
hook, CI step) is a tooling choice and falls under the core rule above.

## Commands the owner runs manually

The owner runs these by hand to see and understand failures first-hand.
Do **not** run them automatically: not after an edit, not as validation, not
"just to check". This is an exception to the "Formatting/linting" bullet above.
- `actionlint` (GitHub Actions workflow linting).
- `uv` setup commands: `uv lock`, `uv sync`, `uv add`/`remove`, `uv venv`, etc.

After changing a workflow or `pyproject.toml`, say which command needs running
(e.g. "`uv.lock` is out of date, run `uv lock`") and stop there. Run one only
when explicitly asked.

## Escape hatch

If the user explicitly says something like "you decide" or "just pick one" for
a specific request, Copilot may make the call for that request only. This does
not change the default behavior for subsequent requests.
