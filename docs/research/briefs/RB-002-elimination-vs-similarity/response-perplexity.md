# RB-002: Theoretical Basis — Perplexity Response

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

### 0. Short answer

- **Hierarchy helps as a representation**, but **strict top‑down elimination is only reliably better than flat retrieval under very strong conditions**: very tight, tree‑aligned clusters; low, well‑calibrated scoring noise at every level; queries that are “localized” to a small number of branches; and large enough budgets (tokens / candidates) within each surviving subtree.
- **In realistic LLM RAG regimes, these conditions usually fail**, so:
    - Early pruning errors compound roughly multiplicatively with depth.
    - Relevant information often spans branches or appears at multiple granularities.
    - Summaries are lossy channels.
- Under these conditions, **“collapsed tree” retrieval (flat similarity over enriched multi‑level nodes) is theoretically favored**: it uses the hierarchy as a representation prior, but not as a hard search constraint. This matches RAPTOR’s empirical finding that collapsed‑tree retrieval beats strict traversal.[^1_1]

The rest of the answer builds a formal picture of *why* this happens and when HCR‑style elimination can still win.

***

## 1. Formalizing the setting

Consider:

- Corpus chunks $D = \{d_1, \dots, d_n\}$.
- A hierarchical tree $T$ whose leaves are chunks and whose internal nodes are LLM summaries over clusters of descendants (RAPTOR‑style).[^1_2][^1_1]
- A query $q$ drawn from some distribution $\mathcal{Q}$.
- A relevance label $Y_i(q) \in \{0,1\}$ for each leaf $d_i$.

Three retrieval policies:

1. **Flat similarity (FS)**
k‑NN over leaf embeddings; return top‑$k$ leaves under a token budget $T_{\text{tok}}$.
2. **Enriched flat (collapsed tree, CT)**
k‑NN over *all* node embeddings (internal + leaves); return top‑$k$ nodes, then expand to text up to $T_{\text{tok}}$.[^1_1]
3. **Hierarchical elimination (HE)**
Start at root. At each level $l$, score children of the current open nodes, keep top‑$k_l$ nodes per level, discard others. Only leaves in surviving subtrees contribute to the final context.

Key metrics:

- **Recall**: fraction of relevant leaves $d_i$ for which $Y_i(q)=1$ that appear in the final context.
- **Precision / utility**: fraction (or expected utility) of retrieved tokens that are relevant/useful.
- **Token efficiency**: utility per token within a hard budget $T_{\text{tok}}$.

HE and CT differ mainly in ***when*** they commit to a small set of branches: HE commits *early, sequentially*; CT defers commitment and lets a single global scorer pick across the whole enriched representation.

***

## 2. Information‑theoretic perspective

### 2.1 Trees as decision codes (the “Twenty Questions” analogy)

Classical information theory views an optimal decision tree as a code for identifying an unknown object $X$ drawn from distribution $\pi$. The best possible expected number of yes/no questions is lower bounded by entropy $H(X)$, and there exist decision trees whose average cost is within an additive constant of $H(\pi)$.[^1_3][^1_4][^1_5]

- A **well‑designed decision tree** (queries = internal node tests) can be *information‑theoretically optimal*: average cost $\approx H(\pi)$.
- The key is that each question is chosen to maximize information gain about $X$ under $\pi$.

Mapping to retrieval:

- Let $X$ be “which leaf(s) are relevant for $q$?”.
- The tree $T$ plus its scoring policy defines a decision process that, given $q$, selects a path (or beam of paths) to some leaves.
- HE is analogous to a **fixed, pre‑designed decision tree** whose questions are “which child cluster is most similar to $q$?”.

In the *idealized* case:

- The tree structure and scoring function are designed to approximate information‑gain–maximizing questions over the distribution $\mathcal{Q}$.
- Then HE can approach the information‑theoretic optimum (logarithmic in number of leaves, like hierarchical softmax).[^1_6][^1_7][^1_8]

