# RB-001: Prior Art Survey — GPT Response

# Prior Art Survey: Hierarchical and Tree-Based Retrieval for LLM Context Delivery

## What “hierarchical retrieval” means in the LLM era

In LLM context delivery, “hierarchical retrieval” is used in two materially different ways: (a) **hierarchical representations** (multi-level summaries / parent-child chunk graphs / community hierarchies) that aim to improve *semantic granularity and coherence* of retrieved evidence, and (b) **hierarchical search** (top-down traversal with pruning) that aims to reduce the *search cost* (often described as logarithmic in corpus size) by eliminating large parts of the corpus early. citeturn13view2turn9view1turn16view1

A practical consequence is that many “tree-based” systems do build trees, but do not actually *search* them hierarchically at inference time: they frequently collapse the tree back into a flat candidate set and perform similarity search over all nodes (multi-scale retrieval, but not logarithmic search). RAPTOR explicitly reports this as its preferred querying strategy on a subset of QASPER. citeturn13view2

“Retrieval by elimination” (your HCR framing) corresponds most closely to **beam / best-first traversal** where each level’s candidate branches are scored, pruned, and expanded, iteratively, until leaves (or a stopping criterion) are reached. LATTICE formalises this pattern explicitly as an LLM-guided search over a semantic tree, including a beam of candidates per step. citeturn8view2turn9view1turn17view2

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["RAPTOR tree organized retrieval diagram","LATTICE LLM-guided hierarchical retrieval semantic tree figure","LlamaIndex Tree Index diagram traversal root to leaf","B-tree data structure diagram"]}

## LLM-era systems and papers using tree-structured or elimination-based retrieval

### RAPTOR: recursive summarisation trees for multi-level retrieval (peer-reviewed)

**RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval** (ICLR 2024; arXiv submitted 31 Jan 2024) by entity["people","Parth Sarthi","nlp researcher"], entity["people","Salman Abdullah","ml researcher"], entity["people","Aditi Tuli","ml researcher"], entity["people","Shubh Khanna","ml researcher"], entity["people","Anna Goldie","ml researcher"], and entity["people","Christopher D. Manning","nlp researcher"]. citeturn13view3turn0search10

Mechanics (as described by the authors):
- **Tree construction (offline):** recursively embed, cluster, and summarise chunks, building a bottom-up tree whose internal nodes are summaries at increasing abstraction levels. citeturn13view3turn0search4  
- **Querying / traversal:** RAPTOR evaluates both top-down tree traversal and a “collapsed tree” strategy. In the *collapsed tree* method, all nodes across layers are pooled, cosine similarity is computed between the query embedding and **all node embeddings**, and top nodes are selected until a token budget is reached. citeturn13view2  
- **Pruning / token control:** the collapsed-tree process is explicitly token-budgeted; in their experiments they report using a collapsed tree with a **2000-token maximum** (roughly top ~20 nodes) for main results on at least one dataset analysis. citeturn13view2turn9view0

Demonstrated strengths:
- RAPTOR reports improved QA performance vs “traditional retrieval-augmented LMs” across several tasks; the abstract highlights an **absolute +20% accuracy improvement on QuALITY** when coupled with GPT-4 compared to the best prior performance they cite. citeturn0search0turn0search4  
- Their ablations indicate non-leaf summary nodes materially contribute to retrieval: they report **18.5%–57%** of retrieved nodes coming from non-leaf layers in a layer-usage analysis. citeturn9view0

Measured / argued weaknesses:
- The querying strategy they prefer in analysis (“collapsed tree”) is **not hierarchical search**; it requires similarity comparisons over all nodes (though they note it can be accelerated using ANN libraries). This matters directly for any claim about logarithmic search complexity. citeturn13view2  
- The paper’s own related-work positioning acknowledges summarisation can be lossy, motivating retaining intermediate nodes and multiple abstraction levels. citeturn8view1turn13view3

### LATTICE: LLM-guided traversal of a semantic tree with calibration (preprint / under review)

