# R&D Methodology

**Note:** This rule is for R&D projects only (e.g., ariadne). Standard implementation projects don't need this.

## Core Principles

### 1. Data First, Fix Later

**NEVER fix issues as you find them.** Gather data across all instances first, then analyze.

```
BAD:  Run App1 → find bug → fix bug → run App2 → find bug → fix bug...
GOOD: Run all apps → collect results → analyze patterns → fix root causes
```

Why data-first:
- Individual bugs often share root causes
- Fixing one symptom may break another flow
- Pattern recognition requires a complete dataset
- Premature fixes waste effort on symptoms, not causes

**The workflow:**
1. **Baseline** - Run all instances, capture metrics
2. **Analyze** - Look for patterns across results
3. **Hypothesize** - What systemic issues explain multiple failures?
4. **Fix** - Address root causes that move multiple instances
5. **Validate** - Re-run all instances to confirm

### 2. Pattern-Centric Thinking

Track knowledge by **patterns**, not by individual instances.

```
BAD:  "App1 works, App2 works, App3 broken"
GOOD: "Toggle pattern: standard handling works. Variant 'toolbar-toggle' needs X"
```

Why pattern-centric:
- 1000 instances doesn't mean 1000 entries
- Knowledge compounds, not fragments
- Context stays focused during debugging
- Solutions become reusable

## The Five Levels of Knowledge

| Level | Type | What It Contains |
|-------|------|------------------|
| 1 | **Patterns** | Recurring phenomena (e.g., toggle, drawer, grid) |
| 2 | **Variants** | Pattern subtypes (e.g., toolbar-toggle, checkbox-toggle) |
| 3 | **Contexts** | Environmental factors (e.g., scrollable, dialog, nested) |
| 4 | **Domains** | Platform specifics (e.g., Compose UI, Flutter, WebView) |
| 5 | **Edge Cases** | Truly unique instances (flag for review) |

## Knowledge Structure

```
docs/knowledge/
├── _taxonomy.yaml       # Machine-readable index (source of truth)
├── _taxonomy.md         # Human-readable overview
├── patterns/            # Level 1: Recurring phenomena
│   └── {pattern}/
│       ├── definition.md
│       ├── handling.md
│       ├── variants/    # Level 2: Subtypes
│       └── references.yaml
├── contexts/            # Level 3: Environmental factors
│   └── {context}/
│       ├── definition.md
│       └── effects.md
├── domains/             # Level 4: Platform specifics
│   └── {domain}/
│       ├── constraints.md
│       └── overrides/
└── edge-cases/          # Level 5: Unique instances
```

## Required Behaviors

### When Starting a Session
1. Read `CLAUDE.md` for current plan and state
2. Read `docs/research/_state.yaml` if exists
3. Start work

**Don't preload knowledge docs.** The taxonomy and pattern files are only needed when debugging—loading them at session start wastes context on information you might never need.

### When Debugging
First, check if this problem has been seen before:
1. Read `docs/knowledge/_taxonomy.yaml` to find relevant patterns
2. Use `/rnd-debug` to work through levels systematically:

```
Level 1: Pattern     → Does standard handling work?
Level 2: Variant     → Is this a known subtype?
Level 3: Context     → What environmental factors?
Level 4: Domain      → Platform-specific behavior?
Level 5: Edge Case   → Truly unique? (flag for review)
```

**Never jump straight to "edge case" without checking patterns first.**

### When Solving Problems
Use `/au-learn` to extract and document the solution:
- New pattern discovered → `patterns/`
- New variant found → `patterns/{pattern}/variants/`
- Context interaction → `contexts/`
- Platform quirk → `domains/`

**Knowledge compounds when documented.**

### When Ending a Session
1. Update `docs/research/_state.yaml` with current state
2. Note blockers and next steps in `CLAUDE.md`
3. Commit and push at logical breakpoints

## Research Documentation

### Finding Documents (FINDINGS-XXX-title.md)
```markdown
# FINDINGS-XXX: Title

**Date**: YYYY-MM-DD
**Status**: Investigating | Resolved

## Observation
What was seen during testing.

## Root Cause
Why it happened.

## Fix Applied
What was changed.

## Validation
How to verify the fix works.

## Related
Files affected, test apps used.
```

### Hypothesis Tracking (hypotheses.md)
```markdown
# Hypotheses

## Active Hypotheses

### H1: [Statement]
**Confidence:** 60%
**Evidence For:**
- [observation]
**Evidence Against:**
- [observation]
**Test:** [how to validate]
```

## Strategic Compaction

**Compact strategically, not arbitrarily:**
- After completing a research phase
- After debugging a complex issue
- After 50+ tool calls if approaching limits

**Never compact:**
- Mid-debugging session
- While actively testing across multiple instances
- Before documenting findings

## Validation Sprints

When validating across multiple apps/instances:

1. **Define the cohort** - List all instances to test
2. **Baseline all** - Run each instance, capture standardized metrics
3. **Build the matrix** - Tabulate results (app × metric)
4. **Identify clusters** - Which apps fail similarly? What do they share?
5. **Form hypotheses** - What root causes explain the clusters?
6. **Prioritize fixes** - Which fix moves the most apps?
7. **Implement & re-validate** - Fix one thing, re-run all apps

**Resist the urge to fix mid-baseline.** The dataset is incomplete until all instances are run.

## Commands for R&D

| Command | Purpose |
|---------|---------|
| `/rnd-debug` | Start 5-level debugging escalation |
| `/au-learn` | Extract patterns from current session |
| `/au-checkpoint` | Save progress at logical breakpoint |

## Anti-Patterns

### Don't Fix While Exploring
```
BAD:  Find issue in App1 → immediately start debugging → lose context on other apps
GOOD: Note issue → continue baseline → analyze all results → then fix systematically
```

The urge to fix is strong. Resist it. Incomplete data leads to local optimizations that may hurt global performance.

### Don't Skip the Taxonomy
```
BAD: "Fixed toggle issue in App X"
GOOD: "Discovered toolbar-toggle variant needs checked attribute"
```

### Don't Fragment Knowledge
```
BAD: Separate docs for each app tested
GOOD: Central pattern docs with app references
```

### Don't Lose Session State
```
BAD: End session without updating _state.yaml
GOOD: Always update state before ending
```
