---
description: Run comprehensive verification on codebase. Checks build, types, lint, tests, and reports status.
---

# /au-verify Command

Run comprehensive verification on current codebase state.

## Instructions

Execute verification in this order:

1. **Build Check** - Run build command, report errors
2. **Type Check** - Run type checker, report errors with file:line
3. **Lint Check** - Run linter, report warnings/errors
4. **Test Suite** - Run tests, report pass/fail and coverage
5. **Debug Statement Audit** - Search for console.log/print
6. **Git Status** - Show uncommitted changes

## Verification Commands

<!-- REPO-CONTEXT-START -->
<!-- This section is replaced during scaffolding with repo-specific commands -->
<!-- Example for app-fe:
```bash
npm run build              # Build
npx tsc --noEmit           # Types
npx eslint .               # Lint
npm run test               # Tests
```
-->
<!-- Example for site-be:
```bash
python manage.py check     # Django check
mypy .                     # Types
ruff check .               # Lint
pytest --cov=.             # Tests
```
-->
<!-- REPO-CONTEXT-END -->

## Output Format

```
VERIFICATION: [PASS/FAIL]

Build:    [OK/FAIL]
Types:    [OK/X errors]
Lint:     [OK/X issues]
Tests:    [X/Y passed, Z% coverage]
Debug:    [OK/X found]

Ready for PR: [YES/NO]
```

If critical issues, list them with fix suggestions.

## Arguments

`/au-verify [mode]`

- `quick` - Only build + types
- `full` - All checks (default)
- `pre-commit` - Checks for commits
- `pre-pr` - Full + security scan

## When to Use

- Before committing
- Before creating PR
- After major changes
- When CI fails locally

## Related Commands

- `/au-review` - Code review
- `/au-fix` - Fix build errors
- `/au-checkpoint` - Save state