**LLM-guided Hierarchical Retrieval** (arXiv 15 Oct 2025; submitted to ICLR 2026) introduces **LATTICE** by entity["people","Nilesh Gupta","ml researcher"], entity["people","Wei-Cheng Chang","ml researcher"], entity["people","Ngot Bui","ml researcher"], entity["people","Cho-Jui Hsieh","ml researcher"], and entity["people","Inderjit S. Dhillon","ml researcher"] (with affiliations spanning entity["organization","The University of Texas at Austin","austin, tx, us"], entity["organization","University of California, Los Angeles","los angeles, ca, us"], and entity["company","Google","technology company"] in the paper header). citeturn2search0turn14view1turn17view2

Mechanics (this is the closest published analogue to “retrieval by elimination” over a tree):
- **Tree construction (offline):** corpus is organised into a semantic hierarchy via either **bottom-up agglomerative** or **top-down divisive** strategies, using multi-level summaries for internal nodes. citeturn2search0turn8view2  
- **Query routing / scoring:** at query time, a “search LLM” performs listwise scoring of candidate nodes and conducts a **greedy best-first traversal** with a **beam** (parallel expansion of top candidates at each step). citeturn8view2turn9view1  
- **Pruning / elimination:** traversal prunes the tree implicitly by repeatedly expanding only the top nodes in the beam; the paper motivates this as logarithmic search complexity in the number of documents under the tree scaffold. citeturn2search0turn9view1turn17view2  
- **Cross-branch calibration:** the paper’s core technical claim is that raw LLM relevance judgments are noisy and not comparable across branches/levels; LATTICE estimates calibrated latent relevance scores from local comparisons and aggregates them into a **path relevance metric** to support global best-first decisions. citeturn2search0turn9view1turn8view2

Comparative evidence:
- The OpenReview/arXiv abstract reports **up to +9% Recall@100 and +5% nDCG@10** over the next best zero-shot baseline on BRIGHT, and claims comparability to a fine-tuned SOTA (DIVER-v2) on static-corpus subsets. citeturn2search0turn17view2turn4search21  
- LATTICE explicitly contrasts itself with RAPTOR: it argues RAPTOR builds a semantic hierarchy but still relies on “conventional embedding-based similarity search” to traverse it, whereas LATTICE uses an LLM as the active traversal agent online. citeturn9view1turn13view2

Key weaknesses / risk factors surfaced by the work itself:
- The paper frames a “central challenge” as **LLM scoring noise and context dependence**, requiring calibration to avoid cross-branch errors—this is a structural fragility unique to LLM-guided elimination search. citeturn9view1turn17view2  
- The need for multiple LLM calls during traversal introduces a latency/cost trade-off; the paper includes cost-performance analysis sections and traversal hyperparameters, indicating non-trivial operational complexity. citeturn9view1turn14view1

### TreeRAG: tree chunking plus bidirectional traversal (peer-reviewed)

**TreeRAG: Unleashing the Power of Hierarchical Storage for Enhanced Knowledge Retrieval in Long Documents** (Findings of ACL 2025) proposes (i) **Tree-Chunking** (tree-like chunking/embedding intended to preserve hierarchical structure among “knowledge points”) and (ii) **Bidirectional Traversal Retrieval** combining “root-to-leaves” and “leaf-to-root” strategies. citeturn4search20turn0search2

Mechanics (as reported):
- **Tree construction:** Tree-Chunking organises chunks into a hierarchy (the paper positions this as less destructive than naïve chunking for long-doc QFS-style tasks). citeturn0search2turn4search20  
- **Traversal strategy:** retrieval explicitly uses both directions along the hierarchy (downward for specificity; upward for context aggregation and connectivity restoration). citeturn4search20turn18view0

Measured performance:
- In an ablation table on the Dragonball dataset, TreeRAG improves retrieval quality over naïve baselines. For example, on Dragonball-Finance at Top-3 it reports **Recall 50.51% vs 30.49%** and **Precision 38.65% vs 23.11%** (TreeRAG vs Naive), and similarly large gains on Dragonball-Medical (Top-3 Recall **14.30% vs 1.56%**). citeturn18view0  
- In a broader comparative table, TreeRAG is reported alongside Late Chunking and RAPTOR-based baselines on Dragonball subsets, continuing to show higher recall and precision under several cut-offs (Top-3/Top-5/Top-10). citeturn18view1

Reported limitations:
- The authors state TreeRAG “does not have a particular advantage” for recalling chunks from **different documents** because each tree is built independently, implying difficulty with cross-document/cross-branch retrieval without an additional global structure. citeturn18view0

