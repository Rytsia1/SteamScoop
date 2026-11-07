# SteamScoop
## Product Requirements Document (PRD)

**Document Version:** 1.0  
**Date:** November 8, 2026  
**Product Name:** SteamScoop  
**Product Category:** Public Game Intelligence & Research Platform  
**Platform:** Web Application  
**Tagline:** Understand Games Through Data.

---

# 1. Executive Summary

## 1.1 Product Overview

SteamScoop is a public Game Intelligence and Research Platform that transforms Steam user reviews into structured, interpretable, and actionable insights through Natural Language Processing (NLP), sentiment analysis, Aspect-Based Sentiment Analysis (ABSA), topic modeling, and statistical analytics.

The platform enables users to explore player feedback, understand community sentiment, identify recurring game-related issues, analyze player opinions over time, and compare multiple games through data-driven visualizations.

SteamScoop is designed to serve multiple audiences, including:

- Game development students.
- Independent game developers and development teams.
- Academic researchers and lecturers.
- Gaming communities.
- Game industry analysts.
- General users interested in game analytics.

Unlike conventional review aggregation platforms, SteamScoop focuses on extracting meaningful information from the textual content of player reviews rather than relying exclusively on recommendation percentages or aggregate ratings.

The platform combines two major product pillars:

1. **Game Intelligence:** Turning player feedback into insights about games, gameplay, performance, content, and community sentiment.
2. **Game Research:** Providing structured datasets, analytical tools, methodological transparency, and reproducible research workflows.

## 1.2 Product Vision

To make game-related community feedback more accessible, understandable, and useful through data-driven intelligence and research.

## 1.3 Product Mission

- Transform unstructured player reviews into structured analytical information.
- Help developers understand player experiences and potential areas for improvement.
- Support academic research in game development, player behavior, and game communities.
- Provide accessible game intelligence tools without requiring mandatory user registration.
- Promote transparent and reproducible analysis of player-generated data.

## 1.4 Product Positioning

SteamScoop is positioned as a public analytical platform that sits between conventional game review platforms and academic data analysis tools.

It does not aim to replace Steam reviews, professional game reviews, or existing game analytics services.

Instead, it provides an additional analytical layer that helps users understand what players discuss, how they feel about particular aspects of a game, and how those opinions change over time.

---

# 2. Problem Statement

## 2.1 Background

Steam provides a large collection of user-generated reviews containing information about player experiences, preferences, complaints, recommendations, and opinions.

However, conventional review interfaces primarily present individual reviews and aggregate recommendation statistics.

For users who need deeper insights, manually analyzing hundreds or thousands of reviews is time-consuming and difficult to reproduce.

Examples of questions that are difficult to answer through manual review browsing include:

- What are the most frequently discussed aspects of a particular game?
- Are players generally satisfied with its gameplay but dissatisfied with its performance?
- What are the most common complaints after a major update?
- How has player sentiment changed over time?
- What differentiates two competing games in terms of player perception?
- Which issues are frequently mentioned by negative reviewers?
- Are complaints about pricing, performance, or game mechanics increasing?

SteamScoop addresses these challenges by applying NLP and analytical methods to publicly accessible review data.

## 2.2 Core Problems

| Problem | Impact |
|---|---|
| Large volumes of unstructured reviews | Difficult to analyze manually |
| Aggregate recommendation metrics | Do not fully represent textual opinions |
| Limited aspect-level insights | Difficult to identify specific strengths and weaknesses |
| Lack of temporal analysis | Changes in community perception are difficult to track |
| Manual game comparison | Time-consuming and inconsistent |
| Limited research reproducibility | Results can be difficult to reproduce |
| Different languages | Multilingual reviews introduce analytical challenges |

## 2.3 Product Opportunity

SteamScoop can provide a centralized platform where users can explore player feedback through sentiment, aspects, topics, temporal trends, and comparative analytics.

The platform can also become a practical learning and research resource for the game development academic community.

---

# 3. Product Goals and Objectives

## 3.1 Primary Goals

**G1 — Game Intelligence**

Provide meaningful insights into player sentiment and game-related discussions.

**G2 — Academic Research Support**

