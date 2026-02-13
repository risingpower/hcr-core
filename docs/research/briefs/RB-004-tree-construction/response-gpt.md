# RB-004: Tree Construction — GPT Response

**Date:** 2026-02-13
**Model:** GPT
**Prompt:** [RB-004 Prompt](./prompt.md)

---

*Paste response below this line.*
# RB-004 Tree Construction for Hierarchical Retrieval

## Core implications for routing accuracy

Hierarchical routing lives or dies on whether the tree’s partitions align with *query-conditioned relevance*, not whether it looks like a “nice” topical taxonomy. The classic “cluster hypothesis” (“closely associated documents tend to be relevant to the same requests”) is only intermittently true, and it fails in exactly the way hierarchical routing fails: relevant items can be isolated (no nearby relevant neighbours) and/or intermingled with non‑relevant items in local neighbourhoods. In Voorhees’ nearest‑neighbour test (n=5), the percentage of relevant documents with **zero** relevant nearest neighbours ranges from **8%** (MED) to **46%** (INSPEC). citeturn20view0 This is a direct empirical signal that in some collections a large fraction of “relevant evidence” is not locally clusterable—even before you add summarisation loss, multi-topic content, or external-source drift.

The same paper makes an additional point that matters more for tree construction than for IR history: cluster-based retrieval is structurally undermined by *intermingling*—relevant documents being closer to non‑relevant documents than to other relevant documents—which contradicts the assumptions of retrieving whole clusters as units. citeturn19view0turn20view0 That maps cleanly onto HCR’s failure mode: if sibling branches overlap in “routing evidence”, a top‑down policy will prune away relevant leaves even with a strong scorer.

A second empirical warning is that common “local” cluster quality checks can be misleading. Smucker & Allan argue that the nearest‑neighbour test is insufficient as a *measure of whether clustering will help retrieval*, motivating a more global document‑network measure (normalized mean reciprocal distance) to avoid over‑crediting local structure. citeturn29view0 This is aligned with RB‑001/RB‑002’s “brittle and dataset-dependent” claim: tree construction needs evaluation criteria that reflect *routing* rather than generic clustering geometry.

## Landscape of tree construction approaches

Below is the practical landscape of methods that can yield a navigation structure for hierarchical retrieval. The main difference between approaches is what signal defines “togetherness” (embedding space, lexical space, graph topology, density, LLM‑elicited concepts), and therefore how they behave under multi-topic documents, rare “detail hooks”, and dynamic updates.

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["hierarchical clustering dendrogram example","bisecting k-means clustering diagram","Leiden algorithm community detection visualization","knowledge graph community detection clusters"],"num_per_query":1}

### Embedding-first, summary-second, bottom-up hierarchies (RAPTOR-style)

RAPTOR builds a tree bottom‑up by recursively clustering embedding vectors and summarising each cluster into a parent node. It explicitly uses **soft clustering** (“nodes can belong to multiple clusters”), motivated by multi-topic segments; it uses **GMMs** and dimension reduction via **UMAP**; it uses **BIC** for selecting the number of clusters and runs **EM** to fit mixture parameters. citeturn22view0 This design choice is important: soft assignment is one of the few published, concrete mitigations for “cross-branch content”. citeturn22view0

However, an empirically crucial observation in RAPTOR is that “collapsed tree retrieval” (search across *all* nodes across levels) can outperform strict traversal, and they motivate it as better granularity matching for different question types. citeturn20view4 For HCR, the implication is sharp: **the value of the tree may be in producing multi-granularity, differentiable summaries—not in enforcing a single routing path** (which compounds per-level elimination errors).

Cost/shape characteristics: RAPTOR’s clustering is iterative and multi-stage (UMAP + GMM + recursion under token limits), so construction cost is dominated by embedding computation, mixture fitting, and repeated LLM summarisation. It is not naturally constrained to the shallow-wide regime; recursion triggers when “a local cluster’s combined context exceeds the summarisation model’s token threshold.” citeturn22view0 That tends to produce variable-depth subtrees and uneven branching.

### Top-down divisive partitioning (bisecting k-means and relatives)

