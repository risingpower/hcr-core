---
description: Run code review on uncommitted changes. Checks security, quality, and best practices. Reports issues by severity.
---

# /au-review Command

Comprehensive security and quality review of uncommitted changes.

## What This Command Does

1. Get changed files: `git diff --name-only HEAD`
2. Review each file for issues
3. Generate report by severity
4. Provide verdict: APPROVE / WARNING / BLOCK

## Checks Performed

### Security (CRITICAL)
- Hardcoded credentials, API keys, tokens
- SQL injection vulnerabilities
- XSS vulnerabilities
- Missing input validation
- Insecure patterns

### Code Quality (HIGH)
- Functions > 50 lines
- Files > 800 lines
- Nesting > 4 levels
- Missing error handling
- Debug statements (console.log, print)
- TODO/FIXME without tickets

### Best Practices (MEDIUM)
- Missing documentation for public APIs
- Accessibility issues
- Poor variable naming
- Magic numbers
- Missing tests for new code

## Output Format

```
## Code Review Summary

**Files Reviewed:** X
**Issues Found:** Y

### CRITICAL (X)
- [Issue with file:line and fix]

### HIGH (X)
- [Issue with file:line and fix]

### MEDIUM (X)
- [Issue with file:line and fix]

**Verdict:** APPROVE / WARNING / BLOCK
```

## Verdict Criteria

- **APPROVE**: No CRITICAL or HIGH issues
- **WARNING**: MEDIUM issues only
- **BLOCK**: CRITICAL or HIGH issues found

## When to Use

- Before committing changes
- After implementing a feature
- Before creating a PR
- When requested by team

## Related Commands

- `/au-plan` - Plan before implementing
- `/au-verify` - Run build/test verification
- `/au-fix` - Fix build errors