### HiREC: hierarchical retrieval as a two-stage elimination pipeline (peer-reviewed)

**Hierarchical Retrieval with Evidence Curation for Open-Domain Financial Question Answering on Standardized Documents** (arXiv 26 May 2025; Findings of ACL 2025) proposes **HiREC** and introduces **LOFin**, a large-scale benchmark built on SEC filings. citeturn3search0turn3search2turn8view3

Although HiREC is not a tree traversal system, it is directly relevant to “retrieval by elimination” because it operationalises hierarchical retrieval as a **document → passage/page** cascade designed to reduce confusion among near-duplicate content—a failure mode that also appears in hierarchical tree routing (wrong early branch choice). citeturn3search0turn8view3

Mechanics:
- **Hierarchical retrieval:** first retrieve related documents, then select the most relevant passages within them, explicitly aiming to reduce near-duplicate confusion in standardised documents (SEC filings). citeturn3search0turn8view3  
- **Evidence curation:** filters irrelevant passages; when needed generates complementary queries to fill missing evidence. citeturn3search0turn8view3  
- **Scale:** the corpus is reported as **145,897 SEC reports** and LOFin includes **1,595 QA pairs** (with LOFin-1.4k and expanded LOFin-1.6k variants described). citeturn8view3turn11view4

Measured performance (LOFin-1.4k main table):
- HiREC reports an **Average Page Recall 45.35** and **Average Answer Accuracy 42.36**, compared to a Dense baseline at **34.78 Page Recall** and **29.22 Answer Accuracy**, and it uses fewer passages on average (**k = 3.7** in the table, interpreted as average number of passages used during generation). citeturn18view2turn11view3

### HIRO: learned discrete hierarchies for retrieval-augmented generation (peer-reviewed, adjacent)

**Hierarchical Indexing for Retrieval-Augmented Opinion Summarization** (TACL 2024) proposes **HIRO** as a learned hierarchical index mapping sentences to paths through a discrete semantic hierarchy; retrieval then selects clusters of prevalent opinions which are passed to an LLM for generation. This is not a general RAG retriever, but it is strong precedent for **learned hierarchical routing** rather than purely clustering-based trees. The authors are entity["people","Tom Hosking","nlp researcher"], entity["people","Hao Tang","nlp researcher"], and entity["people","Mirella Lapata","nlp researcher"] at entity["organization","University of Edinburgh","edinburgh, uk"]. citeturn10view2turn18view4turn6search8

The key mechanical contribution relevant to HCR is the idea that “hierarchy” can be an **indexing function** (encoder → path in a hierarchy) that supports efficient grouping and retrieval, not only a dendrogram built by unsupervised clustering. citeturn10view2turn6search4

### Hierarchical retrieval for graph-structured corpora (peer-reviewed and preprint mix)

Several systems build hierarchies over graphs, then retrieve across levels. These are not tree-only, but they matter because graph community hierarchies often become tree-like and the retrieval becomes elimination-based over those levels.

**HiRAG: Retrieval-Augmented Generation with Hierarchical Knowledge** (Findings of EMNLP 2025; arXiv 13 Mar 2025) constructs a **hierarchical knowledge graph** with “summary entities” at higher layers and retrieves three layers (local, global, bridge). The author list is long; in the paper header it includes entity["company","KASMA.ai","ai company"] and entity["organization","The Chinese University of Hong Kong","hong kong, china"] as affiliations. citeturn10view3turn7search3turn8view4  
Measured performance (objective metrics appendix page shown in the EMNLP PDF): on 2WikiMultiHopQA it reports **EM 46.20 / F1 60.06**, compared to NaiveRAG **EM 15.60 / F1 25.64** and several graph baselines; on HotpotQA it reports **EM 37.00 / F1 52.29**. citeturn18view3turn12view4  
It also reports token/API/time cost comparisons across datasets, indicating that hierarchical indexing increases offline cost but can keep retrieval token costs low depending on method. citeturn12view2turn12view4

