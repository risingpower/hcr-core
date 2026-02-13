# Testing Requirements

## Coverage Target: 80%

Test types required:
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows

## Test Commands

### Test Commands
```bash
pytest                    # All tests
pytest -v                 # Verbose output
pytest -x                 # Stop on first failure
pytest -k "test_*"        # Run specific tests
pytest --cov=hcr_core --cov-report=html  # Coverage report
```

## Test-Driven Development (TDD)

**For new features, start with `/au-tdd` to write tests first.**

MANDATORY workflow for new features:

1. **RED** - Write test first, run it, it should FAIL
2. **GREEN** - Write minimal implementation to pass
3. **IMPROVE** - Refactor while keeping tests green
4. **VERIFY** - Check coverage (80%+)

```
[Write Test] → [Run: FAIL] → [Write Code] → [Run: PASS] → [Refactor] → [Run: PASS]
```

The `/au-tdd` command invokes the tdd-guide agent to enforce this workflow.

## Accessibility Testing (Frontend Only)

Products must be **WCAG 2.1 AA compliant**.

### Test Commands
```bash
pytest                    # All tests
pytest -v                 # Verbose output
pytest -x                 # Stop on first failure
pytest -k "test_*"        # Run specific tests
pytest --cov=hcr_core --cov-report=html  # Coverage report
```

## After Code Changes

**Run `/au-verify` after significant code changes.**

This runs the full verification suite: build, types, lint, and tests.

## Troubleshooting Test Failures

1. Check test isolation (tests affecting each other)
2. Verify mocks are correct
3. Fix implementation, not tests (unless tests are wrong)
4. Use `--verbose` flag for more details

## Test File Organization

```
# Python projects
tests/
├── unit/
├── integration/
└── e2e/

# Next.js projects
__tests__/
├── components/
├── hooks/
└── utils/

e2e/
├── auth.spec.ts
└── checkout.spec.ts
```