Enable users to explore review datasets, perform structured analysis, and export analytical results.

**G3 — Accessibility**

Provide public access to core analytics without mandatory registration.

**G4 — Analytical Transparency**

Make data collection methods, model versions, limitations, and evaluation results accessible to users.

**G5 — Multi-Game Intelligence**

Support analysis and comparison across multiple Steam games.

## 3.2 Success Metrics

The following are proposed targets for the initial product releases, not existing achievements.

| Metric | Initial target |
|---|---:|
| Indexed games | 100 |
| Processed reviews | 100,000 |
| Initial review sample | Up to 5,000/game |
| English sentiment macro-F1 | ≥ 0.85 |
| Secondary-language macro-F1 | ≥ 0.75 |
| Core analytics availability | ≥ 99% |
| Common cached API response | Target < 500 ms |
| Successful ingestion jobs | ≥ 95% |
| Completed game comparisons | Track monthly |
| Returning users | Track monthly |

Model targets must be evaluated against independently annotated test datasets. Performance targets must not be achieved by manipulating test data or evaluation procedures.

---

# 4. Target Users and Personas

## 4.1 Game Development Students

**Needs:**
- Understand player feedback.
- Identify common gameplay issues.
- Compare games within the same genre.
- Obtain supporting data for academic assignments.
- Explore practical applications of NLP in game development.

**Example use case:**

A game development student wants to analyze how players perceive the difficulty and combat mechanics of several action RPGs.

## 4.2 Game Developers

**Needs:**
- Understand recurring player complaints.
- Identify strengths and weaknesses.
- Monitor feedback after game updates.
- Compare their games against competitors.
- Identify potential improvement opportunities.

**Example use case:**

An indie development team wants to understand whether negative feedback is primarily related to performance, game balance, or content limitations.

## 4.3 Lecturers and Academic Researchers

**Needs:**
- Explore review datasets.
- Examine sentiment distributions.
- Study player behavior and opinions.
- Understand model methodology.
- Export data for academic analysis.
- Reproduce analytical configurations.

**Example use case:**

A researcher wants to examine the relationship between game updates and changes in player sentiment.

## 4.4 Gaming Community

**Needs:**
- Explore games.
- Understand community opinions.
- Discover common topics.
- Compare games before purchasing or playing.
- Understand community trends.

**Example use case:**

A player wants to compare two games to understand differences in community sentiment about gameplay and technical performance.

---

# 5. Product Scope

## 5.1 In Scope

SteamScoop v1 includes:

- Public game discovery and search.
- Steam game metadata retrieval.
- Steam review collection.
- Historical review sampling.
- Incremental review collection.
- Sentiment analysis.
- Aspect-based sentiment analysis.
- Topic modeling.
- Temporal sentiment analysis.
- Review exploration and filtering.
- Multi-game comparison.
- Analytical dashboards.
- Model and methodology transparency.
- Dataset metadata and provenance.
- Optional user accounts.
- Research workspaces.
- Data export.

## 5.2 Out of Scope for Initial Releases

- Replacing Steam's review system.
- Publishing user-generated Steam reviews.
- Direct game purchasing.
- Steam account authentication.
- Accessing private Steam user information.
- Real-time monitoring of every Steam review.
- Automated game quality scoring.
- Automated developer recommendations.
- Generative AI chatbot functionality.
- Direct integration with game development engines.
- Full commercial market intelligence services.

These capabilities may be reconsidered in future releases.

---

# 6. Product Architecture and Modules

SteamScoop consists of seven primary product modules.

## 6.1 Global Game Intelligence Dashboard

**Purpose:** Provide an overview of the games and review data indexed by SteamScoop.

Key features:

- Total indexed games.
- Total processed reviews.
- Global sentiment distribution.
- Most discussed games.
- Trending topics.
- Recently updated datasets.
- Collection and processing status.
- Popular game categories where metadata permits.

The dashboard must clearly distinguish between platform-wide statistics and statistics for individual games.

## 6.2 Game Explorer

**Purpose:** Enable users to discover and explore indexed Steam games.

Key features:

