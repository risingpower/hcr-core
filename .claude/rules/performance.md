# Performance Guidelines

## Model Selection Strategy

**Haiku** (Fast, cost-effective):
- Lightweight agents with frequent invocation
- Simple code generation
- Worker agents in multi-agent systems

**Sonnet** (Balanced):
- Main development work
- Complex coding tasks
- Default choice

**Opus** (Deep reasoning):
- Complex architectural decisions
- Research and analysis
- Planning complex features

## Context Window Management

### Avoid Last 20% of Context for:
- Large-scale refactoring
- Multi-file feature implementation
- Complex debugging

### Lower Context Sensitivity:
- Single-file edits
- Utility creation
- Documentation
- Simple bug fixes

## Token Optimization

1. **Use subagents** - Delegate to specialized agents
2. **Compact early** - Don't wait until context is full
3. **Checkpoints** - Save state before major operations
4. **Background tasks** - Run long operations in background

## Build Performance

### Python Performance
```bash
# Clear caches
rm -rf __pycache__ .mypy_cache .pytest_cache .ruff_cache
```

## If Build Fails

1. Use `build-resolver` agent
2. Fix one error at a time
3. Verify after each fix
4. Track progress (X/Y fixed)

## Database Performance (Backend)

### Avoid N+1 Queries
```python
# BAD: N+1 query
for user in User.objects.all():
    print(user.profile.name)

# GOOD: Prefetch
for user in User.objects.select_related('profile').all():
    print(user.profile.name)
```

## React Performance (Frontend)

### Memoization
```typescript
// Memoize expensive calculations
const result = useMemo(() => expensiveCalc(data), [data])

// Memoize callbacks
const handleClick = useCallback(() => {...}, [deps])
```

### Avoid Re-renders
- Don't create objects/arrays inline in JSX
- Use stable references for callbacks
- Split large components
