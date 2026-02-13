---
description: Extract codebase conventions and patterns for context. Analyzes structure, naming, and key abstractions.
---

# /au-map Command

Extract conventions and patterns from existing code to maintain consistency.

## What This Command Does

1. **Analyze Structure** - Map directory layout and organization
2. **Extract Naming Conventions** - Files, components, functions, variables
3. **Identify Key Patterns** - Architectural patterns with file examples
4. **Document Tech Stack** - Dependencies and tools in use
5. **Optional Cache** - Store in `~/.claude/cache/{repo}/codebase.md` (1-day TTL)

## When to Use

Use `/au-map` when:
- Onboarding to unfamiliar code area
- Before implementing in a new module
- To understand conventions before contributing
- Starting work in a repo you don't know well

## When NOT to Use

Use other commands when:
- You need files for a specific task (use `/au-proto` quick scan)
- You already know the codebase conventions
- Making a small change in familiar code

## Differentiation from /au-proto

| Command | Purpose |
|---------|---------|
| `/au-proto` | Find ~10 relevant files **for a specific task** |
| `/au-map` | Extract **conventions and patterns** for general understanding |

## Workflow

```
/au-map

1. Analyze: Directory structure, key entry points
2. Extract: Naming conventions, patterns, tech stack
3. Output: ~15-20 observations in memory (or cached)
4. Ready: Context loaded for implementation work
```

With path argument:
```
/au-map src/components

1. Focus: Only analyze src/components directory
2. Extract: Component patterns, naming, structure
3. Output: Focused observations for that area
```

## Extraction Strategy

### What to Analyze

1. **Directory Structure** - Top-level folders and their purposes
2. **Entry Points** - Main files, index exports, routing
3. **Naming Patterns** - How files, functions, classes are named
4. **Key Abstractions** - Common patterns, base classes, utilities
5. **Config Files** - Build, lint, test configuration
6. **Dependencies** - Major libraries and frameworks

### What to Skip

- Node modules / vendor directories
- Build output directories
- Test files (unless specifically mapping test patterns)
- Generated files
- Lock files

## Project-Type Extraction Rules

<!-- REPO-CONTEXT-START -->
<!-- This section is replaced during scaffolding with repo-specific extraction rules -->
<!-- Example for app-fe (Frontend):
### Frontend Extraction

| Category | What to Extract |
|----------|-----------------|
| Components | Naming (PascalCase?), structure (atomic design?), colocation |
| Hooks | Custom hooks location, naming conventions, patterns |
| State | State management approach, store structure |
| Routing | Route patterns, layouts, guards |
| Styling | CSS approach (modules, tailwind, styled), theme structure |
| API Layer | Fetch patterns, caching, error handling |
-->
<!-- Example for site-be (Backend):
### Backend Extraction

| Category | What to Extract |
|----------|-----------------|
| API Patterns | Endpoint structure, versioning, response format |
| Models | ORM patterns, naming, relationships |
| Services | Business logic organization, dependency injection |
| Middleware | Auth, logging, error handling patterns |
| Testing | Test structure, fixtures, factories |
| Config | Environment handling, settings patterns |
-->
<!-- Example for ariadne (R&D):
### R&D Extraction

| Category | What to Extract |
|----------|-----------------|
| Experiments | Experiment structure, versioning, results storage |
| Data Pipeline | Data flow, processing patterns |
| Analysis | Analysis patterns, notebook conventions |
| Models | ML model organization, training patterns |
| Config | Hyperparameter management, experiment tracking |
| Documentation | Research notes, findings organization |
-->
<!-- REPO-CONTEXT-END -->

## Output Format

Generate observations in this structure:

```markdown
# Codebase Map: {repo}

**Generated:** {date}
**Scope:** {path or "full repo"}

## Structure

[Directory layout with purposes]

src/
  components/   # React components (atomic design)
  hooks/        # Custom hooks
  services/     # API layer
  utils/        # Shared utilities

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase, use prefix | `useAuth.ts` |
| Utils | camelCase | `formatDate.ts` |
| Constants | SCREAMING_SNAKE | `API_BASE_URL` |

## Key Patterns

### [Pattern Name]
[Description with file example]

Found in: `src/components/Button/Button.tsx`

### [Pattern Name]
[Description with file example]

Found in: `src/services/api.ts`

## Tech Stack

| Category | Tool | Notes |
|----------|------|-------|
| Framework | Next.js 14 | App router |
| Styling | Tailwind | With custom config |
| State | Zustand | Minimal stores |
| Testing | Vitest + RTL | |
```

## Caching Behavior

### Cache Location
`~/.claude/cache/{repo}/codebase.md`

### Cache TTL
1 day (24 hours)

### Cache Strategy

1. **Check cache first** - If cache exists and is fresh, use it
2. **Refresh if stale** - Re-analyze if cache > 24 hours old
3. **Force refresh** - User can request fresh analysis with `/au-map --fresh`
4. **Path-specific** - Different paths create separate cache entries

### When to Skip Cache

- User requests `--fresh` flag
- Significant time since last session
- User reports conventions seem wrong

## Observation Guidelines

Aim for **15-20 key observations** that cover:

1. **3-4 structural observations** - Directory layout, organization
2. **4-5 naming conventions** - Files, functions, variables, types
3. **4-5 key patterns** - With specific file examples
4. **3-4 tech stack notes** - Major tools and how they're used
5. **1-2 gotchas** - Unusual patterns or things to watch for

## After Mapping

Suggest next steps based on context:

```
Codebase mapped. Key patterns loaded.

This repo uses:
- [Key pattern 1]
- [Key pattern 2]
- [Key pattern 3]

Ready to implement. Try:
- `/au-proto <task>` for quick implementation
- `/au-plan <feature>` for planned work
```

## Related Commands

- `/au-proto` - Quick implementation with task-specific file scan
- `/au-plan` - Full planning for complex features
- `/au-discuss` - Capture preferences before planning
