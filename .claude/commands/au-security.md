---
description: Run security vulnerability review on code. Checks for OWASP Top 10 issues, auth flaws, injection risks. READ-ONLY - reports findings without modifying code.
---

# /au-security Command

This command invokes the **security-reviewer** agent to scan code for vulnerabilities.

## What This Command Does

1. **Scope Assessment** - Identify files to review (changed or specified)
2. **Risk Classification** - Categorize files by risk level
3. **Vulnerability Scan** - Check for security issues
4. **Report Generation** - Produce detailed findings report
5. **Recommendation** - BLOCK, APPROVE WITH CHANGES, or APPROVE

## When to Use

Use `/au-security` when:
- After writing code that handles user input
- After implementing authentication/authorization
- After creating API endpoints
- After handling sensitive data (PII, payments, credentials)
- Before any production deployment
- After adding third-party integrations

## How It Works

The security-reviewer agent will:

1. **Identify** changed files or review specified scope
2. **Classify** risk level of each file
3. **Scan** for vulnerabilities by category:
   - CRITICAL: Secrets, injection, auth flaws
   - HIGH: Input validation, CSRF, rate limiting
   - MEDIUM: Headers, logging, dependencies
4. **Generate** detailed report with findings
5. **Provide** recommendation and remediation steps

## Example

```
User: /au-security

Agent (security-reviewer):
## Security Review Report

**Date:** 2026-01-24
**Files Reviewed:** 3
**Risk Level:** 🟡 MEDIUM

---

### Critical Issues (0)
None found.

### High Issues (1)

#### [HIGH-001] Missing rate limiting on login
- **File:** `app/api/auth/route.ts:15`
- **Type:** Brute Force Risk
- **Description:** Login endpoint has no rate limiting
- **Impact:** Attackers could brute-force credentials
- **Recommendation:** Add rate limiting middleware

### Medium Issues (2)
...

---

**RECOMMENDATION:** `APPROVE WITH CHANGES`

**Action Required:** Add rate limiting before merge
```

## Usage Variations

```
/au-security                      # Review changed files
/au-security auth/                # Review specific directory
/au-security --scope=api          # Review API endpoints only
```

## Security Checklist

### CRITICAL (Block PR)
- [ ] No hardcoded secrets
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Auth on protected routes
- [ ] Authorization checks

### HIGH (Fix Before Merge)
- [ ] Input validation
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Safe error handling

## CRITICAL

- This command is READ-ONLY - it reports findings but does not fix them
- Fix issues manually or ask for help with specific fixes
- Re-run `/au-security` after fixing to verify

## After Security Review

- Fix reported issues
- Re-run `/au-security` to verify fixes
- Use `/au-review` for general code quality
- Use `/au-verify` to run full verification