But this requires very strong alignment between:

1. Cluster boundaries and the distribution of relevance labels.
2. Query distribution $\mathcal{Q}$ and the same clustering.
3. Scorers that make nearly Bayes‑optimal routing decisions.

In modern RAG, none of these are guaranteed.

### 2.2 Summaries as a lossy channel

Let:

- $L$ be the random variable describing the full descendant text of a node.
- $S = f(L)$ be the LLM summary embedding (internal node representation).
- $Q$ the query.

From information theory:

- $(Q, Y) \to L \to S$ is a Markov chain (summary depends only on the text).[^1_1]
- By the **data‑processing inequality**,
$I(Q; S) \le I(Q; L)$.
Summaries cannot increase mutual information about the query or relevance; at best they preserve some of it.

For HE, early routing decisions are made on $S$ (summaries):

- If $S$ is not a **sufficient statistic for relevance** conditional on $L$ — in other words, if $p(Y|Q,L) \ne p(Y|Q,S)$ — then routing based on $S$ discards information relative to routing on $L$.
- In practice, LLM summaries are *not* sufficient statistics; they are lossy abstractions.

For CT:

- All nodes (including leaves) are in the candidate set.
- The model can still select leaves directly when summary‑level information is too coarse, or intermediate nodes when high‑level abstraction is sufficient.[^1_1]

Thus, from a pure information‑theoretic standpoint:

- **HE is only lossless if each summary is (approximately) sufficient for the relevance of its descendants.**
- Otherwise, **CT strictly dominates** HE in terms of information availability to the scorer:
    - It has access to all leaf representations plus their abstractions.
    - HE forces decisions through a lossy bottleneck at each level.


### 2.3 When can elimination be lossless or bounded‑loss?

In principle, elimination can be (near) lossless if:

1. **Strong cluster hypothesis holds** at each level: relevant leaves for typical queries almost always live in a small number of clusters, and those clusters are *clean* (few non‑relevant leaves) and well‑separated from others.[^1_9][^1_10][^1_2]
2. **Summaries are relevance‑sufficient**: for almost all queries in $\mathcal{Q}$, the ranking of child summaries by similarity is consistent with the ranking of their best descendant leaves by relevance.
3. **Scoring noise is small and calibrated**: the probability that a subtree containing any relevant leaf is pruned at its first branching point is very low ($\varepsilon \ll 1$).
4. **Search depth is modest**: so that multiplicative error accumulation across levels remains acceptable (see §4).

These conditions are analogous to the assumptions under which hierarchical softmax matches flat softmax accuracy while gaining logarithmic speed‑ups: the internal decisions must closely approximate the true posterior over leaves.[^1_7][^1_8][^1_11][^1_6]

When any of these assumptions breaks (cross‑branch relevance, lossy summaries, noisy scorers, deep trees), information‑theoretic arguments alone suggest that **flat search over all enriched representations (CT) should outperform strict HE**.

***

## 3. Decision‑ and search‑theoretic view

### 3.1 Sequential hypothesis testing analogy

Model each branch decision as a binary hypothesis test:

- $H_1$: “this subtree contains at least one relevant leaf”.
- $H_0$: “no descendant of this node is relevant”.

Given a query $q$, a scoring function $s(\text{node}, q)$, and a threshold, the system accepts or rejects $H_1$ at each node.

From **sequential hypothesis testing** (e.g. Wald’s Sequential Probability Ratio Test), one can derive optimal policies for when to stop gathering evidence and accept/reject a hypothesis, given desired Type I/II error rates and cost of additional observations.[Classic SPRT theory; no RAG‑specific papers exist.]

HE implicitly implements a *very aggressive* policy:

- It makes a **single observation** (score) per node and **commits immediately**: subtrees that lose at that level are never revisited.
- There is no sequential refinement per node; all “budget” is in traversing deeper, not revisiting or verifying earlier decisions.

