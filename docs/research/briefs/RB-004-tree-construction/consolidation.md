# RB-004: Tree Construction — Consolidation

**Date:** 2026-02-13
**Status:** Complete (3/4 sources — Gemini unavailable)
**Brief:** [RB-004 Prompt](./prompt.md)
**Sources:** GPT, Claude, Perplexity

## Summary

Three sources independently analysed tree construction for hierarchical retrieval. The convergence is exceptionally strong — all three arrive at the same recommended architecture through complementary analytical routes: **top-down divisive clustering (embedding-based) as the tree backbone, with LLM-generated structured contrastive summaries at each node, controlled soft assignment (1–3 parents per leaf) for multi-topic content, and incremental maintenance via PERCH/GRINCH-style local repairs between periodic full rebuilds.** The most important finding is that no construction method solves the cross-branch failure mode alone — the emerging best practice is a layered defense combining content decomposition, soft clustering, graph-based cross-links, and beam search at query time. A second critical finding is that **routing summaries are fundamentally different from reading summaries** — they should be structured artifacts (entities + keywords + contrastive boundaries + narrative) optimised for sibling differentiation, not comprehension. For tree quality evaluation, **no routing-specific metric exists in the literature** — this is a genuine research gap that HCR can fill with per-level routing accuracy (analogous to selective search's Rn metric) and sibling distinctiveness scores. The federated search literature (CORI, ReDDE, query-based sampling) provides the strongest framework for HCR's external-pointer leaf constraint.

---

## Consensus

All three sources agree on the following. Confidence reflects strength and independence of corroboration.

| # | Finding | GPT | Perplexity | Claude | Confidence |
|---|---------|-----|------------|--------|------------|
| 1 | **Top-down divisive clustering is the best backbone for HCR's constraints.** It naturally controls depth (d=2–3) and branching (b=8–12), produces near-balanced trees, and is computationally cheap. Bisecting k-means outperforms agglomerative methods for cluster quality while being O(n) vs O(n²). | Yes — bisecting k-means produces "more uniformly sized clusters"; split policies are the key lever | Yes — "most natural backbone for HCR"; explicitly recommends top-down divisive with LLM-suggested facets at level 1 | Yes — bisecting k-means "produces better clusterings"; Bonsai (K=100, depth 1–2) outperforms deep binary trees | **Very High** |
| 2 | **RAPTOR's collapsed tree outperforming strict traversal is a structural prediction, not an anomaly.** The tree's value lies in creating multi-granularity representations (enrichment), not in enforcing a routing path. All three sources derive this from first principles. | Yes — "the value of the tree may be in producing multi-granularity, differentiable summaries—not in enforcing a single routing path" | Yes — collapsed tree "outperforms strict top-down traversal, suggesting the tree is more a multi-granularity representation than a reliable routing structure" | Yes — "tree construction and traversal strategy are not independent"; tree's value may be "more in organizing summarization than in providing a routing structure" | **Very High** |
| 3 | **Routing summaries must be structured, contrastive, and entity-preserving — not reading summaries.** Summaries should include: discriminative hooks (rare entities/IDs), contrastive boundary cues ("covers X, NOT Y"), multi-aspect coverage, and structured fields alongside prose. | Yes — "discriminative hooks, contrastive boundary cues, multi-aspect coverage, match-preserving representation" as four required fields | Yes — structured schema: `{theme, includes, excludes, key_entities, key_terms, typical_queries}` | Yes — "contrastive summarization" theoretically well-motivated; "entity and identifier preservation" has strong evidence; structured formats show moderate evidence of advantage | **Very High** |
| 4 | **No single method solves cross-branch queries.** The emerging best practice is a layered defense: (1) content decomposition into atomic units, (2) soft clustering / leaf duplication, (3) graph-based cross-links, (4) beam search at query time, (5) collapsed-tree fallback. | Yes — four structural mitigations (soft assignment, graph augmentation, decomposition, multi-path); "cross-branch safety valve" required | Yes — five-layer defense: decomposition, controlled overlap, cross-links, beam search, HIRO-style thresholds | Yes — five layers: proposition decomposition, soft clustering, entity index, beam search (width 3–5), collapsed-tree fallback | **Very High** |
| 5 | **Standard cluster metrics (silhouette, Davies-Bouldin) are poor predictors of routing quality.** The Stanford IR textbook explicitly states this. No routing-specific tree quality metric exists in the literature. This is a genuine research gap. | Yes — relevance-neighbourhood diagnostics and TPM are the closest; three routing-native metrics proposed | Yes — Dasgupta cost adapted to query-relevance graph; per-level routing accuracy; sibling distinctiveness; coverage@k | Yes — selective search Rn metric is the closest analog; Optimum Clustering Framework (Fuhr 2012) is the principled direction | **Very High** |
| 6 | **LLMs provide highest value in summarization, less in partitioning.** Summarization is indispensable (proven by RAPTOR, LATTICE). Entity extraction is valuable but expensive. Partitioning can be safely left to embedding-based methods. LLM validation/refinement of summaries is promising but unproven. | Yes — LLMs on cluster representatives (not every document); hybrid pipelines proportional to number of base clusters | Yes — LLMs for summaries/labels/aspect suggestion; embeddings for bulk clustering and incremental updates | Yes — summarization is highest-value; semantic partitioning shows "minimal LLM value-add"; contrastive refinement is promising but unproven | **Very High** |
| 7 | **Near-balanced trees are preferred for routing.** Size imbalance creates "miscellaneous" branches with weak summaries and high sibling overlap. Bisecting k-means and PERCH both target balance. Variable branching within bounds (b ∈ [6, 15]) is better than fixed branching everywhere. | Yes — "enforce balance constraints during construction and maintenance, even if it slightly worsens within-cluster cohesion" | Yes — "near-balanced trees are preferred: they minimize average depth and spread misrouting risk more evenly" | Yes — "allow moderate imbalance" with soft constraints (min 3, max 3× median); variable branching ∈ [6, 15] | **Very High** |
| 8 | **Incremental maintenance follows "insert locally, repair locally, rebuild periodically."** PERCH (tree rotations for purity/balance), GRINCH (rotate + graft), and BIRCH (CF-tree summary statistics) provide transferable primitives. No system addresses routing-specific degradation detection. | Yes — PERCH, BIRCH, CluStream as maintenance primitives; "micro-branches" for new content | Yes — PERCH rotations, OHAC split-merge, BERTopic incremental updates; per-node quality monitors with threshold-triggered subtree rebuilds | Yes — GRINCH rotate+graft, BIRCH CF-trees, split/merge heuristics; dirty-flag summary staleness tracking | **Very High** |
| 9 | **Multi-vector (ColBERT-style) representations at the summary level are strongly recommended.** They preserve detail hooks that single-vector embeddings wash out. MUVERA achieves 95% recall with reduced storage. Token pooling reduces ColBERT indexes by 50–75% with <5% degradation. | Yes — "store multi-vector representations for summaries so detail queries can still match rare tokens" | Yes — "small set (e.g., 8–16) of multi-vectors from entity names, schema identifiers, and rare terms" | Yes — "high-confidence recommendation"; "directly address [DPI failure] by preserving token-level discriminative signals" | **High** |
| 10 | **Content decomposition into atomic semantic units is the primary defense against cross-branch failure.** PropRAG achieves 94% Recall@5 on HotpotQA via proposition-based decomposition. Finer-grained units produce cleaner partitions with fewer multi-topic items. | Implicit — decomposition as "third mitigation"; route to source+offset rather than monolithic document | Yes — "primary defense": normalize to atomic units (sections, API endpoints, tickets); only irreducible multi-topic units need soft assignment | Yes — PropRAG explicitly cited; 94% Recall@5 on HotpotQA; "quality degrades significantly with weaker LLMs" | **High** |
| 11 | **Federated search (CORI, ReDDE) provides the framework for external pointer leaves.** 300–500 sampled documents per source are sufficient for effective resource selection. Imperfect representations work surprisingly well for routing. | Yes — BIRCH CF-tree concept: "smallest descriptor that still preserves routing hooks"; streaming clustering for drift | Yes — federated search patterns: metadata + sampled content + historical queries; placeholder leaves for unavailable sources; ConStruM as direct analog | Yes — CORI robust to incomplete representations; query-based sampling; selective search (shard selection) as direct analog to HCR traversal | **High** |
| 12 | **Soft assignment is unusually cheap in HCR because leaves are pointers.** Duplicating a pointer across 2–3 branches incurs minimal storage overhead while dramatically reducing cross-branch elimination probability. | Yes — "duplicating a pointer across two branches incurs minimal storage, but greatly reduces the probability of cross-branch elimination" | Yes — "controlled duplication at the leaf level: each leaf can have up to 2–3 parents" | Yes — "allowing leaves to have 1–3 parents captures cross-topic content without exploding storage" | **High** |
| 13 | **RAPTOR's GMM soft clustering is limited in practice.** Despite being the only mainstream system with native multi-membership, a Stanford CS224N analysis found GMM often produces flat structures with minimal actual soft clustering for standard document sizes. The Gaussian assumption is a poor fit for text embedding distributions. | Implicit — soft clustering is structurally important but RAPTOR's recursive clustering produces variable-depth, uneven branching | Not explicitly stated | Yes — Stanford CS224N analysis; GMM achieves only 55.17% accuracy as baseline; "Gaussian assumption is a poor fit for text embedding distributions" | **Medium** |

---

## Conflicts

| # | Point of Conflict | Position A | Position B | Assessment |
|---|-------------------|-----------|-----------|------------|
| 1 | **Bottom-up vs top-down as primary construction method** | GPT and Perplexity both recommend top-down divisive clustering as the primary backbone, citing controllable topology and natural alignment with HCR's d/b constraints. | Claude recommends "proposition-based decomposition followed by embedding-based soft clustering (GMM or graph-community detection)" — a more bottom-up framing. | **Top-down divisive is the better fit for HCR.** Bottom-up approaches (RAPTOR-style) produce uncontrolled depth and branching. Top-down divisive naturally constrains to d=2–3, b=8–12 and tends toward balanced trees. Claude's recommendation for GMM is weakened by their own finding that GMM is limited in practice. **Default to top-down divisive with soft assignment as a secondary mechanism for multi-topic leaves.** |
| 2 | **GraphRAG as primary vs secondary index** | Perplexity frames graph community detection as a "secondary index for cross-cutting, entity-heavy queries" — supplementary to the main tree. | Claude and GPT both acknowledge graph augmentation's value but don't frame the relationship as primary/secondary explicitly. | **Perplexity's framing is the most practical for HCR.** Full GraphRAG-style construction is 10–50× more expensive than RAPTOR. For Su's use case, a lightweight entity index (NLP-based extraction, not full LLM graph construction) as a cross-branch link structure is the right cost-quality tradeoff. Graph communities as a secondary index for entity-heavy global queries. |
| 3 | **Whether a "collapsed-tree fallback" should be part of the architecture** | GPT explicitly recommends a "cross-branch safety valve: collapsed/fallback retrieval over multi-level summaries when routing confidence is low." Claude includes this as item (5) in the layered defense. | Perplexity does not explicitly recommend collapsed-tree fallback, focusing instead on beam search and multi-path expansion as the query-time mitigations. | **Include collapsed-tree fallback as a design option, but not the default path.** RAPTOR's collapsed tree result is compelling, but under a 400-token budget, searching all nodes is expensive in scoring calls and may not improve precision (which matters more than recall under tight budgets). Beam search with width 3–5 is the primary query-time mitigation; collapsed fallback is the emergency valve when beam search confidence is very low. |
| 4 | **Summary hallucination risk** | GPT uniquely flags that RAPTOR reports ~4% hallucination rate in summaries, and warns that "hallucinated hook terms are more dangerous than hallucinated narrative—because hook terms drive elimination." | Claude and Perplexity do not address hallucination risk in summaries. | **GPT is right to flag this.** Hallucinated entities in a routing summary could cause false-positive routing (queries directed to wrong branches) or false-negative elimination (correct branches dismissed because hallucinated terms don't match). This is a construction-time quality concern that should be part of the LLM validation pass. |
| 5 | **ArchRAG and newer systems** | Claude uniquely surfaces ArchRAG (Wang et al., 2025): +10% accuracy vs GraphRAG with 250× fewer tokens, and TagRAG (78.36% win rate, 14.6× cheaper than GraphRAG). | GPT and Perplexity do not mention ArchRAG or TagRAG. | **ArchRAG is a relevant data point** — it demonstrates that graph-based construction can be made dramatically cheaper (C-HNSW + weighted Leiden). TagRAG's hierarchical domain tag chains are worth noting. Neither changes the primary recommendation (top-down divisive + LLM summaries) but they strengthen the case for lightweight graph augmentation. |

---

## Gaps

### Between sources
- **Gemini unavailable** — unlikely to change conclusions given strong three-source convergence.
- **Claude uniquely surfaced** PropRAG (EMNLP 2025, 94% Recall@5 on HotpotQA), ArchRAG, TagRAG, KG2RAG, Bonsai/PECOS from XMC literature, GRINCH, Election Tree, OHC quasi-dendrograms, CORI/ReDDE/selective search, MUVERA, and content drift detection methods. Claude provided the most comprehensive coverage of adjacent literatures (XMC, federated search, graph-augmented RAG).
- **GPT uniquely surfaced** Smucker & Allan's critique of nearest-neighbour test, HDBSCAN limitations for embedding space, CluStream, Taxonomy Probing Metric (TPM), and summary hallucination risk.
- **Perplexity uniquely surfaced** ConStruM (database context trees), Dasgupta's cost function for hierarchical clustering evaluation, LLM-guided taxonomy generation with multi-aspect clustering, and multi-view hierarchical clustering frameworks.

### In the theory
1. **No empirical study of contrastive summary generation for routing.** All three sources recommend contrastive summaries ("covers X, NOT Y") but acknowledge this is theoretically motivated, not empirically tested. This is the highest-value research gap for HCR to address.
2. **No routing-specific tree quality metric exists.** Per-level routing accuracy (analogous to selective search Rn), sibling distinctiveness, and summary-to-descendant coverage are proposed but have not been implemented or validated for hierarchical retrieval.
3. **No empirical study of incremental maintenance quality degradation for RAG trees.** How quickly does tree quality degrade with incremental insertions? At what threshold should subtrees be rebuilt? No one has measured this.
4. **No formal connection between summary properties and routing accuracy.** What specific summary attributes (length, entity coverage, contrastive cues, structured format) predict per-level routing accuracy? No ablation study exists.
5. **No principled method for workload-aware tree construction.** All clustering is content-based. None optimises partitions for the expected query distribution. The Optimum Clustering Framework (Fuhr 2012) provides the conceptual foundation but has not been applied to hierarchical retrieval.

---

## Key Takeaways

### 1. The construction recipe for HCR is convergent across all sources

Top-down divisive clustering + LLM contrastive summaries + controlled soft assignment:

1. **Decompose** multi-topic content into atomic semantic units before clustering
2. **Partition** top-down via bisecting k-means (or k-way splits) in embedding space, constrained to d=2–3, b∈[6,15]
3. **Assign** multi-topic units to 1–3 parents (soft assignment via duplication — cheap because leaves are pointers)
4. **Summarise** each internal node with an LLM prompt that includes sibling context for contrastive differentiation
5. **Represent** summaries as structured artifacts (entities + keywords + contrastive boundaries + narrative) with multi-vector embeddings
6. **Evaluate** via per-level routing accuracy on held-out queries, sibling distinctiveness scores, and entity coverage metrics

### 2. Routing summaries are a distinct artifact class

No published system optimises summaries for routing. The consensus design:

- **Structured fields**: `{theme, includes, excludes, key_entities, key_terms, typical_queries}`
- **Contrastive cues**: generated with sibling context in the LLM prompt ("state what this branch covers and what it does NOT, relative to siblings")
- **Entity preservation**: explicit instruction to preserve rare identifiers, IDs, proper nouns — not just thematic content
- **Multi-vector representation**: ColBERT-style per-token embeddings for detail hooks, plus single dense embedding for coarse routing, plus BM25 index over key terms
- **Length sweet spot**: ~60–130 tokens for narrative + auxiliary structured fields

This directly supports HCR's cascade scorer (hybrid BM25+dense → cross-encoder).

### 3. Cross-branch failure requires layered defense, not a single solution

The five-layer defense:

| Layer | When | What | Cost |
|-------|------|------|------|
| 1. Decomposition | Construction | Split multi-topic documents into atomic units | LLM calls per document |
| 2. Soft assignment | Construction | Duplicate leaf pointers across 1–3 parents | Minimal (pointers are cheap) |
| 3. Entity cross-links | Construction | Lightweight entity index linking related branches | NLP extraction + entity graph |
| 4. Beam search | Query time | Keep top-3–5 branches per level | 3–5× scoring cost per level |
| 5. Collapsed fallback | Query time | Search all nodes when beam confidence is low | Full scoring pass (emergency only) |

### 4. Tree quality evaluation is an open research problem

Three proposed routing-native metrics (not yet validated):

- **Per-level routing accuracy**: fraction of queries where the correct subtree is in the top-k children (analogous to selective search Rn)
- **Sibling distinctiveness**: pairwise distance/divergence between sibling summaries; penalise hook overlap across siblings
- **Summary-to-descendant coverage**: do high-IDF entities from descendants appear in ancestor summaries? BERTScore between summary and concatenated descendant content

Plus **cross-branch risk rate**: fraction of queries where relevant leaves span >1 sibling branch.

### 5. Federated search literature solves the external pointer problem

HCR's "leaves as pointers" maps directly to the **collection selection problem**:

- **CORI** is robust to incomplete representations — 300–500 sampled documents per source are sufficient
- **Query-based sampling** builds representations from probe queries when full access is unavailable
- **Selective search** (shard selection → flat search within selected shards) is structurally identical to HCR's tree traversal
- **Content drift detection** via embedding distribution monitoring triggers summary regeneration
- **Placeholder leaves** are acceptable — summaries built from metadata alone, refined as content is sampled

### 6. LLM cost profile is manageable for HCR's scale

| Operation | Cost (100K chunks, GPT-4o-mini) | Frequency |
|-----------|--------------------------------|-----------|
| Summarization (internal nodes) | ~$20–50 | Per construction |
| Entity extraction (NLP-based + LLM for ambiguous) | ~$10–30 | Per construction |
| Full graph extraction (GraphRAG-style) | ~$150–250 | Avoid for primary tree |
| Contrastive summary refinement | ~$5–15 | Per construction |
| Incremental summary updates | ~$0.01–0.10 per node | Per update |

Embedding-based clustering (k-means, bisecting k-means) adds minutes, not dollars.

### 7. Summary quality and traversal strategy matter more than tree topology

The deepest insight from all three sources: **optimising tree topology yields diminishing returns compared to optimising summary quality and traversal strategy**. RAPTOR's collapsed tree outperforms its strict traversal mode. LATTICE's LLM-guided traversal outperforms embedding-based traversal on the same tree. The implication: invest engineering effort in summary generation and beam-search traversal before fine-tuning clustering algorithms.

---

## Recommendation

**Decision required:** Yes — tree construction strategy for Phase 1.

### Recommended Construction Pipeline

Based on three-source consensus:

**Step 1: Preprocessing**
- Decompose multi-topic content into atomic semantic units (sections, API endpoints, tables, tickets)
- For external sources: build leaf descriptors from metadata + 300–500 sampled documents (CORI approach)
- Tag multi-topic candidates using topic distribution entropy

**Step 2: Tree backbone (top-down divisive)**
- Level 1: Bisecting k-means (or k-way split) in embedding space, b∈[8,12], guided by LLM-suggested facets for the corpus
- Level 2+: Recursive k-way splits within each cluster, b∈[6,15], stopping at depth 2–3 or when cluster compactness exceeds threshold
- Enforce near-balance: min 3 leaves per branch, max 3× median branch size

**Step 3: Soft assignment**
- For leaves flagged multi-topic: allow assignment to up to 2–3 parents
- LLM review of borderline assignments where embedding distances to top-2 clusters are close

**Step 4: Summary generation**
- LLM prompt per internal node, including:
  - Sampled child content / metadata
  - Sibling summaries (for contrastive generation)
  - Explicit instruction: "state what this branch covers AND does not cover relative to siblings; preserve rare entities, IDs, and structural markers"
- Output: structured summary `{theme, includes, excludes, key_entities, key_terms}`
- Represent as: single dense embedding + multi-vector (ColBERT-style) for entities/hooks + BM25 index over key terms

**Step 5: Maintenance**
- Incremental insertion: route new leaves through scoring cascade, attach to best-matching cluster(s)
- Local repair: split/merge when branch size exceeds bounds or routing accuracy drops
- Summary staleness: dirty-flag on leaf changes, lazy regeneration prioritised by access frequency
- Periodic rebuild: full reconstruction when 20–30% of subtree is new content, or on schedule

**Step 6: Evaluation**
- Held-out query → relevant leaf set
- Per-level routing accuracy (Rn analog)
- Sibling distinctiveness (pairwise summary distance)
- Entity coverage (high-IDF descendant entities in ancestor summaries)
- Cross-branch risk rate

### What This Means for H1a and H1b

**H1a (token efficiency, 65%):** Tree construction quality directly determines whether the 400-token budget can produce correct answers. The federated search finding — that 300–500 sampled documents produce effective routing — suggests the routing index can work even with partial source access. No evidence to change confidence yet; RB-006 benchmark is needed.

**H1b (hybrid superiority, 75%):** All three sources independently confirm the hybrid architecture: coarse tree routing + fine similarity within survivors. The convergent recommendation for top-down divisive clustering with beam search traversal IS the hybrid approach. The evidence strengthens H1b — the construction literature supports it as the natural architecture, not just the theoretical optimum. **Recommend updating H1b to 80%.**

### What Remains Open

1. **Contrastive summary generation for routing** — the highest-value experiment HCR can run: do "covers X, NOT Y" summaries improve per-level routing accuracy vs generic summaries?
2. **Optimal summary schema** — which structured fields actually improve scoring? Entity lists vs keyword lists vs contrastive boundaries vs typical queries?
3. **Incremental maintenance degradation** — how quickly does routing accuracy degrade with insertions? When should subtrees be rebuilt?
4. **Workload-aware construction** — can we use query logs to optimise partitions? (Phase 2+)

---

## Next Steps

1. **Update H1b confidence** to 80% — three-source construction consensus directly supports the hybrid architecture
2. **RB-005 (Failure modes)** — cross-branch queries remain the #1 structural risk. Quantify: what fraction of real queries in Su's target domain are cross-branch? What is the recall floor under beam search (k=3, d=2) with this construction strategy?
3. **RB-006 (Benchmark design)** — must include: per-level routing accuracy as a first-class metric, tree quality evaluation metrics, and comparison of construction methods (divisive vs agglomerative vs graph-augmented)
4. **When Phase 1 begins:** implement construction pipeline (Step 1–4) and evaluation suite (Step 6) as the first deliverables. The cascade scorer (RB-003) and tree construction (RB-004) are architecturally independent and can be built in parallel.
