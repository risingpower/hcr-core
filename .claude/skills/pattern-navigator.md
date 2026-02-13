---
name: pattern-navigator
description: Navigate the knowledge taxonomy to find relevant patterns, variants, and context interactions during debugging. For R&D projects only.
---

# Pattern Navigator Skill

Navigate the knowledge taxonomy to find relevant patterns, variants, contexts, and domain-specific handling during debugging sessions.

## When to Use

Use when:
- Debugging and need to find existing knowledge
- Checking if a pattern exists before creating new
- Looking up context interactions
- Finding domain-specific overrides
- Cross-referencing related patterns

## Knowledge Structure

```
docs/knowledge/
├── _taxonomy.yaml           # Machine-readable index of all knowledge
├── _taxonomy.md             # Human-readable overview
├── patterns/                # Level 1: Recurring phenomena
│   └── {pattern-id}/
│       ├── definition.md    # What it is
│       ├── handling.md      # How to handle it
│       ├── variants/        # Level 2: Subtypes
│       └── references.yaml  # Example instances
├── contexts/                # Level 3: Environmental factors
│   └── {context-id}/
│       ├── description.md
│       ├── effects.md       # General effects
│       └── interactions/    # Pattern-specific effects
│           └── {pattern}.md
├── domains/                 # Level 4: Platform/framework specifics
│   └── {domain-id}/
│       ├── constraints.md
│       ├── quirks.md
│       └── overrides/       # Pattern overrides for this domain
│           └── {pattern}.md
└── edge-cases/              # Level 5: Truly unique instances
    └── {case-id}.md
```

---

## Navigation Commands

### Find Pattern

When you need to check if a pattern exists:

```bash
# Quick check in taxonomy
grep -i "{term}" docs/knowledge/_taxonomy.yaml

# Search pattern definitions
grep -r "{term}" docs/knowledge/patterns/*/definition.md

# Read taxonomy for overview
cat docs/knowledge/_taxonomy.yaml
```

**Then:**
1. If found: Read `patterns/{pattern}/handling.md`
2. If not found: Might be a new pattern to document

---

### Find Variant

When standard pattern handling doesn't work:

```bash
# List known variants
ls docs/knowledge/patterns/{pattern}/variants/

# Search for variant characteristics
grep -r "{distinguishing-feature}" docs/knowledge/patterns/{pattern}/variants/
```

**Then:**
1. Compare current instance to known variants
2. If match: Read variant-specific handling
3. If no match: Might be new variant (use `/au-learn`)

---

### Find Context Interaction

When pattern behaves differently in a specific context:

```bash
# Check context exists
ls docs/knowledge/contexts/

# Read context effects
cat docs/knowledge/contexts/{context}/effects.md

# Check pattern-specific interaction
cat docs/knowledge/contexts/{context}/interactions/{pattern}.md
```

**Then:**
1. If interaction documented: Apply context-aware handling
2. If not documented: Discover and document with `/au-learn`

---

### Find Domain Override

When platform-specific behavior is suspected:

```bash
# Check domain exists
ls docs/knowledge/domains/

# Read domain constraints/quirks
cat docs/knowledge/domains/{domain}/constraints.md
cat docs/knowledge/domains/{domain}/quirks.md

# Check pattern override
cat docs/knowledge/domains/{domain}/overrides/{pattern}.md
```

**Then:**
1. If override exists: Use domain-specific handling
2. If not: Check if this is a new domain quirk

---

### Find Related Patterns

When current pattern might relate to others:

```yaml
# In _taxonomy.yaml, patterns have:
patterns:
  toggle:
    related: [checkbox, switch, drawer]  # Check these too
```

```bash
# Read related pattern
cat docs/knowledge/patterns/{related-pattern}/handling.md
```

---

### Search Edge Cases

When debugging something potentially unique:

```bash
# Search edge cases for similar symptoms
grep -r "{symptom}" docs/knowledge/edge-cases/

# List all edge cases
ls docs/knowledge/edge-cases/
```

**Review:** Could this edge case be promoted to pattern/variant?

---

## Taxonomy Schema

Understanding the `_taxonomy.yaml` structure:

```yaml
version: "1.0"
last_updated: "YYYY-MM-DD"

patterns:
  pattern-id:
    name: "Human Readable Name"
    description: "Brief description"
    variants:
      - variant-1
      - variant-2
    related: [other-pattern-1, other-pattern-2]
    contexts_that_affect: [context-1, context-2]

contexts:
  context-id:
    name: "Context Name"
    description: "What this context is"
    affects_patterns: [pattern-1, pattern-2]

domains:
  domain-id:
    name: "Domain Name"
    overrides: [pattern-1, pattern-3]

edge_cases:
  case-id:
    description: "Brief description"
    related_pattern: pattern-id
    review_flag: true  # Should be reviewed for pattern promotion
```

---

## Quick Reference Lookup

### Pattern Handling Lookup

```bash
# One-liner to get handling for a pattern
cat docs/knowledge/patterns/{pattern}/handling.md
```

### Variant Distinguisher Lookup

```bash
# Find what distinguishes a variant
grep -A5 "distinguisher:" docs/knowledge/patterns/{pattern}/variants/{variant}.md
```

### Context Effect Lookup

```bash
# Find how context affects a pattern
cat docs/knowledge/contexts/{context}/interactions/{pattern}.md
```

---

## Navigation Workflow

When debugging, follow this order:

1. **Pattern** → Does this match a known pattern?
   ```
   Check: _taxonomy.yaml → patterns/{id}/handling.md
   ```

2. **Variant** → Is this a known subtype?
   ```
   Check: patterns/{pattern}/variants/
   ```

3. **Context** → What environmental factors apply?
   ```
   Check: contexts/{context}/interactions/{pattern}.md
   ```

4. **Domain** → Are there platform-specific rules?
   ```
   Check: domains/{domain}/overrides/{pattern}.md
   ```

5. **Edge Case** → Is this truly unique?
   ```
   Check: edge-cases/ for similar cases
   Document if new
   ```

---

## Cross-Reference Checklist

Before declaring something "unique":

- [ ] Searched `_taxonomy.yaml` for pattern
- [ ] Checked related patterns
- [ ] Checked all applicable contexts
- [ ] Checked domain overrides
- [ ] Searched edge cases for similar symptoms
- [ ] Reviewed pattern variants

---

## Integration with Commands

| Command | Purpose |
|---------|---------|
| `/rnd-debug` | Systematic 5-level debugging (uses navigator) |
| `/au-learn` | Document discovered pattern/variant/context |

---

**Remember:** The taxonomy is only valuable if kept updated. When you discover something not in the taxonomy, document it with `/au-learn`.