Under classical SPRT theory, this is only optimal if:

- The single observation is extremely informative (likelihood ratio far beyond thresholds), or
- The cost of additional evidence is prohibitive.

In RAG:

- LLM similarity scores are noisy and context‑dependent; LATTICE’s need for cross‑branch calibration is exactly empirical evidence of this.[LATTICE paper, as you summarized; no tight formal bounds yet.]
- So **HE is operating far from the conditions where one‑shot elimination is optimal** from a decision‑theoretic standpoint.


### 3.2 Branch‑and‑bound / alpha‑beta pruning analogy

In game search, **alpha‑beta pruning** is optimal among algorithms that compute exact minimax values: it prunes branches when bounds prove they cannot improve the final outcome.[^1_12][^1_13][^1_14]

Key properties:

- Pruning is **sound**: pruned branches provably cannot contain the optimal solution.
- The tree is *exactly* the search space; evaluation function satisfies known inequalities that justify pruning.

For HE in retrieval:

- There are *no exact bounds*; similarity scores give **no guarantee** that pruned branches cannot contain relevant information.
- So HE is more like **approximate branch‑and‑bound with unreliable bounds**—which has no optimality guarantees and can easily miss optimal solutions.

In contrast:

- CT does no pruning at the tree level: all nodes are in the candidate set; only the global similarity ranking matters.
- Multi‑stage retrieval cascades in IR explicitly set per‑stage recall constraints and model the tradeoff between cost and error, often guaranteeing that early stages preserve a target recall level (e.g. learn cascades with explicit cost and effectiveness tradeoffs).[^1_15][^1_16][^1_17]
- That line of work is essentially **“elimination under recall constraints”**; HE as typically implemented does *not* enforce such constraints.

***

## 4. Error propagation in hierarchical pruning

Consider a depth‑$d$ tree. Suppose:

- At level $l$, the probability that *all branches containing relevant leaves* are pruned is at most $\varepsilon_l$.
- Equivalently, per‑level recall (conditioned on there existing relevant descendants) is $r_l = 1 - \varepsilon_l$.

Then, assuming independence or using a union bound:

- **Overall recall lower bound** (for any relevant leaf):

$$
R_{\text{HE}} \ge \prod_{l=1}^d (1 - \varepsilon_l) \approx 1 - \sum_{l=1}^d \varepsilon_l
$$

for small $\varepsilon_l$. In the worst case with constant $\varepsilon$:

$$
R_{\text{HE}} \ge (1 - \varepsilon)^d
$$

So:

- Even modest per‑level error rates compound multiplicatively with depth.
- With $\varepsilon=0.1$ and $d=5$, worst‑case recall bound is $(0.9)^5 \approx 0.59$.

This is directly analogous to recent analyses of error propagation in multi‑step chain‑of‑thought reasoning, where per‑step error probability $\varepsilon$ yields failure probability $1 - (1-\varepsilon)^n$ after $n$ steps.[^1_18]

This is *structural* to any sequential elimination scheme:

- Each irreversible decision layer multiplies the probability of preserving all necessary information.
- Beam search / multi‑path traversal (keeping $B$ branches per level) can mitigate this, effectively replacing $\varepsilon_l$ with a smaller value that depends on beam width, but the exponential depth dependence remains.

Decision tree generalization theory echoes this:

- Bounds on misclassification error of decision trees depend on both tree depth and breadth (number of internal nodes), and can deteriorate with increasing depth unless node tests are very accurate.[^1_19][^1_20]
- These results are for supervised classification rather than retrieval, but the mechanism—**error accumulation along paths**—is shared.

By contrast:

- **FS** and **CT** make a *single global ranking* decision; their error behavior is dominated by *the quality of the scoring function*, not path length.
- There is no additional multiplicative factor from depth.