Bisecting k‑means is a practical top‑down method that naturally produces a hierarchy: start with all points, split one cluster into two via k‑means (k=2), repeat until K leaves are reached. citeturn25view0turn26view1 In a classic document clustering evaluation, bisecting k‑means is reported as producing better clusterings than “regular” k‑means and an agglomerative baseline (UPGMA), and it is described as **O(n)** versus **O(n²)** for agglomerative hierarchical clustering. citeturn26view1 The authors also argue part of the advantage is the tendency to yield **more uniformly sized clusters**, which maps directly to routing: extreme size imbalance tends to create “miscellaneous” branches with weak summaries and high sibling overlap. citeturn26view1

Cost/shape characteristics: divisive algorithms are easy to constrain to HCR’s target topology (d=2–3, b=8–12) by setting K accordingly at each level, and by selecting which cluster to split (largest, lowest cohesion, highest entropy). citeturn25view0turn26view1 These “split policies” are a major (and under-theorised) lever: they determine whether the tree becomes balanced (good for routing) or degenerates into a “long tail” of tiny clusters plus one catch‑all.

### Graph community detection hierarchies (GraphRAG/Leiden family)

GraphRAG-style systems convert the corpus into an entity–relationship graph and run community detection (commonly **Leiden**) to identify clusters/communities, then summarise communities for downstream querying. citeturn9view2turn23view0 Relative to embedding-only clustering, the key advantage is that graph structure can capture non-local relationships (shared entities, multi-hop links) that do not sit near each other in embedding space.

The main weaknesses reported in follow-on work are also directly relevant to tree construction: (i) Leiden “relies solely on graph structure and ignores the rich semantics of nodes and edges”, leading to mixed-theme communities and low-quality community summaries; and (ii) global traversal across many communities is **token- and cost-heavy** (a reported example: 2,984 communities and ~\$650 / 106M tokens to answer 100 questions, using a specific LLM pricing assumption). citeturn23view0turn24view0

Cost/shape characteristics: graph-based approaches shift cost into *index-time extraction* (entity recognition, relation extraction, graph building) and then into community detection + summarisation. Their “hierarchy” is usually not a strictly controlled shallow tree; it is a hierarchical community structure or a set of nodes summarised at multiple granularities. citeturn9view2turn23view0 For HCR, the salient takeaway is that graph communities are a strong mechanism for cross-cutting content, but they are expensive and can produce overlapping or semantically incoherent high-level nodes unless semantics are injected upstream. citeturn23view0turn24view0

### Density-based hierarchical clustering (HDBSCAN family)

HDBSCAN yields a hierarchy based on varying density levels, and is designed to be more robust to parameter selection than DBSCAN by selecting clusters based on *stability* across density thresholds; it also supports soft clustering / prediction variants in common implementations. citeturn5search21turn5search17 For retrieval-tree construction, density-based hierarchies are mainly useful when the embedding space has meaningful density structure (e.g., tightly clustered “concept families” plus a lot of noise). Their biggest operational risk is that many real corpora in embedding space do not have stable density-separated “topics”; you can end up with large “noise” segments and unstable cluster boundaries, i.e., exactly the routing ambiguity you’re trying to eliminate. citeturn5search21turn5search17

### Topic-model / mixed-membership approaches (soft assignment by design)

Topic models offer an explicit mechanism for multi-topic membership: each item can load on multiple topics. In modern practice, embedding-based topic models such as BERTopic combine transformer embeddings, clustering, and a class-based TF‑IDF scheme for interpretable topic descriptions. citeturn5search7 The key relevance to HCR is not “topic modelling” per se, but the *mixed-membership prior*: if cross-branch queries are the dominant failure mode, hard partitioning is structurally brittle, so some form of soft assignment (probabilistic memberships, duplication, or graph links) is often necessary.

### Online/incremental tree builders (PERCH-like) and streaming summarisation structures (BIRCH/CluStream-like)

For dynamic maintenance, incremental tree construction is one of the few areas with concrete algorithmic machinery.

* PERCH is an online hierarchical clustering algorithm that (a) routes new points to leaves, (b) inserts them incrementally, and (c) uses **tree rotations** to improve subtree purity and encourage balancedness; it proves perfect dendrogram purity under a separability assumption and reports strong empirical behaviour at scale. citeturn31view0
* BIRCH builds an **in-memory CF-tree** (cluster-feature summaries) and is explicitly designed for very large datasets; it is local (no global scans per decision), incrementally maintainable, and “linearly scalable” under its design, with an incremental mode that can scan the dataset once. citeturn28view0
* CluStream formalises the split between an **online micro-clustering** component (maintaining summary statistics) and an **offline macro-clustering** step, designed for evolving streams and change analysis. citeturn28view1

