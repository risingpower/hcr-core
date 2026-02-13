---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring code. Enforces test-driven development methodology with comprehensive coverage.
---

# Test-Driven Development Workflow

This skill ensures all code development follows TDD principles with comprehensive test coverage.

## When to Activate

- Writing new features or functionality
- Fixing bugs (write test to reproduce first)
- Refactoring existing code
- Adding API endpoints
- Creating new components

## Core Principles

### 1. Tests BEFORE Code
ALWAYS write tests first, then implement code to make tests pass.

### 2. Coverage Requirements
- Target 80%+ coverage (unit + integration + E2E)
- All edge cases covered
- Error scenarios tested
- Boundary conditions verified

### 3. Test Types

**Unit Tests**
- Individual functions and utilities
- Component logic
- Pure functions
- Helpers and utilities

**Integration Tests**
- API endpoints
- Database operations
- Service interactions
- External API calls (mocked)

**E2E Tests (Playwright)**
- Critical user flows
- Complete workflows
- UI interactions
- Accessibility testing

## TDD Workflow Steps

### Step 1: Write Test First (RED)

Write a test that describes the expected behavior.

```
- Define the expected output for given inputs
- Test edge cases and error scenarios
- Use descriptive test names that explain intent
```

### Step 2: Run Test (Verify FAIL)

The test MUST fail initially.

```
- If test passes, it's testing nothing (or code already exists)
- Failure message should clearly indicate what's missing
- This proves the test is actually checking something
```

### Step 3: Minimal Implementation (GREEN)

Write ONLY enough code to make the test pass.

```
- Don't add features beyond what's tested
- Resist the urge to "improve" code before tests pass
- Hardcoding is acceptable temporarily
```

### Step 4: Run Test (Verify PASS)

The test must pass now.

```
- If still failing, fix the implementation
- Don't modify the test to make it pass
- All previous tests must still pass (regression)
```

### Step 5: Refactor (IMPROVE)

Clean up while keeping tests green.

```
- Remove duplication
- Improve naming
- Extract patterns
- Run tests after each refactor
```

### Step 6: Coverage Check

Verify coverage meets standards.

```
- Target: ≥80% code coverage
- Check branch coverage (all if/else paths)
- Ensure critical paths are tested
```

## Edge Cases to ALWAYS Test

### Inputs
- Null/undefined inputs
- Empty arrays/strings
- Invalid types
- Boundary values (0, -1, MAX_INT)

### States
- Loading states
- Error states
- Empty states
- Partial data states

### Operations
- Success scenarios
- Failure scenarios
- Timeout scenarios
- Concurrent operations

## Test Quality Guidelines

### Good Test Names

```typescript
// BAD: Vague name
test('handleSubmit')

// GOOD: Describes behavior
test('handleSubmit should show error when email is invalid')
test('handleSubmit should disable button during submission')
test('calculateTotal returns 0 for empty cart')
```

### Arrange-Act-Assert Pattern

```typescript
test('should calculate total with discount', () => {
  // Arrange - set up test data
  const items = [{ price: 100 }, { price: 50 }];
  const discount = 0.1;

  // Act - perform the action
  const total = calculateTotal(items, discount);

  // Assert - verify the result
  expect(total).toBe(135);
});
```

### Test Isolation

- Each test should be independent
- Tests should not share mutable state
- Use setup/teardown for common fixtures
- Mock external dependencies

## Testing Patterns by Language

### TypeScript/JavaScript (Vitest/Jest)

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component prop="value" />)
    expect(screen.getByText('value')).toBeInTheDocument()
  })

  it('handles click events', async () => {
    const handleClick = vi.fn()
    render(<Component onClick={handleClick} />)

    await fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledOnce()
  })
})
```

### Python (pytest)

```python
import pytest
from mymodule import calculate_total

class TestCalculateTotal:
    def test_returns_sum_of_prices(self):
        # Arrange
        items = [{"price": 100}, {"price": 50}]

        # Act
        result = calculate_total(items)

        # Assert
        assert result == 150

    def test_returns_zero_for_empty_list(self):
        assert calculate_total([]) == 0

    def test_raises_on_invalid_input(self):
        with pytest.raises(ValueError):
            calculate_total(None)
```

### E2E Tests (Playwright)

```typescript
import { test, expect } from '@playwright/test'

test('user can complete checkout flow', async ({ page }) => {
  // Navigate to product page
  await page.goto('/products/widget')

  // Add to cart
  await page.click('button:has-text("Add to Cart")')

  // Go to checkout
  await page.click('a[href="/checkout"]')

  // Fill form
  await page.fill('input[name="email"]', 'test@example.com')

  // Submit
  await page.click('button:has-text("Place Order")')

  // Verify success
  await expect(page.locator('h1')).toContainText('Order Confirmed')
})
```

## Mocking Strategies

### When to Mock

- External APIs (payment processors, third-party services)
- Database calls (for unit tests, not integration tests)
- Time-dependent operations
- Network requests
- File system operations

### When NOT to Mock

- The code you're testing
- Simple data transformations
- In integration tests (use real dependencies)

### Mock Example

```typescript
// Mock an API client
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ data: { user: { id: 1 } } }),
    post: vi.fn().mockResolvedValue({ data: { success: true } })
  }
}))

// Test with mock
test('fetches user data', async () => {
  const user = await getUser(1)
  expect(user.id).toBe(1)
})
```

## Common Testing Mistakes to Avoid

### ❌ Testing Implementation Details
```typescript
// BAD: Testing internal state
expect(component.state.count).toBe(5)
```

### ✅ Test User-Visible Behavior
```typescript
// GOOD: Test what users see
expect(screen.getByText('Count: 5')).toBeInTheDocument()
```

### ❌ Brittle Selectors
```typescript
// BAD: Breaks easily
await page.click('.css-class-xyz')
```

### ✅ Semantic Selectors
```typescript
// GOOD: Resilient to changes
await page.click('button:has-text("Submit")')
await page.click('[data-testid="submit-button"]')
```

### ❌ Dependent Tests
```typescript
// BAD: Tests depend on each other
test('creates user', () => { /* ... */ })
test('updates same user', () => { /* depends on previous test */ })
```

### ✅ Independent Tests
```typescript
// GOOD: Each test sets up its own data
test('creates user', () => {
  const user = createTestUser()
  // Test logic
})

test('updates user', () => {
  const user = createTestUser()
  // Update logic
})
```

## Continuous Testing

### Watch Mode During Development
```bash
npm test -- --watch   # Vitest/Jest
pytest --watch        # pytest-watch
```

### Pre-Commit Verification
```bash
npm run test && npm run lint && npm run typecheck
```

## Success Metrics

- 80%+ code coverage achieved
- All tests passing (green)
- No skipped or disabled tests without justification
- Fast unit test execution (< 50ms each)
- E2E tests cover critical user flows
- Accessibility tests included (axe-core)

---

**Remember**: Tests are not optional. They are the safety net that enables confident refactoring, rapid development, and production reliability. Write the test first.