So unless HE buys you *substantial* gains in score quality or efficiency, its intrinsic error‑propagation disadvantage is hard to overcome.

***

## 5. The cluster hypothesis: conditions and limits

The **cluster hypothesis** in IR: “documents in the same cluster behave similarly with respect to relevance to information needs.”[^1_21][^1_10]

Classic and later work shows:

- Jardine \& van Rijsbergen (1971) showed that hierarchic clustering can match the effectiveness of linear associative retrieval (flat term‑based ranking) while improving efficiency.[^1_2][^1_9]
- Voorhees (1985) and follow‑ups (“The Cluster Hypothesis Revisited”) found that absolute retrieval performance depends on pairwise similarity of relevant documents, but **retrieving entire clusters is usually worse than retrieving individual documents from within clusters**.[^1_22][^1_10]
- Later work on query‑specific hierarchic clustering again found that cluster search can be effective, but effectiveness depends heavily on how tightly relevant documents cluster and on not treating clusters as monolithic retrieval units.[^1_23]

Translating this to modern embedding‑based RAG:

The cluster hypothesis holds best when:

1. **Single‑facet topics**: queries correspond to one dominant semantic facet, and relevant content lives in a tight region of embedding space.
2. **Low label entropy per cluster**: cluster purity (w.r.t. relevance) is high.
3. **Low cross‑cutting structure**: documents are not heavily multi‑topic or multi‑label.

It breaks (or weakens) when:

- **Cross‑branch / multi‑hop queries**: answer requires combining evidence from multiple topics or document sections (e.g., cause in one section, effect in another), which often land in different clusters.
- **Facet / role symmetry**: two semantically similar passages play different roles (e.g., pro vs con) that embeddings fail to separate.
- **Adversarial or dense knowledge graphs** where relevant facts are thinly spread across the corpus.

Under these realistic conditions:

- A **tree that commits to one or few branches per level is structurally misaligned** with the relevance geometry: relevant leaves are not concentrated enough within a single branch.
- Conversely, **using the tree as a representation but retrieving on individual nodes (CT) is aligned with Voorhees’ observation**: exploit cluster structure but still rank *within* it.[^1_10][^1_22]

This is exactly what RAPTOR’s collapsed tree does.

***

## 6. Explaining RAPTOR’s collapsed‑tree result

RAPTOR explicitly compares tree traversal vs collapsed‑tree retrieval and finds that **the collapsed tree approach “consistently performs better,”** attributing this to its flexibility to retrieve information “at the correct level of granularity” for each question.[^1_1]

Theoretical explanation:

1. **Data‑processing / lossy summaries**
Tree traversal must pass through higher‑level summaries that discard some information about descendants. If high‑level summaries are not perfectly aligned with relevance for a given query, early pruning can drop relevant leaves that would otherwise have high similarity if evaluated directly.[^1_1]
2. **Granularity mismatch**
Under traversal with fixed $k$ per level, the **ratio of high‑level vs low‑level nodes in the final context is fixed** by the tree parameters, not by the query.[^1_1]
    - Some queries benefit from coarse summaries (global theme).
    - Others require fine‑grained evidence (specific paragraph).
CT lets the scorer pick whichever node level (summary vs leaf) best matches the query.
3. **Cross‑branch queries and multi‑hop reasoning**
Traversal tends to **focus on one or a few subtrees**; cross‑branch relevance is a known failure mode. CT can freely select nodes from multiple branches since all are ranked in a single flat pool.
4. **Rank fusion over multiple views**
CT effectively does implicit *rank fusion* across multiple representations of the same material (leaf, mid‑level summary, top summary). Rank fusion is known to improve recall and robustness because different representations capture different aspects of relevance.[^1_16]
5. **Error propagation vs single‑shot ranking**
Traversal incurs multiplicative per‑level error; CT has a single ranking error term (from the embedding similarity function). Given noisy scorers, **CT’s error profile is better conditioned**, especially for deeper trees.