None of these were designed for IR routing on summaries, but they are directly transferable as *maintenance primitives*: incremental insertion + local repair, and microcluster summaries + periodic rebuilds. citeturn31view0turn28view0turn28view1

### LLM-guided clustering and taxonomy induction

Recent work increasingly uses LLMs to inject “semantic views” into clustering, with the explicit goal of better alignment to human concepts and improved cluster interpretability.

Two patterns are particularly relevant to HCR:

* Few-shot / expert-guided clustering: LLMs can amplify limited guidance to make clustering more label-efficient and semantically coherent than pure embedding distance. citeturn6search33
* Hybrid pipelines that use LLMs cheaply on *cluster representatives* rather than on every document: an EMNLP industry paper reports hierarchical clustering improvements while keeping LLM calls limited (described as proportional to the number of base clusters rather than documents), and reports gains on silhouette and human preference in a business setting. citeturn6search9
* Topic modelling with LLM-generated topic words: LiSA uses LLM prompts to generate candidate topic words per document to construct a “topic-level semantic space”, then combines that with clustering. citeturn6search0

The hard frontier remains what RB‑001 flagged: **automatically choosing the partition objective and parameters** so that resulting clusters match query relevance patterns. Published work shows LLMs can help, but the field does not yet offer a principled, workload-aware selection method. citeturn6search9turn6search33turn6search0

## What makes a node summary good for routing

A routing summary is not a reading summary. It is a *decision interface* whose job is to maximise separability between siblings under limited tokens and noisy scorers. The literature provides several concrete evidence points that translate into design requirements.

Query-biased (user-directed) summaries significantly improve humans’ speed and accuracy in relevance judgements versus static previews. citeturn20view2 This is not “routing through a tree”, but it isolates a general principle: **summaries that surface the query-relevant evidence reduce decision error**. In HCR terms, node summaries should be optimised to let a scorer (BM25+dense+reranker, or even a human) answer: “is my evidence below here?”—not to provide a coherent narrative.

Contrastive summarisation research frames the task as explicitly highlighting differences between related texts (comparative/contrastive summaries), and surveys describe it as a distinct sub-problem from generic summarisation without standard benchmarks but with clear intent: difference-highlighting rather than theme reconstruction. citeturn3search0turn3search8 For routing, this motivates **contrastive sibling summaries**: each child summary should include at least one boundary statement (“covers X rather than Y”) or discriminative anchor terms that are unlikely to appear in sibling summaries.

Keyphrase extraction surveys emphasise that keyphrases support searching and IR tasks by packaging a text’s main topics into a small set of phrases. citeturn3search2 The routing implication is that summaries should contain an explicit “hook list” (rare entities, identifiers, proper nouns, version numbers, acronyms) in addition to prose, because these are the features most likely to differentiate siblings and trigger high BM25 or high token-level match.

Diversity-oriented selection mechanisms such as Maximal Marginal Relevance (MMR) explicitly trade relevance against redundancy; MMR was proposed for retrieval and summarisation contexts to reduce redundancy while maintaining relevance. citeturn7search2 For HCR summaries, MMR-style selection is a useful upstream tactic: when constructing summaries from multiple descendants, select evidence snippets/keywords that cover *distinct sub-aspects* rather than collapsing to the dominant theme—because collapsed themes are exactly what lose detail hooks (RB‑003’s DPI bottleneck).

On representation, late-interaction retrieval models like ColBERT encode query and document into token-level vectors and score via late interaction; ColBERT and ColBERTv2 motivate multi-vector representations as an alternative to single-vector pooling, which can preserve fine-grained matching signals. citeturn3search3turn3search6 For HCR this suggests a concrete upgrade path that is orthogonal to summary text quality: **store multi-vector representations for summaries (or summary+hook lists)** so that detail queries can still match rare tokens even when the prose is thematic.

Finally, summary correctness matters because errors can be amplified by routing. RAPTOR reports a focused annotation study where ~4% of summaries contained minor hallucinations (though they report no discernible QA impact in their setting). citeturn22view0 For HCR routing, hallucinated hook terms are more dangerous than hallucinated narrative—because hook terms drive elimination.

