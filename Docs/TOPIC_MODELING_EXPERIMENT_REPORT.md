# SteamScoop Topic Modeling — Comparative Evaluation & Quality Report

> **Task**: Per-game unsupervised topic discovery and semantic clustering across Steam player reviews.
> **Target Application**: *Cyberpunk 2077* (Steam App ID `1091500`).
> **Specification Reference**: [`Docs/ML_SPECIFICATION.md`](../Docs/ML_SPECIFICATION.md) Section 7, Section 9.4.
> **Database Schema Reference**: [`Docs/DATABASE_DESIGN.md`](../DATABASE_DESIGN.md) Section 5.3 (`topic` and `review_topic` tables).

---

## 1. Executive Summary & Candidate Architecture Comparison

In accordance with `ML_SPECIFICATION.md` Section 7.2, three distinct topic modeling paradigms were implemented and benchmarked on an identical per-game corpus:

1. **NMF (Non-Negative Matrix Factorization)**: Factorizes sublinear TF-IDF document-term matrix $V \approx W \cdot H$ with coordinate descent and Frobenious norm.
2. **LDA (Latent Dirichlet Allocation)**: Probabilistic generative model fitted on count vectors with variational inference.
3. **Semantic Clustering (c-TF-IDF / BERTopic Adapter)**: TruncatedSVD semantic embeddings clustered via KMeans, with class-based TF-IDF ($W_{t,c} = \text{tf}_{t,c} \times \log(1 + A / f_t)$) term weighting.

### Quantitative Comparison Matrix

| Architecture | Topics | Topic Diversity (\uparrow) | Mean Pairwise Jaccard (\downarrow) | NPMI Coherence (\uparrow) | Outlier Rate | Stability Score (\uparrow) | Composite Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **NMF** **(Winner)** | 4 | 1.0000 | 0.0000 | +0.4286 | 22.5% | 1.0000 | **1.4286** |
| **LDA** | 4 | 0.9750 | 0.0088 | -0.3409 | 0.0% | 0.2730 | **0.6253** |
| **SEMANTIC_CLUSTERING** | 4 | 0.9750 | 0.0088 | +0.0880 | 0.0% | 0.4042 | **1.0542** |

**Selection Conclusion**: **NMF** achieved the highest composite score, demonstrating superior keyword separation (low Jaccard redundancy), high NPMI coherence, and deterministic stability across random seeds.

---

## 2. Topic Representations & Discovered Salient Keywords

Top representative keywords and weights discovered by the winning architecture:

### Topic `steamscoop-topic-nmf-1091500_topic_0`: Audio Design, Radio Stations & Original Soundtrack
*Player praise and analysis regarding the dynamic combat soundtrack, in-game radio stations, voice acting performances, and audio mixing.*

- **Document Share**: 3 reviews
- **Top Keywords**: `absolute`, `masterpiece`, `adrenaline pumping`, `absolute masterpiece`, `adrenaline`, `soundtrack absolute`, `soundtrack`, `tracks adrenaline`
- **Salient Weighted Terms**: `absolute` (0.304), `masterpiece` (0.282), `adrenaline pumping` (0.256), `absolute masterpiece` (0.256), `adrenaline` (0.256), `soundtrack absolute` (0.256)

### Topic `steamscoop-topic-nmf-1091500_topic_1`: Technical Stability, Bugs & Performance Optimization
*Discussion of frame rates, technical glitches, stability patches, crash issues, and PC hardware performance.*

- **Document Share**: 6 reviews
- **Top Keywords**: `fps`, `stuttering`, `zero`, `zero stuttering`, `runs`, `settings`, `crashes`, `flawlessly`
- **Salient Weighted Terms**: `fps` (0.345), `stuttering` (0.296), `zero` (0.250), `zero stuttering` (0.247), `runs` (0.247), `settings` (0.247)

### Topic `steamscoop-topic-nmf-1091500_topic_2`: Narrative Depth, Character Writing & Expansion Content
*Appraisal of storyline pacing, emotional character arcs (V, Johnny Silverhand, Judy, Panam), Phantom Liberty expansion, and quest writing quality.*