**ArchRAG: Attributed Community-based Hierarchical RAG** (arXiv preprint, Feb 2025) builds a hierarchy of “attributed communities” using an LLM-based iterative clustering framework, then builds a hierarchical index (**C-HNSW**, inspired by HNSW) and uses hierarchical search plus adaptive filtering to reduce online token cost. citeturn8view5turn9view3turn10view4  
It claims **up to 250× token savings** compared to GraphRAG. citeturn12view1turn9view4  
It reports strong performance improvements over RAG and GraphRAG-style baselines on multiple datasets; for instance, Table 3 in the arXiv HTML lists (among others) Multihop-RAG Accuracy **68.8** vs Vanilla RAG **58.6**, and HotpotQA Recall **69.2** vs Vanilla RAG **56.1**. citeturn14view0

**T-Retriever: Tree-based Hierarchical Retrieval Augmented Generation for Textual Graphs** (arXiv 8 Jan 2026) reformulates attributed-graph retrieval as **tree-based retrieval** using an “encoding tree”, introducing Adaptive Compression Encoding and a semantic-structural entropy objective for hierarchical partitions. citeturn17view1turn0search6  
The paper claims significant outperformance on “diverse graph reasoning benchmarks” but the abstract does not surface the specific numeric deltas; this should be treated as promising but not yet widely replicated evidence. citeturn17view1

## Production frameworks and implementations of hierarchical retrieval patterns

### LlamaIndex: explicit tree indices, coarse-to-fine hierarchies, and merging retrievers

entity["company","LlamaIndex","llm data framework"] includes multiple “structured retrieval” primitives that operationalise hierarchy in ways directly relevant to HCR, even when the backend is still a vector store. citeturn16view1turn16view4

Key mechanisms (documented):
- **Tree Index:** builds a hierarchical tree whose leaves are nodes; query-time retrieval traverses from root to leaf, selecting `child_branch_factor` children per level (default 1, configurable). This is literal top-down elimination search, though the scoring details are implementation-specific. citeturn16view1turn16view0  
- **HierarchicalNodeParser + AutoMergingRetriever:** constructs a chunk-size hierarchy (default levels reported as 2048 → 512 → 128 tokens) where leaf nodes are embedded and retrieved via similarity search, and parent nodes are stored in a docstore; the AutoMergingRetriever can recursively merge retrieved leaf nodes into parent contexts when enough children are retrieved. citeturn16view3turn3search1turn16view2  
- **Recursive retrieval over structured nodes:** their “RecursiveRetriever” concept explicitly supports nodes that **link to other query engines** (e.g., a node representing a table summary links to a Pandas/SQL engine), enabling leaves to resolve to external data sources rather than plain text chunks—mechanically close to “leaf nodes resolve to external systems”. citeturn3search13

Overall, this ecosystem constitutes credible production precedent that hierarchy is not only academic: it is being packaged as usable retrieval infrastructure, though often still tied to vector search for initial candidate selection. citeturn16view3turn16view4

### LangChain: parent-child retrieval as a pragmatic hierarchy

entity["organization","LangChain","llm application framework"] documents **ParentDocumentRetriever** (in its JavaScript docs) as a retriever that embeds small “child” chunks but returns the larger “parent” documents, explicitly to balance targeted retrieval vs context richness. citeturn15view0

This is a hierarchical pattern, but it addresses a different failure mode than HCR: it is primarily a **context reconstruction** technique after flat similarity retrieval, not a log-time elimination search over a tree. citeturn15view0

### GraphRAG: hierarchical community summaries as retrieval scaffolding

entity["organization","Microsoft Research","research lab | redmond, wa, us"]’s GraphRAG (as described in public docs and the arXiv paper) builds a knowledge graph from text, partitions it into a **hierarchy of communities**, generates community summaries, and uses local/global retrieval patterns at query time. citeturn19search31turn19search26turn19search0

Even though it is graph-based, GraphRAG’s community hierarchy is a major production-grade example of **hierarchical summarisation artefacts being queried for token-efficient context**—one of the core ideas also present in tree-based RAG systems. citeturn19search31turn19search26

### RAGFlow: “RAPTOR mode” as productised preprocessing

entity["organization","RAGFlow","open-source rag framework"] documents an “Enable RAPTOR” configuration, positioning RAPTOR as an available document preprocessing / indexing option in a broader RAG system. This is limited evidence that RAPTOR-style hierarchical summarisation trees are being operationalised beyond research code. citeturn0search21turn0search7