Formal conditions under which CT should outperform traversal:

- **Lossy, non‑sufficient summaries** (almost always true in practice).
- **Moderate to high depth**: so that multiplicative error hurts traversal.
- **Cross‑branch or multi‑hop queries** that require information from multiple clusters.
- **Queries with heterogeneous granularity needs** (sometimes you want a whole chapter summary, other times a particular sentence).
- **Scorers with non‑trivial noise and miscalibration**, so that per‑level elimination is risky.

Conditions under which strict traversal could win:

- **Extreme scale or latency constraints**: when k‑NN over all nodes is too expensive, but per‑level pruning reduces search space dramatically.
- **Very strong cluster hypothesis**: relevant content lies almost entirely in one small subtree, and cross‑branch relevance is rare (e.g., highly structured technical manuals partitioned by subsystem).
- **Tree jointly learned with the encoder** to approximate optimal decision trees or hierarchical softmax, so that internal decisions are close to Bayes‑optimal and summary representations are nearly sufficient.[^1_8][^1_11][^1_6][^1_7]
- **Generous per‑branch context budget**: once the right branch is selected, many leaves within it can be retrieved, amortizing early commitment.

In short: **RAPTOR’s collapsed‑tree result is what information theory and classical IR would predict once you acknowledge lossy summaries, noisy scorers, cross‑branch relevance, and depth‑dependent error.**[^1_9][^1_22][^1_10][^1_2][^1_1]

***

## 7. Hybrid strategies: theory and implications

Hybrid strategies sit between HE and CT. Two broad families:

### 7.1 Coarse filtering + flat local search

Procedure:

1. Use a **shallow hierarchy** (or only top $L$ levels) to select a **set of candidate subtrees**.
2. Flatten all nodes (or leaves) in these subtrees and run **flat similarity within the union**.

Theoretical rationale:

- This mirrors **multi‑stage retrieval cascades** in IR: cheap, high‑recall first stage → expensive, high‑precision second stage.[^1_17][^1_15][^1_16]
- Suppose stage‑1 recall is $R_1$ (probability that any relevant doc is in the candidate set of subtrees), and stage‑2 local ranking has recall $R_2$ within that candidate set. Then overall recall is $R_1 R_2$.
- If stage‑1 is designed to have very high recall, e.g. $R_1 \ge 0.99$, the product is dominated by stage‑2, and you inherit the robustness of flat search while reducing the search space.

Conditions for advantage over pure CT:

- Very large corpora where CT is too slow or memory‑heavy.
- Hierarchy that is reliable enough at *coarse* levels to cull large obviously irrelevant regions without much risk (small depth, small $\varepsilon_l$ there).
- Token budget or compute constraints that favor reducing candidate set size before full scoring.


### 7.2 Parallel traversal / beam search

Instead of a single path:

- Keep a **beam of size $B$** at each level (top‑$B$ branches overall or per parent).
- This turns the per‑level “catastrophic pruning” probability from $\varepsilon_l$ into something more like the probability that *all* $B$ branches miss all relevant subtrees.

If each branch independently has probability $p_l$ of containing a relevant leaf (crude), then:

- Probability that at least one branch in the beam keeps a relevant subtree is $1 - (1-p_l)^B$.
- This can dramatically reduce effective $\varepsilon_l$, making the overall $R_{\text{HE}}$ closer to 1 even for moderate depth.

This is analogous to:

- **Beam search in sequence decoding**: exploiting multiple high‑probability trajectories to mitigate local scoring errors.
- **Rank fusion**: combining multiple candidate lists increases recall and reduces per‑query variance.[^1_16]

Theoretical basis:

- Still no exact optimality guarantees (bounds are heuristic), but error accumulation is softened from $(1-\varepsilon)^d$ toward a gentler curve governed by beam size and score distribution.

***

## 8. Token budget as a hard constraint