A routing-optimised node summary therefore has a defensible set of required fields (evidence-backed for the “why”, implementation-specific for the “how”):

* **Discriminative hooks**: a concise list of rare entities/IDs/terms (supported by keyphrase/IR utility). citeturn3search2  
* **Contrastive boundary cues**: sibling-separated coverage statements (motivated by contrastive summarisation framing). citeturn3search0turn3search8  
* **Multi-aspect coverage**: avoid single-theme collapse via diversity-aware selection (MMR principle). citeturn7search2  
* **Match-preserving representation**: optionally multi-vector embeddings to preserve token-level matches (late interaction evidence). citeturn3search3turn3search6  

## Handling multi-topic and cross-cutting content

Multi-topic content breaks the single-parent assumption. The empirical cluster-hypothesis diagnostics explain why: a large fraction of relevant documents may have no relevant neighbours, and relevant/non-relevant intermix locally. citeturn20view0 In HCR this manifests as cross-branch queries: evidence is split across siblings, but top-down routing picks only one branch and irrevocably drops the others.

There are only a few strategies that actually address this structurally; most “fixes” merely tune scoring.

Soft assignment is the most direct mitigation. RAPTOR explicitly uses soft clustering (nodes can belong to multiple clusters) because “individual text segments often contain information relevant to various topics.” citeturn22view0 In HCR, soft assignment is unusually cheap because leaves are external pointers: duplicating a pointer across two branches incurs minimal storage, but greatly reduces the probability of cross-branch elimination.

Graph augmentation is the second structural mitigation. GraphRAG-style pipelines create an entity–relationship graph so that cross-cutting entities form explicit links; community summaries then act as cross-topic routers. citeturn9view2turn23view0 The weakness is that community detection can ignore semantics and create mixed-theme communities, degrading summary distinctiveness; and global traversal is expensive. citeturn23view0turn24view0 That pushes the design towards **hybrids**: embedding-based tree for cheap routing + graph-based “cross links” for multi-hop or entity-centred queries.

Content decomposition is the third mitigation: split documents into smaller, closer-to-single-topic segments before clustering. RAPTOR’s unit is “text segments” clustered by embeddings, which is a practical form of decomposition even if not explicitly framed that way. citeturn22view0 For HCR, decomposition is especially important because leaves are pointers: you can route to *source+offset* (file path + symbol, table name + column, API endpoint + field) rather than to a monolithic document pointer.

The remaining mitigations are query-time rather than index-time: multi-path expansion (take top-k children per level), sibling backtracking, and “collapsed index fallback”. RAPTOR’s own results on collapsed retrieval are evidence that “search all nodes” can recover granularity matching when strict traversal would miss. citeturn20view4 The architectural implication for HCR is that you likely need an explicit **cross-branch safety valve** (multi-path or collapsed fallback) because cross-branch queries are not edge cases; they are an expected workload mode in broad knowledge bases. citeturn20view0turn22view0turn20view4

## Tree topology under a hard token budget

Within RB‑002’s preferred regime (shallow and wide), topology choices still matter because they determine how much ambiguity each summary must resolve and how often routing decisions must be made.

Balancedness is not cosmetic; it is a summary-quality lever. If one branch becomes disproportionately large, its summary must cover many themes, increasing sibling overlap and reducing discriminative hooks. Bisecting k‑means is argued to outperform regular k‑means partly because it tends to produce **uniformly sized clusters**, and the paper explicitly points to size imbalance as a reason regular k‑means performs worse. citeturn26view1 PERCH similarly treats balancedness as a maintenance target, using rotations to encourage it. citeturn31view0 For HCR, the practical inference is: **enforce balance constraints during construction and maintenance**, even if it slightly worsens within-cluster cohesion, because routing cares more about sibling separability than about strict compactness.

The second key topology insight is that strict traversal may be less valuable than multi-granularity representations. RAPTOR’s collapsed tree retrieval (flat over all nodes) is motivated as retrieving information at the “correct level of granularity” for a question, and it performed more consistently than tree traversal in their experiments. citeturn20view4 For HCR, this suggests an optimal structure is not a single tree but a **tree + collapsed view** (or a small forest of trees built from different signals), with traversal used when high-confidence and fallback used when routing uncertainty is high.