## Pre-LLM precedents that map cleanly to HCR-style retrieval by elimination

The core idea behind HCR—early elimination via a hierarchical index to achieve log-like search scaling—has strong precedent in classic IR and database indexing. The differences in the LLM era are: (i) the “keys” are semantic and fuzzy, (ii) internal nodes are often *generated summaries* rather than hand-designed categories, and (iii) query evaluation may involve LLM calls.

**B-trees (database indexing).** The canonical B-tree paper by entity["people","Rudolf Bayer","computer scientist"] and entity["people","Edward M. McCreight","computer scientist"] describes organising index pages in a branching tree such that retrieval/insertion/deletion costs scale with the logarithm of the index size (with base determined by page/branching factor). This is the archetype of “log complexity via hierarchical elimination”. citeturn5search11turn5search0

**k-d trees (space-partitioning search).** entity["people","Jon Louis Bentley","computer scientist"]’s k-d tree work (1975) is an early example of hierarchical space partitioning for associative searching, conceptually similar to routing queries through a decision structure that narrows the candidate region at each level. citeturn5search3

**HNSW (hierarchical approximate nearest neighbour search).** entity["people","Yury A. Malkov","computer scientist"] and entity["people","Dmitry A. Yashunin","computer scientist"] propose Hierarchical Navigable Small World graphs as a multi-layer structure for ANN search; their abstract explicitly describes a hierarchy of proximity graphs and notes that starting from upper layers enables favourable scaling (often described as logarithmic). Modern vector retrieval stacks frequently depend on this family of ideas even when the user perceives retrieval as “flat vector search”. citeturn5search2turn5search6

**Cluster-based browsing and hierarchical clustering for information access.** Scatter/Gather (SIGIR 1992) by entity["people","Douglas R. Cutting","computer scientist"], entity["people","Jan O. Pedersen","computer scientist"], entity["people","David R. Karger","computer scientist"], and entity["people","John W. Tukey","statistician"] treats clustering as a primitive information access method for navigating large document collections, providing older but directly relevant precedent for “semantic hierarchies” as a retrieval interface. citeturn5search1turn5search12

The direct mapping to HCR is: pre-LLM systems optimise *routing and pruning* in a well-defined metric/ordering space; LLM-era hierarchical retrieval tries to create an equivalent hierarchical scaffold for semantic relevance, often by clustering and summarisation. citeturn13view3turn2search0turn5search11

## Comparative evidence: what is actually supported (and what is not)

Across the strongest, most directly relevant works (RAPTOR, LATTICE, TreeRAG, HiREC, ArchRAG, HiRAG), the evidence supports a bounded set of claims.

Hierarchical structure tends to help when the task requires multi-hop reasoning, long-document coherence, or separating global from local evidence. RAPTOR reports significant improvements on multiple QA tasks when retrieval can pull from multi-level summaries rather than only leaf chunks. citeturn0search0turn9view0 TreeRAG reports large recall/precision improvements over Naive baselines on long-document retrieval settings (Dragonball subsets). citeturn18view0turn18view1 HiREC shows large gains in both retrieval (page recall) and downstream answer accuracy on a large-scale standardised-document corpus where flat retrieval is confounded by near-duplicates. citeturn18view2turn8view3 ArchRAG and HiRAG report improvements over graph-based and vanilla RAG baselines on multi-hop QA datasets, suggesting hierarchical organisation of intermediate representations can help beyond text-only chunk retrieval. citeturn14view0turn18view3

Token efficiency improvements are sometimes measured and can be substantial, but the measurement regimes vary. HiREC explicitly reports using fewer passages on average (k) while achieving better accuracy, which is a direct proxy for context budget efficiency. citeturn18view2 ArchRAG claims up to 250× token savings over GraphRAG, but that is within a graph-RAG operational definition of token usage and depends on that baseline’s token-heavy community traversal. citeturn12view1turn9view4 HiRAG reports token/API/time costs for indexing vs retrieval, illustrating a recurring pattern: hierarchical methods can shift cost into offline indexing while keeping online retrieval compact. citeturn12view2turn12view4

