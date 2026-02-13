# Security Guidelines

## Sensitive Code Review

**After editing auth, API, or user-input handling code, run `/au-security`.**

This invokes the security-reviewer agent to scan for vulnerabilities (read-only, reports only).

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Error messages don't leak sensitive data

## CRITICAL: Never Commit These

```
# Patterns to block
*.pem
*.key
.env
.env.local
credentials.json
*_SECRET*
*_API_KEY*
```

## Secret Management

```typescript
// NEVER: Hardcoded secrets
const apiKey = "sk-proj-xxxxx"

// ALWAYS: Environment variables
const apiKey = process.env.API_KEY
if (!apiKey) {
  throw new Error('API_KEY not configured')
}
```

## Project-Specific Security Rules

### Python Security
- Bare `except:`: ALWAYS specify exception type
- No customer data in research datasets
- API keys from environment variables only

### Secret Management
```python
# API keys from environment only
import os
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
```

## Error Handling

### Fail Fast, Don't Mask Errors

Errors should surface so we can fix them. Never silently swallow exceptions.

```python
# BAD: Silently swallows all errors
try:
    process_payment()
except:
    pass

# BAD: Generic fallback hides the real problem
try:
    result = api.call()
except Exception:
    result = default_value  # What went wrong? We'll never know

# GOOD: Let errors propagate (caller decides how to handle)
result = api.call()

# GOOD: Catch specific exceptions, log and re-raise
try:
    process_payment()
except stripe.error.CardError as e:
    logger.error(f"Payment failed: {e.user_message}")
    raise  # Re-raise so caller knows it failed

# GOOD: Transform to domain exception with context
try:
    user = db.get_user(id)
except DatabaseError as e:
    raise UserNotFoundError(f"Failed to fetch user {id}") from e
```

### Error Messages: Surface Errors, Not Secrets

Errors should be visible but not leak sensitive data.

```python
# BAD: Leaks internal details
raise Exception(f"Database query failed: {sql_query}")

# BAD: Silent failure (we won't know it's broken)
return None

# GOOD: Informative but safe
raise Exception(f"Failed to fetch user {user_id}")
```

## Security Response Protocol

If security issue found:
1. **STOP** immediately
2. Use `code-reviewer` agent for full audit
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues

## Universal Constraint

**No AI/ML in compliance decisions** - We provide tools, humans make compliance judgments. Never automate compliance verdicts.