A third implication is that variable branching is likely necessary even within fixed depth. “Fixed b everywhere” forces unnatural partitions where some areas are over-split (thin evidence, low separability) and others are under-split (huge, vague summaries). The clustering literature’s emphasis on balancing and on split policies (which cluster to split, by what criterion) makes clear that these policy choices materially change outcomes, but does not provide workload-aware rules. citeturn26view1turn31view0 In practice, HCR should treat branch factor as a controlled resource: allocate more children where (a) the parent summary’s hook entropy is high, and (b) sibling separability can be demonstrated by routing metrics (see evaluation section).

## Maintaining the tree as the knowledge base grows

The research literature on *retrieval* trees does not deeply address incremental updates (consistent with RB‑001), but adjacent clustering work provides transferable mechanisms.

The cleanest incremental pattern is: **insert locally, repair locally, periodically rebuild globally**.

*Local insertion + local repair.* PERCH is explicitly an incremental tree builder: it routes new points to leaves and performs rotations to improve subtree purity and balancedness, providing a concrete model of “insert then repair” rather than “rebuild everything.” citeturn31view0 Even if HCR doesn’t adopt PERCH directly, the maintenance primitives are clear: detect “masking” / poor local structure and rotate or restructure near the insertion path rather than touching the entire tree. citeturn31view0

*Incremental summarisation structures.* BIRCH’s CF-tree is designed as an in-memory summary of the data distribution, explicitly enabling incremental maintenance, a local decision process (no global scans), and one-pass processing. citeturn28view0 This is conceptually identical to what HCR needs at internal nodes: a compact, incrementally maintainable representation that supports routing decisions without storing full text.

*Streaming microclusters + periodic macro rebuild.* CluStream’s division between online microclustering statistics and offline macroclustering is a formal recipe for handling drift: keep lightweight summaries online, periodically rebuild higher-level structure for accuracy. citeturn28view1 Applied to HCR, this suggests maintaining “micro-branches” for new content (fast insertion), and periodically re-clustering only the affected super-branch when drift is detected.

What remains genuinely open is *how to detect degradation in a routing-specific way* (not just “cluster cohesion got worse”). Generic similarity metrics can move without corresponding retrieval impact; conversely, retrieval failures can increase due to summary drift while average cohesion stays stable. The evaluation section gives practical, routing-aligned monitoring signals, but the literature does not yet offer consensus automatic policies for “when to rebuild.” citeturn29view0turn31view0turn28view1

## Evaluating tree quality independent of end-to-end retrieval

A useful evaluation suite needs to answer: “Is this a good routing index?” without conflating it with scorer selection, prompt design, or generation quality.

Three families of intrinsic metrics have direct relevance:

**Relevance-neighbourhood diagnostics (query-aware).** Voorhees’ nearest-neighbour test measures how often relevant documents have relevant neighbours, directly probing the cluster hypothesis in a way that predicts whether cluster routing is plausible. citeturn20view0 Smucker & Allan argue that NN is insufficient alone and propose a global measure over document networks to better capture navigability/retrieval utility. citeturn29view0 For HCR, these become routing metrics if you replace “document relevance” with “leaf relevance under a query workload” and evaluate at each internal node: do relevant leaves concentrate under a small set of children given the queries that hit this parent?

**Hierarchy-structure quality (query-agnostic, but task-aligned).** Dendrogram purity is a holistic measure used in hierarchical clustering evaluation; PERCH explicitly targets high dendrogram purity and balancedness under online insertion. citeturn31view0 Dendrogram purity does not guarantee retrieval performance, but it provides a structural sanity check: if dendrogram purity is low under reasonable labels (topics, sources, entity families), routing will be unstable.

**Reference-free taxonomy evaluation (structure-only, no labels).** A recent paper proposes two reference-free taxonomy metrics: (i) robustness via correlation between semantic similarity and taxonomic similarity, and (ii) logical adequacy using NLI for parent–child edges; they report correlation with F1 against ground-truth taxonomies and show these metrics can predict downstream hierarchical classification performance. citeturn31view1 Another recent proposal, the Taxonomy Probing Metric (TPM), directly tests whether the taxonomy is *unambiguously differentiable in embedding space* by checking whether each child matches its correct parent and vice versa, and reports that simpler embedding-similarity “coherence” metrics do not correlate with downstream performance in their setting. citeturn30view2