The literature does not show a stable consensus that “hierarchical always beats flat” in general RAG, because the comparisons are not normalised across (i) identical corpora, (ii) identical embedding models, (iii) identical generation models, and (iv) identical token budgets. Surveys of RAG and retrieval-augmented LLMs repeatedly foreground retrieval quality and computational efficiency as central limitations, but they do not establish a universal dominance result for any single retrieval structure. citeturn6search3turn20search0turn20search1

A critical point for HCR’s claimed “logarithmic search complexity” is that several influential “tree-based” systems do not operationalise log-time traversal at inference time. RAPTOR’s preferred collapsed-tree retrieval is explicitly an all-nodes similarity search (albeit over multi-level nodes), which is conceptually closer to flat retrieval over an expanded representation set. citeturn13view2turn9view0 In contrast, LATTICE is explicitly designed as log-complexity traversal (tree scaffold + best-first beam search), making it the most direct prior art analogue to “tree-based retrieval by elimination”. citeturn2search0turn9view1turn17view2

## Open problems and gaps that remain unsolved

**Robust hierarchy construction and maintenance under change.** Most systems rely on offline clustering and summarisation (RAPTOR, TreeRAG, LATTICE) or iterative LLM-based clustering (ArchRAG). These processes are expensive and can be brittle when the corpus updates frequently, because the hierarchy can become stale or inconsistent with new documents. The RAG surveys flag continual updating and retrieval robustness as ongoing challenges, even outside hierarchical methods. citeturn13view3turn4search20turn2search0turn20search0

**Early-branch errors and cross-branch queries.** Elimination-style traversal has a structural risk: if the system prunes a branch that contains needed evidence, the answer becomes unrecoverable unless the traversal maintains sufficient breadth. TreeRAG’s own limitation statement about weak advantage across different documents (independent trees) is one concrete manifestation of “cross-branch / cross-document” failure. citeturn18view0 LATTICE elevates this into a central technical problem: noisy, context-dependent LLM judgments make reliable cross-branch comparisons hard; their calibration machinery is an explicit attempt to prevent mistaken elimination. citeturn9view1turn17view2

**Scoring internal nodes reliably under tight context windows.** Hierarchies often depend on internal-node summaries. But summaries can discard “small” details that become decisive for certain queries. RAPTOR explicitly discusses using multiple abstraction levels and retrieving non-leaf nodes, but this does not remove the fundamental compression risk; it only offers more levels to choose from. citeturn9view0turn13view3 T-Retriever’s motivation similarly argues that rigid compression quotas can damage local structure, proposing globally optimised compression to preserve natural hierarchy—another view of the same compression trade-off. citeturn17view1

**Token-budgeted context assembly at very low budgets (your ~400-token target).** Published hierarchical systems frequently operate at much higher retrieval budgets (e.g., RAPTOR highlights a 2000-token retrieval cap in a main querying strategy discussion), and many evaluation protocols assume substantially larger contexts than 400 tokens. citeturn13view2 HiREC’s “k passages” framing and ArchRAG/HiRAG token-cost reporting are closer, but they still do not establish a standard methodology for optimising retrieval to a *fixed, very small* context window while maintaining recall for multi-hop questions. citeturn18view2turn12view1turn12view4

**Leaves that resolve to tools / external data sources, not only text snippets.** Most hierarchical retrieval papers treat leaves as textual chunks. The strongest mainstream precedent for “leaf nodes resolve to external systems” appears more in framework implementations than in academic benchmarking: LlamaIndex’s recursive retrieval explicitly retrieves a node, then queries a linked structured query engine (e.g., Pandas/SQL) behind that node. citeturn3search13 This is an important gap/opportunity area: there is limited peer-reviewed evidence on end-to-end hierarchical traversal where terminal nodes are heterogeneous connectors with distinct latency/cost models (APIs, databases, SaaS systems), which is central to HCR’s “leaf nodes resolve to external data sources” framing.

**Lack of standardised, apples-to-apples benchmarks for hierarchical vs flat retrieval.** The community has strong benchmarks for ranking (Recall@k, nDCG) and QA correctness, but hierarchical retrieval introduces extra degrees of freedom (tree construction strategy, traversal policy, summary fidelity, breadth vs depth budget, online LLM call budget). LATTICE and HiRAG include ablations and cost analyses, but broader cross-paper comparability remains weak—something the general RAG surveys also emphasise when discussing evaluation fragmentation. citeturn9view1turn12view2turn6search3turn20search0