- Search by game title.
- Search by Steam App ID.
- Game metadata.
- Developer and publisher information.
- Release date.
- Review statistics.
- Sentiment distribution.
- Dataset freshness.
- Link to original Steam store page.

Each indexed game must have a dedicated analytical page.

## 6.3 Review Intelligence and Explorer

**Purpose:** Enable detailed exploration of individual player reviews.

Key features:

- Review text.
- Recommendation status.
- Review language.
- Creation and update dates.
- Playtime information where available.
- Helpful votes.
- Sentiment prediction.
- Aspect predictions.
- Topic assignments.
- Filtering and sorting.

Supported filters:

- Positive, negative, and neutral sentiment.
- Language.
- Date range.
- Recommendation status.
- Aspect.
- Topic.
- Playtime range.
- Helpful vote range.

The platform must preserve the distinction between Steam's recommendation status (`voted_up`) and SteamScoop's NLP sentiment prediction.

## 6.4 Aspect and Topic Intelligence

**Purpose:** Identify what players discuss and how they feel about specific game aspects.

Initial aspect taxonomy:

| Aspect | Description |
|---|---|
| Gameplay | Overall player experience |
| Game Mechanics | Rules and interactive systems |
| Difficulty | Challenge and balancing |
| Graphics | Visual quality and presentation |
| Story | Narrative and characters |
| Performance | Optimization and technical stability |
| Multiplayer | Online and cooperative experience |
| Content | Game content and progression |
| Pricing | Value and monetization |
| Audio | Music and sound design |
| Community | Multiplayer community and social experience |
| Updates | Patches and developer updates |

Key features:

- Aspect frequency.
- Aspect sentiment distribution.
- Representative reviews.
- Topic frequency.
- Topic descriptions.
- Topic trends.
- Aspect comparison.

Aspect taxonomy must be versioned and extensible.

Topic labels generated by topic modeling should be treated as analytical interpretations, not objectively verified categories.

## 6.5 Game Comparison Lab

**Purpose:** Enable users to compare multiple Steam games.

Key features:

- Compare at least two games.
- Sentiment distribution comparison.
- Aspect sentiment comparison.
- Topic distribution comparison.
- Review volume comparison.
- Temporal sentiment comparison.
- Language distribution comparison.
- Export comparison results.

Comparison results must disclose differences in dataset size, collection periods, and language coverage.

## 6.6 Research Workspace

**Purpose:** Allow registered users to save and organize analytical work.

Key features:

- Create research projects.
- Add multiple games.
- Save analysis configurations.
- Save filters.
- Store analytical snapshots.
- Organize research notes.
- Share read-only analysis links.
- Invite project collaborators.
- Track export history.

Workspace functionality requires authentication.

## 6.7 Dataset and Methodology Center

**Purpose:** Improve research transparency and data usability.

Key features:

- Dataset descriptions.
- Collection timestamps.
- Collection methodology.
- Sampling methodology.
- Data coverage.
- Supported languages.
- Model versions.
- Model evaluation metrics.
- Known limitations.
- CSV and JSON export.
- Source attribution.

---

# 7. User Roles and Access Control

SteamScoop follows a public-first access model.

| Role | Access |
|---|---|
| Guest | Public dashboards, search, review exploration, comparison |
| Member | Guest functionality + personal workspaces |
| Researcher | Member functionality + advanced research projects and export privileges |
| Moderator | Content moderation, if applicable |
| Admin | Platform administration, ingestion, models, users, and system configuration |

Lecturers are not automatically administrators. Roles must reflect actual responsibilities.

## 7.1 Access Principles

- Public analytics do not require login.
- Registration is optional.
- Workspace creation requires an account.
- Research project collaboration requires authentication.
- Administrative functions require explicit authorization.
- Backend authorization must be enforced independently of frontend visibility.
- Export limits must be configurable.

Institutional email verification is optional and must not be mandatory for general platform access.

---

