---
description: Extract and document learnings from current session. Captures patterns, fixes, and constraints for future reference. R&D projects only.
---

# /au-learn Command

Extract reusable knowledge from the current session and document it in the knowledge taxonomy.

## What This Command Does

1. **Analyze Session** - Review what was debugged/solved
2. **Identify Type** - Classify the learning (pattern, variant, context, domain, constraint)
3. **Determine Location** - Find where it belongs in taxonomy
4. **Draft Documentation** - Create the knowledge document
5. **Confirm with User** - Ask for approval before saving
6. **Update Taxonomy** - Add to `_taxonomy.yaml` and relevant files

## When to Use

Use `/au-learn` when:
- You've solved a non-trivial debugging problem
- You've discovered a new pattern or behavior
- A workaround was needed for something unexpected
- User corrected your approach (valuable learning)
- You found a platform/framework quirk

## What to Extract

| Type | When | Example |
|------|------|---------|
| **Pattern** | New recurring phenomenon | "Toggle elements need special click handling" |
| **Variant** | New subtype of existing pattern | "Toolbar toggles behave differently than menu toggles" |
| **Context** | How environment affects patterns | "Scrollable containers affect element detection" |
| **Domain** | Platform-specific behavior | "Compose UI requires different selectors" |
| **Constraint** | Rule that must be followed | "Never use coordinates in LLM prompts" |

## How It Works

The command will:

1. **Summarize** what was learned in the session
2. **Classify** the type of learning
3. **Find** or create the appropriate location in `docs/knowledge/`
4. **Draft** the documentation with:
   - Definition/description
   - Identification criteria
   - Handling approach
   - Examples
5. **Ask** for confirmation
6. **Update** `_taxonomy.yaml` and create/update files

## Example

```
User: /au-learn "fixed toggle detection in toolbar"

Agent:
## Learning Extraction

### What Was Learned
Toggle elements in toolbars require explicit checked state detection
rather than relying on class name changes.

### Classification
**Type:** Variant
**Parent Pattern:** toggle
**Variant Name:** toolbar-toggle

### Proposed Documentation

**File:** `docs/knowledge/patterns/toggle/variants/toolbar-toggle.md`

```markdown
# Toolbar Toggle Variant

## Distinguishing Characteristics
- Parent container is a toolbar (ActionBar, Toolbar class)
- Uses `android:state_checked` attribute
- Class name doesn't change on toggle

## Handling
1. Check for `checked` attribute explicitly
2. Don't rely on class name changes
3. May need to check parent context first
```

**Confirm?** (yes/no/modify)
```

## Output Locations

| Type | Location |
|------|----------|
| Pattern | `docs/knowledge/patterns/{id}/` |
| Variant | `docs/knowledge/patterns/{id}/variants/` |
| Context | `docs/knowledge/contexts/{id}/` |
| Domain | `docs/knowledge/domains/{id}/` |
| Edge Case | `docs/knowledge/edge-cases/` |

## Usage Variations

```
/au-learn                         # Extract from current session
/au-learn "context hint"          # Extract with guidance
/au-learn --type=pattern          # Force classification type
```

## Rules

- **Don't extract trivial fixes** - Must save future time
- **Don't extract one-time issues** - Must be recurring
- **Keep focused** - One concept per extraction
- **Include examples** - Real cases help future use

## CRITICAL

- Always ask for confirmation before saving
- Update `_taxonomy.yaml` when adding new entries
- Cross-reference related patterns/contexts
- This command is for R&D projects only

## After Learning

- Knowledge is now available for `/rnd-debug` lookups
- Consider if related patterns need updating
- Update `hypotheses.md` if beliefs changed