For HCR specifically, the most actionable “routing-native” metrics are derivable from these ideas, even if not standardised in the literature:

* **Sibling distinctiveness score:** measure how separable child summaries are under the scoring model (e.g., margin between top-1 and top-2 child over a probe set). Motivation: TPM’s “choose correct node among many” framing. citeturn30view2  
* **Hook coverage / leakage:** measure whether high-IDF terms/entities from descendants appear in the ancestor’s hook list; penalise hook overlap across siblings. Motivation: keyphrase/IR utility and the goal of sibling differentiation. citeturn3search2  
* **Cross-branch risk rate:** fraction of queries where relevant leaves lie in >1 sibling branch at a given parent (requires a query workload or synthetic probes). Motivation: Voorhees-style diagnostics of relevance scattering and intermingling. citeturn20view0  

The key is that these metrics evaluate the *index structure* (and summary fields) before you ship changes into the runtime scoring cascade.

## Implications of external source pointer leaves

HCR’s leaf nodes are not content chunks; they are *pointers to external sources*. That changes both construction and maintenance.

First, you cannot assume full text is always available at build time (APIs may be gated; repos may be private; datasets may be large). The tree must therefore be constructible from **resource descriptors**: metadata, schemas, directory structures, sampled snippets, and derived statistics (entities/IDs, keyphrases, term histograms). This is conceptually aligned with BIRCH’s CF idea: store a compact summary that is “sufficient” for decisions instead of retaining all points. citeturn28view0 The design target becomes: “what is the smallest descriptor that still preserves routing hooks?”

Second, external sources drift. Unlike static corpora, a repo’s file tree, a database schema, or an API surface can change. Streaming clustering work suggests a stable recipe: maintain lightweight online summaries and periodically rebuild higher-level structure to reflect drift. citeturn28view1 For HCR, the analogue is: (a) keep leaf descriptors updated (e.g., weekly term/entity stats), (b) maintain parent summaries as aggregations over these descriptors, and (c) trigger subtree rebuild when routing diagnostics degrade.

Third, the token budget (<400 tokens) interacts with external pointers in a useful way: duplicating a leaf pointer across multiple branches to mitigate multi-topic routing is cheap in storage, and it can be cheaper than building complex multi-parent DAGs. RAPTOR’s explicit motivation for soft clustering—segments belonging to multiple clusters—becomes even more attractive when leaves are pointers rather than stored content. citeturn22view0

Finally, cost discipline becomes more important than in “all-text” RAG. Graph-based pipelines offer strong cross-cutting representations but can be prohibitively expensive if they require exhaustive traversal or heavy LLM processing over many communities; a reported GraphRAG-like global analysis example is ~\$650 and 106M tokens for 100 questions in one dataset setting. citeturn23view0turn24view0 For an agentic system with continual growth, this cost profile strongly favours: LLM assistance where it produces maximal structural lift (boundary-setting summaries, ambiguity resolution on hard items), and embedding/lexical methods for the bulk partitioning.

A construction strategy that follows from the evidence above (evidence-backed components plus the known frontier) is:

* **Primary tree:** top-down divisive clustering constrained to d=2–3, b=8–12, with explicit balance constraints (supported by bisecting k‑means’ uniform-size argument and PERCH’s balancedness goal). citeturn26view1turn31view0  
* **Soft assignment layer:** duplicate pointers (or allow multi-parent membership) for items with high assignment uncertainty (supported by RAPTOR’s soft clustering rationale). citeturn22view0  
* **Summary schema optimised for routing:** hook lists + contrastive boundaries + multi-aspect selection, optionally with match-preserving representations (motivated by query-biased summaries, contrastive summarisation, MMR, and late interaction retrieval evidence). citeturn20view2turn3search0turn7search2turn3search3  
* **Cross-branch safety valve:** collapsed/fallback retrieval over multi-level summaries when routing confidence is low (supported by RAPTOR’s collapsed-tree results). citeturn20view4  
* **Maintenance:** incremental insertion with local repairs + periodic subtree rebuild under routing-native diagnostics (supported by PERCH/BIRCH/CluStream maintenance primitives, but workload-aware triggers remain an open problem). citeturn31view0turn28view0turn28view1