# 8. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Public access to core analytics | P0 |
| FR-02 | Search games by title or App ID | P0 |
| FR-03 | Retrieve and store Steam game metadata | P0 |
| FR-04 | Collect Steam reviews through the current API | P0 |
| FR-05 | Historical review sampling | P0 |
| FR-06 | Incremental weekly collection | P0 |
| FR-07 | Sentiment classification | P0 |
| FR-08 | Review exploration and filtering | P0 |
| FR-09 | Basic aspect analysis | P1 |
| FR-10 | Topic modeling | P1 |
| FR-11 | Temporal analytics | P1 |
| FR-12 | Multi-game comparison | P1 |
| FR-13 | Display model and methodology information | P0 |
| FR-14 | Dataset provenance and freshness | P0 |
| FR-15 | User registration and authentication | P1 |
| FR-16 | Save research workspaces | P1 |
| FR-17 | Export datasets and analytical results | P1 |
| FR-18 | Share research analysis | P2 |
| FR-19 | Collaborative research projects | P2 |
| FR-20 | Multilingual analytics | P2 |

Priority definitions:

- P0: Required for initial public MVP.
- P1: Important for the research-oriented release.
- P2: Future enhancement.

---

# 9. Non-Functional Requirements

## 9.1 Performance

- Common cached analytics API requests should target responses below 500 ms.
- Review exploration must support pagination.
- Large exports must run asynchronously.
- Expensive NLP inference must not block public API requests.
- Dashboard analytics should use precomputed aggregates when practical.

## 9.2 Reliability

- Background ingestion must support retry and recovery.
- Data persistence must be transactional.
- Collection jobs must be idempotent.
- Failed jobs must retain diagnostic information.
- Public analytics must remain accessible independently of ingestion execution.

## 9.3 Scalability

- Use a modular monolith architecture initially.
- Support multiple background workers.
- Separate read operations from heavy ingestion and processing workloads.
- Introduce additional infrastructure only when justified by measured bottlenecks.

## 9.4 Security

- Use secure password hashing such as Argon2id.
- Enforce server-side authorization.
- Protect authentication sessions or tokens.
- Apply API rate limiting.
- Validate user input.
- Restrict export privileges and quotas.
- Maintain administrative audit logs.
- Avoid unnecessary collection of personal data.

## 9.5 Accessibility and Usability

- Responsive web interface.
- Clear information hierarchy.
- Accessible charts and labels.
- Consistent navigation.
- Understandable analytical terminology.
- Explicit empty, loading, and error states.

## 9.6 Data Integrity

- Unique Steam review identifiers within each game.
- Idempotent upsert operations.
- Versioned model predictions.
- Collection timestamps.
- Dataset provenance.
- Consistent analytical aggregation.

---

# 10. Steam Data Ingestion Requirements

## 10.1 Data Source

Primary source:

Steam User Reviews API:

`https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`

The current endpoint must be used rather than the deprecated legacy `/appreviews` endpoint.

Steam review API documentation: https://partner.steamgames.com/doc/webapi/IUserReviewsService

## 10.2 Collection Strategy

SteamScoop uses a hybrid strategy consisting of:

1. Initial historical sampling.
2. Weekly incremental collection.
3. Reconciliation and recovery.

## 10.3 Initial Historical Collection

Baseline configuration:

| Parameter | Value |
|---|---|
| Maximum initial sample | 5,000 reviews/game |
| Sampling strategy | Temporal quota sampling |
| Time buckets | 10 |
| Initial quota | Up to 500 reviews/bucket |
| Page size | 100 |
| Language | All available |
| Review type | All |
| Purchase type | All |
| Pagination | Cursor-based |

The 5,000-review target is an initial sampling target, not a permanent storage cap.

Sampling methodology must be documented. Temporal quota sampling is not equivalent to random sampling.

## 10.4 Incremental Collection

- Refresh indexed games weekly.
- Use the Updated review filter.
- Maintain a collection watermark.
- Use a configurable 14-day overlap window.
- Upsert new and modified reviews.
- Reprocess NLP predictions when relevant review content changes.

## 10.5 Checkpointing

Collection must support interruption and recovery.

Required checkpoint information:

- Job ID.
- Game ID.
- Collection type.
- Date window.
- Cursor.
- Last observed review timestamps.
- Completed pages.
- Number of collected reviews.
- Completion status.
- Last update timestamp.

Review batches and corresponding cursor checkpoints must be committed transactionally.