Introduce a constraint:

- Retrieved context length $\le T_{\text{tok}}$.

This creates a **knapsack problem**:

- Each node $i$ has:
    - Cost $c_i$ (tokens).
    - Utility $u_i(q)$ (expected contribution to answer quality).
- Objective: choose a subset $S$ maximizing $\sum_{i\in S} u_i(q)$ s.t. $\sum_{i\in S} c_i \le T_{\text{tok}}$.

How FS, CT, HE relate to this:

- **FS**: implicitly approximates $u_i$ with similarity scores over leaves; typically not cost‑aware, so it may choose redundant or verbose chunks that blow the budget.
- **CT**: has more choices (summaries vs leaves) but still usually ranks by similarity, not explicit utility‑per‑token; yet summaries allow *higher information density per token*, which can be good under tight budgets.
- **HE**: imposes additional *structural constraints* on feasible subsets $S$: you can only pick leaves from a small number of branches; high‑level summaries of those branches may be “forced” into the context even if low‑utility for this query.

Token budget can make elimination **more** attractive when:

- The tree is **well‑aligned**: a small number of branches contain almost all relevant info; high‑level summaries are genuinely high information‑density; deeper nodes refine without redundancy.
- Then HE focuses tokens on a coherent region of the corpus, reducing fragmentation and redundancy.

But token budget makes elimination **less** attractive when:

- Relevant information is **spread across branches**: HE spends budget to deepen one branch and loses out on small but crucial segments elsewhere.
- Summaries are **noisy or generic**, so including them consumes tokens without proportional utility; but HE is biased toward including them (since they are the routing signal).
- CT can instead directly choose a mix of mid‑level and leaf nodes that maximizes similarity/utility per token across the entire tree.

So:

- Under a tight token budget, **CT’s flexibility in picking nodes at arbitrary levels and locations generally yields a better approximation to the knapsack optimum**.
- HE only wins if the hierarchy and summarization are so good that “stick to one or few branches and go deep” is near‑optimal for most queries.

***

## 9. Summary of conditions where elimination vs similarity wins

Putting it together:

### When hierarchical elimination (HE) can outperform flat similarity / CT

You expect HE to be superior **only if all of the following roughly hold**:

1. **Tree quality / cluster hypothesis**
    - Clusters are tight and well‑separated; relevant leaves for typical queries lie in one or very few subtrees.[^1_23][^1_10][^1_2][^1_9]
    - Cross‑branch and multi‑hop queries are rare or can be handled within a single subtree (e.g. document‑local reasoning only).
2. **Summaries and scorers**
    - Summaries at each node are highly informative and close to sufficient for the relevance of their descendants.
    - Per‑level misrouting probability $\varepsilon_l$ is very small, and depth $d$ is modest, so $R_{\text{HE}} \approx \prod (1-\varepsilon_l)$ remains high.
3. **Cost / scale**
    - Global k‑NN over all nodes (CT) is computationally expensive, and per‑level pruning yields significant savings.
    - The cost advantage outweighs the occasional recall loss.
4. **Token budget alignment**
    - Most queries benefit from *concentrated* context drawn from a single coherent region of the tree; high‑level summaries plus a few detailed leaves are enough.
    - Fragmented context across many branches hurts answer quality more than slightly lower recall within the main branch.

These are *exactly* analogous to the classical conditions under which hierarchical softmax and clustering‑based search match the effectiveness of flat methods while improving efficiency.[^1_6][^1_7][^1_8][^1_10][^1_2][^1_9]

### When enriched flat retrieval (CT) or flat leaf retrieval dominates

CT or FS are favored when:

1. **Cluster hypothesis only partially holds**
    - Relevant content commonly spans multiple clusters / branches.
    - Documents are multi‑topic and relevance cuts across the tree partition.
