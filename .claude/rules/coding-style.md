# Coding Style Guidelines

## Core Principles

1. **Consistency over preference** - Match existing patterns in the codebase
2. **Clarity over cleverness** - Write code others can understand
3. **Minimal changes** - Don't refactor beyond what's needed for the task
4. **No over-engineering** - Solve the current problem, not hypothetical ones
5. **Fail fast, not silently** - Errors should surface so we can fix them

## What NOT to Do

### Don't Add Unnecessary Complexity
```typescript
// BAD: Premature abstraction
const configFactory = createConfigFactoryBuilder().withDefaults().build();

// GOOD: Direct and clear
const config = { timeout: 5000, retries: 3 };
```

### Don't Add Unrequested Features
```typescript
// BAD: Adding "nice to have" features
function saveUser(user) {
  validateEmail(user.email);     // Not requested
  sanitizeInput(user.name);      // Not requested
  logAnalytics('user_saved');    // Not requested
  return db.save(user);
}

// GOOD: Just what was asked
function saveUser(user) {
  return db.save(user);
}
```

### Don't Add Backwards Compatibility Hacks
```typescript
// BAD: Keeping unused code "just in case"
const oldConfig = {}; // deprecated, keeping for backwards compat
const _unusedHelper = () => {}; // might need later

// GOOD: Delete unused code
// (nothing - just delete it)
```

### Don't Build Silent Fallbacks

**We want to know when something breaks so we can fix it.** Never add fallbacks that silently handle errors or mask failures.

```typescript
// BAD: Silent fallback masks the real problem
function getUser(id) {
  try {
    return await api.getUser(id);
  } catch (error) {
    return null;  // Caller has no idea something went wrong
  }
}

// BAD: Default value hides missing data
const userName = user?.name || 'Unknown User';  // Why is name missing?

// BAD: Optional chaining that masks bugs
const price = product?.pricing?.amount ?? 0;  // Should pricing always exist?

// GOOD: Let errors surface
function getUser(id) {
  return await api.getUser(id);  // Caller handles error appropriately
}

// GOOD: Explicit error for unexpected state
if (!user.name) {
  throw new Error(`User ${user.id} missing required name field`);
}

// GOOD: Validate assumptions explicitly
if (!product.pricing) {
  throw new Error(`Product ${product.id} has no pricing configured`);
}
const price = product.pricing.amount;
```

**When fallbacks ARE appropriate:**
- User-facing display (show "N/A" rather than crash the UI)
- External data you don't control (third-party APIs)
- Explicitly documented optional fields

**When fallbacks are NOT appropriate:**
- Internal data that should always exist
- Required fields in your own models
- State that indicates a bug if missing

## Naming Conventions

### Variables and Functions
- Use descriptive names that explain purpose
- Avoid abbreviations unless widely known (e.g., `id`, `url`)
- Boolean variables: use `is`, `has`, `should` prefixes

```typescript
// BAD
const d = new Date();
const usr = getUsr();
const flag = true;

// GOOD
const createdAt = new Date();
const currentUser = getCurrentUser();
const isAuthenticated = true;
```

### Files and Directories
- Use kebab-case for files: `user-profile.tsx`
- Match existing project conventions
- Group related files in directories

## Code Organization

### Function Length
- Prefer functions under 50 lines
- Extract helper functions for complex logic
- Single responsibility per function

### File Length
- Prefer files under 300 lines
- Split large files into logical modules
- Keep related code together

### Nesting Depth
- Maximum 3-4 levels of nesting
- Use early returns to reduce nesting
- Extract complex conditions into named variables

```typescript
// BAD: Deep nesting
if (user) {
  if (user.isActive) {
    if (user.hasPermission('edit')) {
      if (resource.isEditable) {
        // actual logic
      }
    }
  }
}

// GOOD: Early returns
if (!user) return;
if (!user.isActive) return;
if (!user.hasPermission('edit')) return;
if (!resource.isEditable) return;
// actual logic
```

## Comments

### When to Comment
- Complex business logic that isn't obvious
- Non-obvious performance optimizations
- Workarounds with links to issues/tickets

### When NOT to Comment
- Self-explanatory code
- Code you didn't modify
- Removed code (just delete it)

```typescript
// BAD: Obvious comment
// increment counter
counter++;

// BAD: Commented-out code
// const oldImplementation = () => { ... }

// GOOD: Explains why, not what
// Using setTimeout instead of requestAnimationFrame for Safari compatibility
// See: https://bugs.webkit.org/show_bug.cgi?id=12345
setTimeout(animate, 16);
```

## Project-Specific Style

<!-- REPO-CONTEXT-START -->
<!-- This section is replaced during scaffolding with repo-specific content -->
<!-- Example for app-fe:
### Frontend Style
- Use `cn()` utility for class merging
- Use `cva` for component variants
- Prefer named exports over default
- Use `@/` path aliases
-->
<!-- Example for site-be:
### Django Style
- Use services layer for business logic
- Use logging module, not print()
- Type hints on all public functions
-->
<!-- REPO-CONTEXT-END -->

**See also:** `design-system.md` for color tokens, card standards, and component patterns (frontend repos only).

## Format and Lint

Always run formatters before committing:
- Let automated tools handle formatting
- Don't manually adjust formatted code
- Fix lint errors, don't disable rules