## 10.6 Background Processing

Use Celery and Redis for asynchronous tasks.

Core jobs:

- Historical collection.
- Incremental collection.
- Review processing.
- Analytics aggregation.
- Failed job recovery.
- Reconciliation.

Steam API failures must not block public dashboard access.

## 10.7 Data Collection Governance

- Review Steam's applicable terms and policies before public deployment.
- Publicly accessible data must not automatically be assumed unrestricted for redistribution.
- Retain only necessary review and analytical fields.
- Avoid storing SteamID.
- Avoid unnecessary hardware and author metadata.
- Provide source attribution and original review links where available.
- Record collection timestamps and methodology.
- Document limitations and coverage gaps.
- Provide a contact process for data correction or takedown requests.

---

# 11. Machine Learning and NLP Requirements

## 11.1 Sentiment Analysis

Objective:

Classify review text into sentiment categories.

Initial classes:

- Positive.
- Negative.
- Neutral.

Candidate models:

- TF-IDF + Logistic Regression.
- TF-IDF + Linear SVM.
- DistilBERT.
- RoBERTa.
- XLM-RoBERTa for multilingual expansion.

Traditional ML models must be evaluated as baselines before selecting more complex Transformer models.

## 11.2 Aspect-Based Sentiment Analysis

Objective:

Identify game-related aspects discussed in reviews and classify sentiment associated with those aspects.

The initial implementation may use a two-stage architecture:

1. Aspect extraction or classification.
2. Aspect-level sentiment classification.

Each prediction must include model version, confidence where applicable, and relevant evidence text.

## 11.3 Topic Modeling

Candidate architecture:

- Sentence Transformers.
- UMAP.
- HDBSCAN.
- BERTopic.

Topic modeling must support:

- Topic extraction.
- Topic frequency.
- Topic descriptions.
- Representative reviews.
- Topic distribution.
- Topic trends.

Generated topic labels may require manual review.

## 11.4 Language Detection

Use language detection before model inference.

Candidate:

- fastText language identification.
- Multilingual embedding models.

English is the initial primary language, with multilingual expansion planned.

Unsupported languages must not receive unreliable predictions simply to increase coverage.

## 11.5 Model Evaluation

Required metrics:

**Sentiment:**
- Accuracy.
- Precision.
- Recall.
- Macro F1.
- Weighted F1.
- Confusion matrix.

**Aspect Analysis:**
- Aspect extraction precision, recall, and F1.
- Aspect sentiment F1.

**Topic Modeling:**
- Topic coherence.
- Topic diversity.
- Human interpretability.

Evaluation must use independent annotated datasets and appropriate train-validation-test separation.

Model predictions must be stored by model version so new models can be evaluated without recollecting Steam reviews.

---

# 12. Data Model Requirements

Primary entities:

| Entity | Responsibility |
|---|---|
| games | Steam game metadata |
| reviews | Collected review records |
| ml_models | Model registry |
| sentiment_predictions | Sentiment results |
| aspects | Aspect taxonomy |
| aspect_predictions | Aspect-level results |
| topics | Topic definitions |
| review_topics | Review-topic assignments |
| game_analytics | Aggregated game statistics |
| users | User accounts |
| roles | User role definitions |
| research_projects | Research workspaces |
| project_members | Project collaboration |
| saved_analyses | Saved analysis configurations |
| analysis_snapshots | Historical analysis snapshots |
| ingestion_jobs | Collection job lifecycle |
| collection_checkpoints | Pagination recovery |
| ingestion_batches | Batch-level collection logs |
| pipeline_runs | NLP pipeline execution history |
| model_evaluations | Model evaluation results |
| export_jobs | Dataset export tracking |
| audit_logs | Administrative activity |

PostgreSQL is the primary database.

JSONB may be used for flexible analytical filter configurations and selected metadata, but important relational entities must remain normalized.

---

# 13. Technology Stack

## 13.1 Frontend

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- TanStack Query.
- Apache ECharts.

## 13.2 Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.
- HTTPX.

## 13.3 Database and Background Processing

- PostgreSQL.
- Redis.
- Celery.
- Celery Beat.

## 13.4 Machine Learning

