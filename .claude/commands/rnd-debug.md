---
description: Invoke hierarchical debugging protocol for R&D projects. Works through 5 levels systematically: Pattern → Variant → Context → Domain → Edge Case.
---

# /rnd-debug Command

Start the R&D debugging protocol when stuck on a problem. Systematically escalates through knowledge levels.

## What This Command Does

1. **Level 1: Pattern** - Check if known pattern handling applies
2. **Level 2: Variant** - Check if this is a known subtype
3. **Level 3: Context** - Check for environmental factors
4. **Level 4: Domain** - Check for platform-specific behavior
5. **Level 5: Edge Case** - Document if truly unique

## When to Use

Use `/rnd-debug` when:
- Standard approach isn't working
- Unexpected behavior encountered
- You've tried the obvious solutions
- Need systematic problem analysis
- Want to avoid random debugging

## The Five Levels

### Level 1: Pattern
- What known pattern does this match?
- Read `knowledge/patterns/{pattern}/handling.md`
- Does standard handling apply?

### Level 2: Variant
- Is this a known subtype?
- Check `knowledge/patterns/{pattern}/variants/`
- Apply variant-specific handling if found

### Level 3: Context
- What environmental factors are present?
- Read `knowledge/contexts/{context}/effects.md`
- Check for pattern × context interaction rules

### Level 4: Domain
- Are there platform/framework specifics?
- Read `knowledge/domains/{domain}/constraints.md`
- Check for domain-specific overrides

### Level 5: Edge Case
- Is this truly unique?
- Document in `knowledge/edge-cases/`
- Flag for review: might be undiscovered pattern

## How It Works

The command will:

1. **Capture** the current problem state
2. **Search** `_taxonomy.yaml` for relevant patterns
3. **Escalate** through levels until solution found
4. **Document** what level resolved it
5. **Suggest** `/au-learn` if new knowledge discovered

## Example

```
User: /rnd-debug "toggle not being detected"

Agent:
## Debugging: Toggle Detection Failure

### Level 1: Pattern Check
**Pattern:** toggle
**Standard Handling:** Click and verify state change

Reading `knowledge/patterns/toggle/handling.md`...
- Check for `checkable` attribute ✓
- Verify clickable bounds ✓
- Standard handling should work...

**Result:** Standard handling not resolving issue.

### Level 2: Variant Check
Checking `knowledge/patterns/toggle/variants/`...
- checkbox-toggle: No (not a checkbox)
- switch-toggle: No (not a switch)
- **toolbar-toggle: POSSIBLE** (element is in toolbar)

Reading `knowledge/patterns/toggle/variants/toolbar-toggle.md`...
- Toolbar toggles use `state_checked` attribute
- Don't rely on class name changes

**Result:** This appears to be a toolbar-toggle variant!

### Recommended Action
Use explicit `checked` attribute detection:
```python
is_checked = node.attributes.get('checked') == 'true'
```

### Resolution
**Level:** 2 (Variant)
**Pattern:** toggle/toolbar-toggle
**Fix:** Use checked attribute instead of class name

---

**New learning?** Use `/au-learn` to document if this reveals something new.
```

## Usage Variations

```
/rnd-debug                        # Start debugging current issue
/rnd-debug "description"          # Start with context
/rnd-debug --level=3              # Start at specific level
/rnd-debug --pattern=toggle       # Focus on specific pattern
```

## Debugging Escalation Rules

| If Level N fails... | Then... |
|---------------------|---------|
| Level 1 (Pattern) | Check variants (Level 2) |
| Level 2 (Variant) | Check context effects (Level 3) |
| Level 3 (Context) | Check domain constraints (Level 4) |
| Level 4 (Domain) | Document as edge case (Level 5) |
| Level 5 (Edge Case) | Flag for pattern review |

## CRITICAL

- **Don't skip levels** - Systematic escalation prevents missed solutions
- **Document resolution level** - Helps calibrate future debugging
- **Consider `/au-learn`** - If resolution reveals new knowledge
- This command is for R&D projects only

## After Resolution

- Use `/au-learn` if new pattern/variant/context discovered
- Update `_state.yaml` with debugging outcome
- Consider if related patterns need updating
