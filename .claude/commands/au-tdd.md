---
description: Start Test-Driven Development workflow. Writes tests first, verifies they fail, then implements minimal code to pass. Enforces RED → GREEN → REFACTOR cycle.
---

# /au-tdd Command

This command invokes the **tdd-guide** agent to implement features using Test-Driven Development.

## What This Command Does

1. **Write Test First** (RED) - Create test for expected behavior
2. **Verify Failure** - Confirm test fails (proves it's testing something)
3. **Implement Minimally** (GREEN) - Write just enough code to pass
4. **Refactor** - Clean up while keeping tests green
5. **Repeat** - Continue for next behavior

## When to Use

Use `/au-tdd` when:
- Writing new features
- Fixing bugs (write test to reproduce first)
- Refactoring existing code
- Adding test coverage to untested code
- You want to ensure code correctness

## How It Works

The tdd-guide agent will:

1. **Clarify** the behavior to implement
2. **Write** a failing test first
3. **Run** the test to confirm it fails
4. **Implement** minimal code to pass
5. **Run** tests again to confirm pass
6. **Refactor** if needed, keeping tests green
7. **Repeat** for each behavior

## Example

```
User: /au-tdd Add a function to validate email addresses

Agent (tdd-guide):
## TDD Session: Email Validation

### Test 1: Valid email returns true

**1. RED - Write Test**
```typescript
test('should return true for valid email', () => {
  expect(isValidEmail('user@example.com')).toBe(true);
});
```

**2. Run → Expected FAIL**
```
ReferenceError: isValidEmail is not defined
```

**3. GREEN - Implement**
```typescript
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```

**4. Run → PASS** ✓

### Test 2: Invalid email returns false
...
```

## Usage Variations

```
/au-tdd                           # Start TDD for current task
/au-tdd "validate email"          # TDD for specific feature
/au-tdd --coverage                # Include coverage check after
```

## CRITICAL

- Tests are written BEFORE implementation
- Each test must fail before writing code
- Implementation should be minimal
- One behavior per test

## After TDD

- Use `/au-verify` to run full test suite
- Use `/au-review` to check code quality
- Use `/au-checkpoint` to save progress