- Pandas.
- NumPy.
- scikit-learn.
- PyTorch.
- Hugging Face Transformers.
- Sentence Transformers.
- BERTopic.
- UMAP.
- HDBSCAN.
- fastText.
- MLflow.

## 13.5 Infrastructure and Testing

- Docker.
- Docker Compose.
- Git and GitHub.
- GitHub Actions.
- pytest.
- Playwright.

The initial architecture should remain a modular monolith with independent background workers rather than a microservices architecture.

---

# 14. API Requirements

API prefix:

`/api/v1`

## 14.1 Public API

| Endpoint | Purpose |
|---|---|
| GET /games/search | Search games |
| GET /games/{app_id} | Game details |
| GET /games/{app_id}/reviews | Review exploration |
| GET /games/{app_id}/analytics | Game analytics |
| GET /games/{app_id}/sentiment | Sentiment distribution |
| GET /games/{app_id}/aspects | Aspect analysis |
| GET /games/{app_id}/topics | Topic analysis |
| GET /games/{app_id}/trends | Temporal trends |
| POST /games/compare | Compare multiple games |
| GET /models | Model information |
| GET /methodology | Methodology documentation |

## 14.2 Authentication API

- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh
- GET /auth/me

## 14.3 Research API

- POST /research/projects
- GET /research/projects
- GET /research/projects/{id}
- PATCH /research/projects/{id}
- POST /research/projects/{id}/games
- POST /research/projects/{id}/analyses
- GET /research/projects/{id}/analyses
- POST /research/projects/{id}/exports

## 14.4 Administrative API

- POST /admin/ingestion/jobs
- GET /admin/ingestion/jobs
- GET /admin/ingestion/jobs/{id}
- POST /admin/ingestion/jobs/{id}/retry
- GET /admin/pipeline-runs
- GET /admin/models
- GET /admin/users

Administrative endpoints require appropriate authorization.

---

# 15. User Experience Requirements

## 15.1 Main Navigation

Proposed navigation:

- Home.
- Explore Games.
- Compare Games.
- Research.
- Methodology.
- About.

Authenticated users additionally receive:

- My Workspace.
- Saved Analyses.
- Account Settings.

Administrative navigation must be separated from public navigation.

## 15.2 Game Detail Page

Each game page should contain:

1. Game overview.
2. Review statistics.
3. Sentiment overview.
4. Aspect sentiment.
5. Topic analysis.
6. Temporal trends.
7. Review explorer.
8. Dataset information.
9. Methodology and model information.

## 15.3 Dashboard Principles

- Prioritize understandable analytical insights.
- Avoid excessive visualization.
- Show sample sizes alongside percentages.
- Clearly distinguish raw Steam statistics from NLP predictions.
- Provide tooltips and explanations.
- Display collection dates and dataset limitations.

---

# 16. Product Releases and Roadmap

## Release 1 — Core Intelligence MVP

**Objective:** Establish a functional public game analytics platform.

Features:

- Public landing page.
- Game search.
- Game metadata.
- Steam review ingestion.
- Historical sampling.
- Weekly incremental collection.
- Sentiment analysis.
- Game analytics dashboard.
- Review explorer.
- Basic aspect analysis.
- Methodology documentation.

## Release 2 — Advanced Analytics

**Objective:** Expand analytical capabilities.

Features:

- Advanced ABSA.
- Topic modeling.
- Temporal analytics.
- Multi-game comparison.
- Improved language detection.
- Multilingual sentiment analysis.
- Model evaluation dashboard.

## Release 3 — Research Platform

**Objective:** Support structured academic workflows.

Features:

- User authentication.
- Research workspaces.
- Saved analyses.
- Dataset exports.
- Analytical snapshots.
- Shareable research links.
- Research collaboration.

## Release 4 — Community Expansion

**Objective:** Increase platform utility for the broader gaming community.

Potential features:

- Public research projects.
- Community-generated analysis.
- Advanced game discovery.
- Additional data sources.
- Expanded research capabilities.
- Advanced developer insights.

---