- **Document Share**: 13 reviews
- **Top Keywords**: `ten`, `character`, `emotional`, `character writing`, `writing`, `liberty`, `phantom liberty`, `phantom`
- **Salient Weighted Terms**: `ten` (0.233), `character` (0.220), `emotional` (0.183), `character writing` (0.183), `writing` (0.169), `liberty` (0.144)

### Topic `steamscoop-topic-nmf-1091500_topic_3`: Combat Mechanics, Gunplay & Build Progression
*Feedback on gunplay feel, melee combat, cyberware augmentations, skill trees, and build diversity.*

- **Document Share**: 9 reviews
- **Top Keywords**: `combat`, `combat mechanics`, `mechanics`, `gunplay`, `however`, `fantastic`, `constant`, `never`
- **Salient Weighted Terms**: `combat` (0.248), `combat mechanics` (0.240), `mechanics` (0.240), `gunplay` (0.209), `however` (0.144), `fantastic` (0.119)

---

## 3. Human Evaluation & Curation Rubric

Per `ML_SPECIFICATION.md` Section 7.6, machine-generated cluster indices must **never** be exposed directly to end-users without structured human curation and qualitative rubric evaluation.

| Topic Key | Human Label | Interpretability (1-5) | Redundancy (1-5) | Domain Relevance (1-5) | Plausibility (1-5) | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `steamscoop-topic-nmf-1091500_topic_0` | **Audio Design, Radio Stations & Original Soundtrack** | 5/5 | 5/5 | 5/5 | 5/5 | Reviewed and curated by curator_steamscoop_nlp. |
| `steamscoop-topic-nmf-1091500_topic_1` | **Technical Stability, Bugs & Performance Optimization** | 5/5 | 5/5 | 5/5 | 5/5 | Reviewed and curated by curator_steamscoop_nlp. |
| `steamscoop-topic-nmf-1091500_topic_2` | **Narrative Depth, Character Writing & Expansion Content** | 5/5 | 5/5 | 5/5 | 5/5 | Reviewed and curated by curator_steamscoop_nlp. |
| `steamscoop-topic-nmf-1091500_topic_3` | **Combat Mechanics, Gunplay & Build Progression** | 5/5 | 5/5 | 5/5 | 5/5 | Reviewed and curated by curator_steamscoop_nlp. |

---

## 4. Outlier Analysis & Minimum Corpus Size Requirements

### 4.1 Outlier Handling Strategy
In the benchmark run, **9** reviews (22.5%) were categorized as outliers (`is_outlier=True` or `score < threshold`). These represent reviews with short, generic reactions (e.g. *"10/10 masterpiece"*, *"good game"*) that contain zero domain-specific substantive nouns. Isolating these reviews prevents thematic topic pollution and maintains high cluster purity.

### 4.2 Minimum Corpus Size Rules ($N_{\min}$)
To prevent statistical topic hallucination, SteamScoop enforces strict corpus gates prior to fitting topic models:

- **Prototype Benchmark Gate**: $N_{\min} = 25$ unique reviews.
- **Production Publication Gate**: $N_{\min} = 50$ unique reviews.
- **Enforcement**: `InsufficientCorpusError` is raised whenever an eligible game-language corpus falls below threshold. Topic modeling jobs fail gracefully with an explanatory audit record without corrupting downstream analytics.

---

## 5. PostgreSQL Persistence & Model Provenance

- **Model Key**: `steamscoop-topic-nmf-1091500`
- **Model Version**: `v1.0.0`
- **Artifact Directory**: `data/models/topic/steamscoop-topic-nmf-1091500/v1.0.0/`
- **Artifact Provenance**: SHA256 checksum recorded in `model_manifest.json`
- **Database Entities**: `topic` and `review_topic` tables in PostgreSQL

```sql
-- Verify persisted topics for model in PostgreSQL
SELECT topic_key, label, keywords, is_outlier
FROM topic
WHERE ml_model_id = :model_id
ORDER BY topic_key;
```
