# Knowledge Taxonomy

Human-readable overview of discovered patterns, contexts, and domains.

**Domain:** {PROJECT_DOMAIN}
**Last Updated:** {DATE}

---

## Quick Reference

| Level | Count | Description |
|-------|-------|-------------|
| Patterns | 0 | Recurring phenomena |
| Variants | 0 | Pattern subtypes |
| Contexts | 0 | Environmental factors |
| Domains | 0 | Platform specifics |
| Edge Cases | 0 | Unique instances |

---

## Patterns (Level 1)

*No patterns documented yet.*

<!-- Template for adding patterns:
### {Pattern Name}

**Path:** `patterns/{pattern-id}/`
**Identification:** {how to recognize}
**Default Handling:** {standard approach}

**Variants:**
- `{variant-id}` - {distinguisher}

**References:** {N} examples documented
-->

---

## Contexts (Level 3)

*No contexts documented yet.*

<!-- Template for adding contexts:
### {Context Name}

**Path:** `contexts/{context-id}/`
**Identification:** {how to recognize}
**Affects Patterns:** {list of patterns}
-->

---

## Domains (Level 4)

*No domains documented yet.*

<!-- Template for adding domains:
### {Domain Name}

**Path:** `domains/{domain-id}/`
**Identification:** {how to recognize}
**Overrides Patterns:** {list of patterns with domain-specific handling}
-->

---

## Edge Cases (Level 5)

*No edge cases documented yet.*

---

## How to Update

1. **Adding a pattern:**
   - Create `patterns/{pattern-id}/definition.md` and `handling.md`
   - Update `_taxonomy.yaml` patterns section
   - Update this file's Patterns section

2. **Adding a variant:**
   - Create `patterns/{pattern-id}/variants/{variant-id}.md`
   - Update `_taxonomy.yaml` pattern's variants list
   - Update this file

3. **Adding a context:**
   - Create `contexts/{context-id}/definition.md` and `effects.md`
   - Update `_taxonomy.yaml` contexts section
   - Update this file

4. **Adding a domain:**
   - Create `domains/{domain-id}/constraints.md`
   - Update `_taxonomy.yaml` domains section
   - Update this file

5. **Adding an edge case:**
   - Create `edge-cases/{case-id}.md`
   - Update stats in `_taxonomy.yaml`
   - Consider: is this really unique, or an undiscovered pattern?

---

*See `_taxonomy.yaml` for machine-readable version.*