2. **Summaries are lossy and scorers noisy**
    - Early decisions based on internal nodes have non‑trivial error; depth amplifies this to substantial recall loss.
    - No strong calibration guarantees across branches (as LATTICE empirically observes).
3. **Varied granularity needs**
    - Some queries need high‑level summaries; others need specific snippets.
    - A fixed ratio of levels (as in tree traversal with fixed $k$ per level) is structurally suboptimal.[^1_1]
4. **Token budget is tight**
    - It is more important to spend tokens on the *best nodes anywhere* than on maintaining tree‑structured coherence.
    - Summaries are sometimes less useful than carefully chosen leaves from multiple parts of the corpus.

Empirically, RAPTOR’s collapsed tree outperforming traversal falls directly into this regime, and the theory above explains why this is expected.[^1_22][^1_10][^1_2][^1_9][^1_1]

***

## 10. Gaps and what a proper theory for HCR would need

Current theory is **fragmentary and indirect**:

- Information theory gives tools for:
    - Optimal decision trees (Twenty Questions).[^1_4][^1_5][^1_3]
    - Data‑processing and rate–distortion (lossy summaries).
- Decision and search theory gives tools for:
    - Sequential hypothesis testing and optimal stopping.
    - Branch‑and‑bound and cascades with explicit cost–error tradeoffs.[^1_13][^1_14][^1_12][^1_15][^1_17][^1_16]
- IR theory covers:
    - Cluster hypothesis and its empirical limits.[^1_10][^1_2][^1_9][^1_22][^1_23]
    - Rank fusion and recall‑oriented retrieval.[^1_16]

But **there is no formal, end‑to‑end theory of LLM‑based hierarchical retrieval** that:

- Models LLM summarization as a stochastic lossy channel.
- Models embedding similarities and LLM scoring as noisy, possibly biased estimators of relevance.
- Derives **explicit recall/precision bounds** for hierarchical traversal vs global k‑NN under those noise models.
- Incorporates a **token budget constraint** and treats context selection as knapsack optimization over tree‑structured candidates.
- Characterizes precisely the corpus and query‑distribution conditions under which trees provide net benefits.

A proper theory for HCR would need to:

1. Specify a generative model for:
    - Corpus clustering structure.
    - Query distribution and relevance labels.
    - Summarization and embedding noise.
2. Define HE, CT, and FS as policies over this model.
3. Prove **non‑asymptotic bounds** on:
    - Recall loss and error propagation for HE as functions of depth, branching factor, and noise parameters.
    - Relative performance of CT vs HE under varying cluster tightness and cross‑branch relevance.
    - Utility/token tradeoffs under explicit budgets.
4. Calibrate these models empirically on real RAG benchmarks.

Until such a theory exists, the safest stance—consistent with both information theory and classical IR—is:

- **Use hierarchies primarily as representation/enrichment (like RAPTOR’s collapsed tree),** not as hard elimination structures, unless you have strong empirical evidence that your corpus + queries satisfy the stringent conditions under which hierarchical elimination is theoretically favored.
<span style="display:none">[^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43]</span>

<div align="center">⁂</div>

[^1_1]: https://proceedings.iclr.cc/paper_files/paper/2024/file/8a2acd174940dbca361a6398a4f9df91-Paper-Conference.pdf

[^1_2]: https://www.sciencedirect.com/science/article/abs/pii/0020027171900519

[^1_3]: https://yuvalfilmus.cs.technion.ac.il/Papers/frugal.pdf

[^1_4]: https://yuvalfilmus.cs.technion.ac.il/Manuscripts/MSC-2018-01.pdf

[^1_5]: https://yuvalfilmus.cs.technion.ac.il/Students/YuvalDaganMSc.pdf

[^1_6]: https://www.lateral.io/resources-blog/semantic-trees-hierarchical-softmax

[^1_7]: https://www.ruder.io/word-embeddings-softmax/

[^1_8]: https://www.cl.uni-heidelberg.de/courses/ss19/emb/material/sgns.pdf

