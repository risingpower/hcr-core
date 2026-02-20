# Hypotheses Log

Track beliefs, confidence levels, and validation status.

**Last Updated:** 2026-02-20

---

## Summary

| Status | Count |
|--------|-------|
| Confirmed | 1 (H1c) |
| Invalidated | 2 (H1a, H1b) |
| Uncertain | 0 |
| Retired | 1 |
| **Total Resolved** | **3** |

---

## Active Hypotheses

*All hypotheses resolved. See Invalidated and Confirmed sections below.*

---

## Retired Hypotheses

### H1 (original): Elimination vs similarity

**Status:** retired (reframed)
**Final Confidence:** 55% (strict elimination) / 70% (hybrid reframing)
**Created:** 2026-02-13 (project inception)
**Retired:** 2026-02-13

**Original Statement:**
Retrieval by elimination (narrowing through tree layers) outperforms retrieval by similarity (nearest-neighbour in vector space) for precision-critical, token-sensitive LLM systems.

**Reason for Retirement:**
RB-002 theoretical analysis from three independent sources concluded this framing is too binary. Strict elimination is theoretically fragile (error compounds at (1-ε)^d). The real question isn't elimination *vs* similarity — it's how to combine them optimally. Reframed as three independent, testable sub-hypotheses: H1a (token efficiency), H1b (hybrid superiority), H1c (scoring as lever).

**Legacy:**
The original hypothesis drove the right research. Its failure as stated is a feature — it forced us to find a more precise, testable set of claims.

---

## Confirmed Hypotheses

### H1c: Scoring quality as exponential lever

**Status:** CONFIRMED (as mechanism of failure)
**Final Confidence:** 95%
**Created:** 2026-02-13
**Resolved:** 2026-02-19

**Statement:**
Per-level scoring quality is the primary determinant of hierarchical retrieval quality, with error compounding at (1-ε)^d where ε is per-level error rate and d is tree depth.

**Resolution:**
Confirmed empirically as the mechanism that invalidated H1a and H1b. Per-level epsilon measured for the first time in any hierarchical retrieval system. At depth=5 (medium corpus, 21,897 chunks), even moderate per-level error produces catastrophic end-to-end failure: nDCG dropped from 0.580 (small, depth=3) to 0.094 (medium, depth=5). The (1-ε)^d compounding is the governing equation, exactly as theoretically predicted.

**Key evidence:**
- Small-scale per-level epsilon (default config): L0=0.00, L1=0.22, L2=0.50, L3=0.58, L4=0.84
- Best config (v11, beam=8): L1=0.06, L2=0.28 --- dramatically better but still insufficient at scale
- Beam width monotonically improves epsilon at every level, confirming the mechanism
- Medium-scale collapse to nDCG=0.094 confirms compounding across 5 levels is fatal

**Note:** H1c is confirmed as a mechanism, but the second part of the hypothesis --- that achieving sufficient ε is "feasible" with embedding-based routing --- is invalidated. The mechanism works as predicted; the routing quality required is not achievable with current embedding approaches.

---

## Invalidated Hypotheses

### H1a: Token efficiency of hierarchical retrieval

**Status:** INVALIDATED
**Final Confidence:** 0%
**Created:** 2026-02-13
**Resolved:** 2026-02-19

**Statement:**
Hierarchical coarse-to-fine retrieval achieves equivalent or better answer accuracy than flat similarity retrieval while using fewer tokens.

**Resolution:**
Invalidated at medium scale. HCR achieved nDCG@10 = 0.094 vs Flat+CE = 0.749 at 21,897 chunks. While HCR maintained token efficiency (292 tokens vs 349), the tokens it selected were overwhelmingly incorrect due to routing failure. Token savings are meaningless when accuracy collapses.

**Key evidence:**
- Small scale: best HCR nDCG=0.580, Flat+CE=0.835 (gap=0.255)
- Medium scale: HCR nDCG=0.094, Flat+CE=0.749 (gap=0.655)
- Fail-fast kill at Phase B step 3

---

### H1b: Hybrid coarse-to-fine superiority

**Status:** INVALIDATED
**Final Confidence:** 0%
**Created:** 2026-02-13
**Resolved:** 2026-02-19

**Statement:**
Coarse elimination combined with fine similarity search outperforms either pure approach alone.

**Resolution:**
Invalidated. Coarse elimination via embedding-based routing destroys recall at scale. The hybrid approach (coarse routing + fine similarity within surviving branches) never outperformed pure flat similarity + cross-encoder at any configuration tested. Twelve configs across two embedding models and four routing strategies all failed to match the kill baseline.

**Key evidence:**
- Best HCR config (v11): nDCG=0.580 vs Flat+CE=0.835 at small scale
- All 12 configs below kill baseline
- Medium scale: catastrophic collapse to nDCG=0.094
- Routing error compounds multiplicatively, negating any benefit from hierarchical structure

---

## How to Update

1. **New hypothesis:** Add to Active Hypotheses with initial confidence
2. **Evidence found:** Update confidence %, add to Evidence For/Against
3. **Validated:** Move to Validated section, document final evidence
4. **Invalidated:** Move to Invalidated section, document why

**Confidence Guidelines:**
- 0-25%: Speculation, little evidence
- 26-50%: Plausible, some supporting evidence
- 51-75%: Likely, substantial evidence
- 76-90%: High confidence, strong evidence
- 91-100%: Near certain, overwhelming evidence

**Always justify confidence changes** with specific evidence references.