# 17. Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Steam API rate limits | Collection delays | Global rate limiter, backoff, checkpoints |
| API changes | Integration failure | Isolated Steam adapter and API monitoring |
| Review sampling bias | Research validity | Document sampling methodology |
| Multilingual model quality | Incorrect predictions | Per-language evaluation |
| NLP inference cost | Increased operating costs | Batch processing and caching |
| Dataset growth | Storage pressure | Storage monitoring and retention policy |
| Review content restrictions | Legal and operational risk | Terms review, attribution, retention controls |
| Duplicate collection | Data inconsistency | Unique constraints and idempotent upserts |
| Model drift | Declining accuracy | Periodic evaluation |
| Incorrect interpretation | Misleading insights | Confidence indicators and methodological disclaimers |

---

# 18. Ethical and Analytical Considerations

SteamScoop must communicate that:

1. Steam reviews do not represent every player.
2. Review sentiment is not equivalent to objective game quality.
3. Steam's recommendation status is different from NLP sentiment.
4. Review samples may contain temporal and selection biases.
5. Topic modeling produces interpretations of recurring text patterns.
6. Model predictions may contain errors.
7. Multilingual model performance may vary by language.
8. Review counts and dataset coverage must be disclosed.
9. Analytics should not be presented as definitive evidence of player behavior without appropriate research methodology.

The platform must encourage responsible interpretation rather than treating automated predictions as unquestionable facts.

---

# 19. Deployment and Operational Requirements

Initial deployment should support:

- Frontend hosting.
- FastAPI backend hosting.
- PostgreSQL managed database.
- Redis service.
- Celery worker processes.
- Celery Beat scheduler.
- Model artifact storage.
- Automated database migrations.
- Automated testing and deployment pipelines.

Public analytics must be served from stored and precomputed data wherever possible.

Public user searches must not trigger unrestricted Steam API collection.

New game indexing should follow controlled ingestion policies, with job limits and administrative oversight.

---

# 20. Acceptance Criteria for MVP

SteamScoop MVP is considered ready when:

### Public Platform
- Users can access the platform without registration.
- Users can search indexed Steam games.
- Users can open individual game analytics pages.
- Users can explore reviews through filters and pagination.
- Users can understand the displayed analytical metrics.

### Data Collection
- The current Steam Reviews API is integrated.
- Initial historical sampling works.
- Weekly incremental collection works.
- Checkpoints support recovery.
- Duplicate reviews are prevented.
- Collection jobs expose status and logs.

### Machine Learning
- Sentiment classification is operational.
- Predictions are associated with model versions.
- Model evaluation results are documented.
- Unsupported language predictions are handled appropriately.
- Basic aspect analysis is available or explicitly scheduled for the next release.

### Transparency
- Data collection methodology is published.
- Model methodology is documented.
- Dataset timestamps are displayed.
- Analytical limitations are disclosed.
- Steam attribution is provided.

### Reliability and Security
- Background processing does not block public API requests.
- Failed jobs can be recovered.
- API access is rate-limited.
- Administrative endpoints are protected.
- Database constraints preserve data integrity.

---

# 21. Future Product Opportunities

Potential future directions include:

- Cross-platform game review intelligence.
- Game genre benchmarking.
- Player feedback analysis after major patches.
- Developer-oriented issue discovery.
- Game economy and monetization perception analysis.
- Player community behavior research.
- Research dataset versioning.
- Advanced multilingual semantic search.
- Community research collaboration.
- Public game intelligence reports.

These opportunities should be considered only after the core product demonstrates reliable data collection, analytical quality, and actual user demand.

---

# 22. Final Product Definition

SteamScoop is a public Game Intelligence and Research Platform that transforms Steam user reviews into structured analytical insights.

Its primary value is not merely showing whether players like or dislike a game.

Its value is helping users understand:

- What players are discussing.
- Which aspects of a game receive positive or negative feedback.
- Why players express certain opinions.
- How community sentiment changes over time.
- How different games compare.
- How review data can support game development and academic research.

**Product Vision:** Make game-related community feedback more understandable, accessible, and useful through data-driven intelligence.

**Product Mission:** Bridge the gap between unstructured player feedback and actionable game intelligence.

**Tagline:** Understand Games Through Data.