---
description: Incrementally fix build and type errors. Uses build-resolver agent. Fixes one error at a time for safety.
---

# /au-fix Command

Incrementally fix TypeScript/build errors using the **build-resolver** agent.

## What This Command Does

1. Run build/type check
2. Parse error output, group by file
3. For each error:
   - Show error context
   - Explain the issue
   - Apply minimal fix
   - Re-run build
   - Verify error resolved
4. Report summary

## Build Commands

<!-- REPO-CONTEXT-START -->
<!-- This section is replaced during scaffolding with repo-specific commands -->
<!-- Example for app-fe:
```bash
npm run build              # Full build
npx tsc --noEmit           # Type check only
```
-->
<!-- Example for site-be:
```bash
mypy .                     # Type check
ruff check .               # Lint check
python manage.py check     # Django check
```
-->
<!-- REPO-CONTEXT-END -->

## Fix Strategy

### DO:
- Add type annotations
- Add null checks
- Fix imports
- Add missing dependencies

### DON'T:
- Refactor unrelated code
- Change architecture
- Add features
- Optimize performance

## Safety Checks

Stop if:
- Fix introduces new errors
- Same error persists after 3 attempts
- User requests pause

## Output Format

```
# Build Fix Report

**Initial Errors:** X
**Fixed:** Y
**Remaining:** Z

## Fixes Applied

1. [File:line] - Added type annotation
2. [File:line] - Fixed import path
...

## Verification
- Build: PASSING
- Types: PASSING
- New errors: 0
```

## When to Use

- Build fails
- Type errors blocking work
- CI failing with type/build errors
- After major refactoring

## Related Commands

- `/au-verify` - Check current state
- `/au-review` - Code review
- `/au-plan` - Plan larger fixes