[^1_9]: https://www.sciencedirect.com/science/article/pii/0020027171900519

[^1_10]: https://nlp.stanford.edu/IR-book/html/htmledition/clustering-in-information-retrieval-1.html

[^1_11]: https://arxiv.org/pdf/1707.08588.pdf

[^1_12]: https://homepage.iis.sinica.edu.tw/~tshsu/tcg/2019/slides/slide6.pdf

[^1_13]: https://stanford-cs221.github.io/autumn2022-extra/modules/games/alpha-beta-pruning.pdf

[^1_14]: https://ftp.cs.ucla.edu/pub/stat_ser/solution-branching-factor.pdf

[^1_15]: http://rueycheng.com/paper/efficient-cost-aware-cascade.pdf

[^1_16]: https://rodgerbenham.github.io/thesis.pdf

[^1_17]: https://dl.acm.org/doi/10.1145/3589334.3645523

[^1_18]: https://openreview.net/pdf/4c267f1cbe03ee6ce71028722496731661058364.pdf

[^1_19]: https://www.ijcai.org/Proceedings/07/Papers/163.pdf

[^1_20]: http://papers.neurips.cc/paper/1340-generalization-in-decision-trees-and-dnf-does-size-matter.pdf

[^1_21]: https://en.wikipedia.org/wiki/Cluster_hypothesis

[^1_22]: https://dl.acm.org/doi/pdf/10.1145/253495.253524

[^1_23]: https://www.sciencedirect.com/science/article/abs/pii/S0306457301000486

[^1_24]: https://towardsai.net/p/l/decision-tree-splitting-entropy-vs-misclassification-error

[^1_25]: https://www.appliedaicourse.com/blog/alpha-beta-pruning-in-artificial-intelligence/

[^1_26]: https://www.sciencedirect.com/science/article/abs/pii/S0020019017301205

[^1_27]: http://arxiv.org/pdf/2405.16753.pdf

[^1_28]: https://arxiv.org/html/2602.07453v1

[^1_29]: https://www.geeksforgeeks.org/artificial-intelligence/alpha-beta-pruning-in-adversarial-search-algorithms/

[^1_30]: https://classic.csunplugged.org/documents/activities/information-theory/unplugged-05-information_theory.pdf

[^1_31]: https://openreview.net/forum?id=GN921JHCRw\&noteId=rquBHNygEX

[^1_32]: https://www.themoonlight.io/zh/review/raptor-recursive-abstractive-processing-for-tree-organized-retrieval

[^1_33]: https://dev.to/lucash_ribeiro_dev/graph-augmented-hybrid-retrieval-and-multi-stage-re-ranking-a-framework-for-high-fidelity-chunk-50ca

[^1_34]: https://iclr.cc/virtual/2024/poster/19034

[^1_35]: https://arxiv.org/html/2503.09492v3

[^1_36]: https://liner.com/review/raptor-recursive-abstractive-processing-for-treeorganized-retrieval

[^1_37]: https://eric.ed.gov/?id=EJ053526

[^1_38]: https://onlinelibrary.wiley.com/doi/10.1155/2023/2769757

[^1_39]: https://building-babylon.net/2017/08/01/hierarchical-softmax/

[^1_40]: https://discovery.researcher.life/article/the-cluster-hypothesis-revisited/fbf5b109f2663cf392e9bc77aadc6e3c

[^1_41]: https://zilliz.com/ai-faq/what-are-the-challenges-of-keeping-a-generation-grounded-when-using-multistep-retrieval-and-how-might-errors-compound-over-multiple-steps

[^1_42]: https://milvus.io/ai-quick-reference/what-are-the-challenges-of-keeping-a-generation-grounded-when-using-multistep-retrieval-and-how-might-errors-compound-over-multiple-steps

[^1_43]: https://par.nsf.gov/servlets/purl/10621593

