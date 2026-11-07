# SteamScoop

# System Design Document (SDD)

**Document ID:** SS-SDD-001\
**Version:** 1.0\
**Status:** Architecture Baseline\
**Date:** 8 November 2026\
**Product:** SteamScoop\
**Tagline:** Understand Games Through Data.

------------------------------------------------------------------------

## Document Control

  -----------------------------------------------------------------------
  Field                               Value
  ----------------------------------- -----------------------------------
  Document title                      SteamScoop System Design Document

  Version                             1.0

  Source documents                    SteamScoop PRD v1.0; SteamScoop SRS
                                      v1.0

  Intended audience                   Software engineers, ML engineers,
                                      DevOps engineers, QA engineers,
                                      maintainers

  Architecture style                  Modular monolith with asynchronous
                                      workers

  Primary database                    PostgreSQL

  Task broker                         Redis

  Backend                             Python / FastAPI

  Frontend                            React / TypeScript
  -----------------------------------------------------------------------

### Revision History

  Version   Date         Description
  --------- ------------ --------------------------------
  1.0       2026-11-08   Initial system design baseline

------------------------------------------------------------------------

# 1. Introduction

## 1.1 Purpose

This System Design Document (SDD) describes how SteamScoop will be
implemented to satisfy the product and software requirements defined in
its PRD and SRS.

It specifies:

-   System architecture and deployment boundaries.
-   Component responsibilities and interactions.
-   Database architecture and core entities.
-   Data flows from Steam collection to public analytics.
-   Background worker and task orchestration design.
-   Technology choices and their rationale.
-   Security, reliability, observability, and deployment considerations.

This document is an engineering design baseline. It does not replace the
SRS: the SRS defines required behavior, while this document describes
the proposed technical realization.

## 1.2 Scope

SteamScoop is a public Game Intelligence & Research Platform that
collects Steam game reviews, processes them using NLP, and provides
game-level analytics and research capabilities.

The initial system uses a modular monolith for the application backend,
PostgreSQL for durable data, Redis and Celery for background processing,
and a React-based frontend.

## 1.3 Design Principles

1.  **Public-first reads:** public analytics should be served from
    stored and precomputed data.
2.  **Asynchronous heavy work:** ingestion, NLP inference, aggregation,
    and exports must not block ordinary API requests.
3.  **Modular monolith first:** maintain clear domain boundaries without
    premature microservices.
4.  **Idempotent processing:** duplicate task delivery or repeated API
    pages must not create duplicate review records.
5.  **Recoverable ingestion:** every collection batch must be
    checkpointed transactionally.
6.  **Versioned intelligence:** predictions and topic assignments must
    retain model and taxonomy versions.
7.  **Data minimization:** store only Steam review fields needed for
    product and research use.
8.  **Methodological transparency:** expose collection periods, sampling
    method, model versions, and limitations.
9.  **Replaceable integrations:** isolate Steam API details behind
    adapters.
10. **Measured scaling:** add infrastructure only when profiling
    demonstrates a need.

## 1.4 Related Documents

-   `PRD.md` --- product goals, scope, user groups, and release
    strategy.
-   `SRS.md` --- functional requirements, non-functional requirements,
    use cases, business rules, and system behavior.
-   `DATA_COLLECTION_POLICY.md` --- collection and data governance
    policy.
-   `INGESTION_ARCHITECTURE.md` --- detailed ingestion and checkpoint
    strategy, if maintained separately.

------------------------------------------------------------------------

# 2. Architecture Overview

## 2.1 Chosen Architecture

SteamScoop will use a **modular monolith with independent background
worker processes**.

The backend is deployed as one logical application with domain modules.
Celery workers execute long-running jobs in separate processes.
PostgreSQL is the system of record. Redis acts as the Celery broker and
may provide short-lived caching and distributed coordination.

This approach provides clear boundaries while avoiding the operational
cost of microservices during the initial development stage.

### Architectural characteristics

-   One primary backend codebase.
-   One primary PostgreSQL database.
-   Domain-oriented modules inside the backend.
-   Separate API, worker, and scheduler processes.
-   Asynchronous processing through Celery.
-   Versioned REST API.
-   External Steam integration isolated behind adapters.

## 2.2 Context Diagram

``` mermaid
flowchart LR
    Guest["Guest / Public User"]
    Member["Member / Researcher"]
    Admin["Administrator"]

    Steam["Steam Reviews API"]
    Store["Steam Store Metadata Source"]

    Web["SteamScoop Web Frontend"]
    API["SteamScoop FastAPI Backend"]
    Workers["Celery Workers"]
    DB[("PostgreSQL")]
    Redis[("Redis")]
    Storage[("Object / Model Artifact Storage")]

    Guest --> Web
    Member --> Web
    Admin --> Web
    Web --> API

    API --> DB
    API --> Redis

    Workers --> Redis
    Workers --> DB
    Workers --> Steam
    Workers --> Store
    Workers --> Storage
```

## 2.3 Logical Architecture

``` mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        React["React + TypeScript"]
        Charts["Apache ECharts"]
    end

    subgraph Application["Application Layer"]
        API["FastAPI Routes"]
        Auth["Authentication & Authorization"]
        Services["Application Services"]
        DTO["Pydantic Schemas"]
    end

    subgraph Domain["Domain Modules"]
        Games["Game Catalog"]
        Reviews["Review Management"]
        Intelligence["Game Intelligence"]
        Research["Research Workspace"]
        Admin["Administration"]
        Ingestion["Ingestion Orchestration"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        Repositories["SQLAlchemy Repositories"]
        SteamAdapter["Steam API Adapter"]
        Cache["Cache / Rate Limiter"]
        TaskPublisher["Celery Task Publisher"]
    end

    subgraph Async["Asynchronous Processing"]
        Celery["Celery Workers"]
        NLP["NLP Pipeline"]
        Aggregation["Analytics Aggregation"]
        Export["Export Worker"]
    end

    DB[("PostgreSQL")]
    Redis[("Redis")]

    React --> API
    Charts --> React
    API --> Auth
    API --> DTO
    API --> Services
    Services --> Games
    Services --> Reviews
    Services --> Intelligence
    Services --> Research
    Services --> Admin
    Services --> Ingestion

    Games --> Repositories
    Reviews --> Repositories
    Intelligence --> Repositories
    Research --> Repositories
    Ingestion --> Repositories

    Ingestion --> TaskPublisher
    TaskPublisher --> Redis
    Celery --> Redis
    Celery --> SteamAdapter
    Celery --> NLP
    Celery --> Aggregation
    Celery --> Export

    Repositories --> DB
    Cache --> Redis
    SteamAdapter --> Steam["Steam Reviews API"]
```

## 2.4 Architectural Layers

### Presentation layer

Responsibilities: - Render public dashboards and research interfaces. -
Collect search, filter, and comparison inputs. - Display asynchronous
job states. - Present model and dataset transparency. - Manage
client-side server-state caching.

The frontend must not contain privileged Steam API keys or database
credentials.

### API/application layer

Responsibilities: - Expose REST endpoints. - Validate request and
response schemas. - Apply authentication and authorization. - Enforce
business rules. - Coordinate domain services. - Return stable API
responses. - Enqueue asynchronous tasks.

Routes should remain thin. Business logic belongs in services, not route
handlers.

### Domain layer

Responsibilities: - Game catalog management. - Review lifecycle and
query behavior. - Sentiment, aspect, topic, and trend analytics. -
Research project and export permissions. - Ingestion job lifecycle and
policy.

Domain modules should avoid direct dependencies on frontend concerns.

### Infrastructure layer

Responsibilities: - Database persistence. - Steam API communication. -
Redis interaction. - Task publishing. - File/object storage. - Logging
and external integrations.

External services should be accessed through adapters or repository
interfaces.

### Worker layer

Responsibilities: - Historical review collection. - Incremental review
synchronization. - Review validation and mapping. - NLP inference. -
Analytics aggregation. - Export generation. - Recovery and
reconciliation.

Workers use the same domain and infrastructure code where practical, but
run independently from the API process.

------------------------------------------------------------------------

# 3. Component Design

## 3.1 Frontend Components

Technology: - React. - TypeScript. - Vite. - Tailwind CSS. - TanStack
Query. - Apache ECharts.

Suggested frontend structure:

``` text
frontend/
├── src/
│   ├── app/
│   │   ├── router/
│   │   ├── providers/
│   │   └── layouts/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── charts/
│   │   ├── filters/
│   │   ├── data-table/
│   │   └── feedback/
│   │
│   ├── features/
│   │   ├── dashboard/
│   │   ├── game-explorer/
│   │   ├── game-detail/
│   │   ├── review-explorer/
│   │   ├── aspect-intelligence/
│   │   ├── topic-intelligence/
│   │   ├── comparison/
│   │   ├── methodology/
│   │   ├── authentication/
│   │   ├── research-workspace/
│   │   └── administration/
│   │
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── query-client.ts
│   │   └── formatters.ts
│   │
│   ├── hooks/
│   ├── types/
│   └── main.tsx
│
├── public/
└── package.json
```

### Frontend module responsibilities

  Module                Responsibility
  --------------------- -------------------------------------------
  Dashboard             Platform-level statistics and trends
  Game Explorer         Search and discover indexed games
  Game Detail           Display per-game intelligence
  Review Explorer       Filter and paginate reviews
  Aspect Intelligence   Aspect frequency and sentiment
  Topic Intelligence    Topic clusters and representative reviews
  Comparison            Compare multiple games
  Methodology           Explain datasets and models
  Authentication        Registration, login, account state
  Research Workspace    Projects and saved analyses
  Administration        Ingestion jobs and operational status

### Frontend data behavior

-   TanStack Query manages server state, caching, and request lifecycle.
-   Filters should be represented in URL query parameters when
    shareable.
-   Long review lists must use server-side pagination.
-   Charts must show sample counts and data freshness.
-   Loading, empty, stale, and error states must be distinct.
-   The UI must not imply that a queued ingestion job has already
    completed.

## 3.2 Backend Application Components

Technology: - Python. - FastAPI. - Pydantic. - SQLAlchemy. - Alembic. -
HTTPX.

Suggested backend structure:

``` text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── routes/
│   │       └── dependencies/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── modules/
│   │   ├── games/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── reviews/
│   │   ├── intelligence/
│   │   ├── research/
│   │   ├── ingestion/
│   │   ├── users/
│   │   ├── administration/
│   │   └── exports/
│   │
│   ├── integrations/
│   │   └── steam/
│   │       ├── client.py
│   │       ├── mapper.py
│   │       ├── schemas.py
│   │       └── exceptions.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/
│   │
│   └── workers/
│       ├── celery_app.py
│       └── tasks/
│
├── tests/
├── alembic.ini
└── pyproject.toml
```

This is a proposed logical layout. The implementation may adjust file
placement while preserving domain boundaries.

### Route/service/repository responsibilities

**Router** - Parse HTTP request. - Validate request schema. - Resolve
authenticated principal. - Call application service. - Return response
schema.

**Service** - Enforce business rules. - Coordinate repositories and
external adapters. - Manage transactions at application boundaries. -
Publish asynchronous tasks where required.

**Repository** - Encapsulate SQLAlchemy queries. - Persist and retrieve
domain records. - Avoid HTTP-specific behavior.

**Integration adapter** - Handle Steam request format. - Map Steam
response fields. - Translate HTTP/API errors into internal exceptions. -
Isolate external API changes.

## 3.3 Steam Integration Component

The Steam integration must be isolated from domain logic.

Primary review endpoint:

`https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`

The adapter is responsible for: - Building the documented `input_json`
request. - Supplying App ID and collection filters. - Managing cursor
pagination. - Respecting page-size limits. - Handling HTTP 429 and
transient failures. - Validating response shape. - Mapping source fields
into internal schemas.

The adapter must not: - Store SteamID for standard analysis. - expose
Steam credentials to the frontend. - make requests directly from public
dashboard routes. - assume an undocumented numeric rate limit. -
construct cursor values.

### Review request profile

Historical collection:

``` python
{
    "appid": app_id,
    "filter": 1,
    "languages": ["all"],
    "review_type": 0,
    "purchase_type": 1,
    "num_per_page": 100,
    "cursor": cursor,
    "date_range_start": start_timestamp,
    "date_range_end": end_timestamp
}
```

Incremental collection:

``` python
{
    "appid": app_id,
    "filter": 2,
    "languages": ["all"],
    "review_type": 0,
    "purchase_type": 1,
    "num_per_page": 100,
    "cursor": cursor
}
```

Date-window parameters should be supplied according to the API contract
and only when both required boundaries are known.

The exact filter configuration must be persisted with the ingestion job
for reproducibility.

## 3.4 Game Catalog Component

Responsibilities: - Maintain unique Steam App ID records. - Store
normalized game metadata. - Track metadata freshness. - Mark games as
indexed or not indexed. - Provide search and detail queries. -
Coordinate approved initial ingestion requests.

Game metadata retrieval is isolated behind a Store metadata adapter
because Store endpoints may have different documentation and stability
characteristics from the Steamworks Reviews API.

## 3.5 Review Management Component

Responsibilities: - Persist normalized review data. - Enforce review
uniqueness. - Handle source update timestamps. - Compute content
hashes. - Track first and last collection timestamps. - Provide
paginated review queries. - Mark records requiring NLP reprocessing.

The review component does not own sentiment model execution. It
publishes processing work to the NLP pipeline.

## 3.6 Intelligence Component

Responsibilities: - Retrieve versioned sentiment predictions. - Retrieve
aspect and topic assignments. - Provide game-level aggregate metrics. -
Provide temporal summaries. - Provide comparison data. - Expose model
and dataset metadata.

Analytics endpoints should read precomputed or cached aggregates where
appropriate.

## 3.7 Research Component

Responsibilities: - Manage users' research projects. - Manage
project-game associations. - Save analysis configurations. - Store
immutable snapshots where implemented. - Enforce project visibility and
membership permissions. - Coordinate export requests.

Research project authorization must be checked in backend services for
every protected operation.

## 3.8 Administration Component

Responsibilities: - Register games for indexing. - Trigger approved
ingestion jobs. - Inspect job lifecycle and checkpoints. - Retry
eligible failures. - Inspect pipeline runs. - Manage model registry
metadata. - Manage roles and platform configuration. - Record audit
events.

Administrative functions must not be exposed through public routes
without authorization.

------------------------------------------------------------------------

# 4. Database Architecture

## 4.1 Database Strategy

PostgreSQL is the primary system of record.

Use one PostgreSQL database initially, with logical domain boundaries
represented by modules and table naming conventions. Separate databases
or schemas may be introduced later only when operational or
access-control requirements justify them.

Redis is not a durable replacement for PostgreSQL. Critical job status,
checkpoints, review records, and model predictions must be persisted in
PostgreSQL.

## 4.2 Logical Data Domains

1.  Game catalog.
2.  Review data.
3.  ML model registry and predictions.
4.  Topics and aspects.
5.  Analytics aggregates.
6.  Ingestion operations.
7.  Users and authorization.
8.  Research workspaces.
9.  Exports and audit records.

## 4.3 Entity Relationship Diagram

``` mermaid
erDiagram
    GAMES ||--o{ REVIEWS : contains
    GAMES ||--o{ INGESTION_JOBS : indexed_by
    INGESTION_JOBS ||--o{ COLLECTION_CHECKPOINTS : tracks
    INGESTION_JOBS ||--o{ INGESTION_BATCHES : records
    INGESTION_JOBS ||--o{ PIPELINE_RUNS : triggers

    REVIEWS ||--o{ SENTIMENT_PREDICTIONS : receives
    ML_MODELS ||--o{ SENTIMENT_PREDICTIONS : produces

    REVIEWS ||--o{ ASPECT_PREDICTIONS : receives
    ASPECTS ||--o{ ASPECT_PREDICTIONS : identifies
    ML_MODELS ||--o{ ASPECT_PREDICTIONS : produces

    GAMES ||--o{ TOPICS : has
    REVIEWS ||--o{ REVIEW_TOPICS : assigned
    TOPICS ||--o{ REVIEW_TOPICS : contains

    GAMES ||--o{ GAME_ANALYTICS : aggregates

    USERS ||--o{ RESEARCH_PROJECTS : owns
    RESEARCH_PROJECTS ||--o{ PROJECT_GAMES : includes
    GAMES ||--o{ PROJECT_GAMES : selected
    RESEARCH_PROJECTS ||--o{ SAVED_ANALYSES : stores
    RESEARCH_PROJECTS ||--o{ PROJECT_MEMBERS : has
    USERS ||--o{ PROJECT_MEMBERS : joins

    USERS ||--o{ EXPORT_JOBS : requests
    USERS ||--o{ AUDIT_LOGS : performs
```

## 4.4 Core Tables

### 4.4.1 `games`

  Column                     Type             Constraints / Notes
  -------------------------- ---------------- ---------------------
  id                         BIGINT or UUID   Primary key
  steam_app_id               BIGINT           Unique, not null
  name                       VARCHAR          Not null
  developer                  TEXT             Nullable
  publisher                  TEXT             Nullable
  header_image               TEXT             Nullable
  release_date               DATE             Nullable
  is_indexed                 BOOLEAN          Default false
  last_metadata_refresh_at   TIMESTAMPTZ      Nullable
  next_refresh_at            TIMESTAMPTZ      Nullable
  created_at                 TIMESTAMPTZ      Not null
  updated_at                 TIMESTAMPTZ      Not null

Use the Steam App ID as a unique external identifier. Internal primary
key type should be selected consistently across the project.

### 4.4.2 `reviews`

  Column               Type             Constraints / Notes
  -------------------- ---------------- --------------------------------
  id                   BIGINT or UUID   Primary key
  game_id              FK games.id      Not null
  steam_review_id      VARCHAR          Not null
  review_text          TEXT             Subject to source terms
  language             VARCHAR          Nullable
  recommended          BOOLEAN          Steam `voted_up`
  playtime_forever     INTEGER          Nullable
  playtime_at_review   INTEGER          Nullable
  votes_up             INTEGER          Default 0
  votes_funny          INTEGER          Default 0
  steam_purchase       BOOLEAN          Nullable
  received_for_free    BOOLEAN          Nullable
  review_created_at    TIMESTAMPTZ      Source timestamp
  review_updated_at    TIMESTAMPTZ      Source timestamp
  first_collected_at   TIMESTAMPTZ      Not null
  last_collected_at    TIMESTAMPTZ      Not null
  content_hash         CHAR(64)         Hash of model-relevant content

Constraints: - Unique `(game_id, steam_review_id)`. - Foreign key to
games. - Index on `(game_id, review_created_at)`. - Index on
`(game_id, language)`. - Do not persist SteamID for standard SteamScoop
analytics.

### 4.4.3 `ml_models`

  Column                Type             Notes
  --------------------- ---------------- ---------------------------------------------
  id                    BIGINT or UUID   Primary key
  model_name            VARCHAR          Model family/name
  model_version         VARCHAR          Version identifier
  task                  VARCHAR          sentiment, aspect, topic, language
  supported_languages   JSONB            Supported language codes
  artifact_reference    TEXT             Model artifact location
  status                VARCHAR          experimental, validated, active, deprecated
  created_at            TIMESTAMPTZ      Creation time

A uniqueness constraint should cover the selected model identity and
version.

### 4.4.4 `sentiment_predictions`

  Column              Type              Notes
  ------------------- ----------------- ------------------------------
  id                  BIGINT or UUID    Primary key
  review_id           FK reviews.id     Not null
  model_id            FK ml_models.id   Not null
  sentiment           VARCHAR           positive, negative, neutral
  confidence          NUMERIC           Nullable
  prediction_status   VARCHAR           success, unsupported, failed
  predicted_at        TIMESTAMPTZ       Not null

Recommended uniqueness: `(review_id, model_id)` for one sentiment result
per review/model version.

### 4.4.5 `aspects`

  Column             Type             Notes
  ------------------ ---------------- ------------------------
  id                 BIGINT or UUID   Primary key
  name               VARCHAR          Unique within taxonomy
  description        TEXT             Definition
  taxonomy_version   VARCHAR          Version identifier
  is_active          BOOLEAN          Default true

### 4.4.6 `aspect_predictions`

  Column          Type              Notes
  --------------- ----------------- --------------------------
  id              BIGINT or UUID    Primary key
  review_id       FK reviews.id     Not null
  model_id        FK ml_models.id   Not null
  aspect_id       FK aspects.id     Not null
  sentiment       VARCHAR           Aspect sentiment
  confidence      NUMERIC           Nullable
  evidence_text   TEXT              Optional supporting span
  predicted_at    TIMESTAMPTZ       Not null

### 4.4.7 `topics`

  Column              Type             Notes
  ------------------- ---------------- ----------------------------
  id                  BIGINT or UUID   Primary key
  game_id             FK games.id      Not null
  topic_name          VARCHAR          Nullable or reviewed label
  topic_description   TEXT             Nullable
  model_version       VARCHAR          Topic model version
  created_at          TIMESTAMPTZ      Not null

### 4.4.8 `review_topics`

  Column        Type            Notes
  ------------- --------------- ---------------
  review_id     FK reviews.id   Composite key
  topic_id      FK topics.id    Composite key
  probability   NUMERIC         Nullable

Primary key: `(review_id, topic_id)`.

### 4.4.9 `game_analytics`

Stores precomputed metrics by game and aggregation period.

Suggested columns: - `id` - `game_id` - `aggregation_date` -
`aggregation_interval` - `total_reviews` - `processed_reviews` -
`positive_count` - `negative_count` - `neutral_count` -
`sentiment_model_id` - `computed_at`

Aggregates must identify the model version and eligible review
population.

## 4.5 Ingestion Operations Tables

### `ingestion_jobs`

Suggested columns: - `id` - `game_id` - `job_type` - `status` -
`target_reviews` - `collected_reviews` - `configuration` JSONB -
`started_at` - `completed_at` - `error_message` - `created_at`

The `configuration` field should preserve sampling windows, filters,
page size, and other collection parameters used by the job.

### `collection_checkpoints`

Suggested columns: - `id` - `job_id` - `game_id` - `collection_type` -
`window_start` - `window_end` - `cursor` - `last_seen_created_at` -
`last_seen_updated_at` - `pages_completed` - `reviews_collected` -
`completed` - `updated_at`

Each historical bucket must have an independent checkpoint.

### `ingestion_batches`

Suggested columns: - `id` - `job_id` - `page_number` - `fetched_count` -
`inserted_count` - `updated_count` - `skipped_count` - `status` -
`request_started_at` - `request_completed_at` - `error_message`

### `pipeline_runs`

Suggested columns: - `id` - `ingestion_job_id` - `pipeline_name` -
`status` - `processed_records` - `failed_records` - `model_version` -
`started_at` - `completed_at`

## 4.6 Research and User Tables

Suggested tables: - `users` - `roles` - `permissions` - `user_roles` -
`research_projects` - `project_members` - `project_games` -
`saved_analyses` - `analysis_snapshots` - `export_jobs` - `audit_logs`

Important constraints: - Project owner must reference a valid user. -
Project-game association must be unique. - Project membership must be
unique per user/project. - Private project access must be authorized
server-side. - Export jobs must reference their requesting user.

## 4.7 Indexing Strategy

Initial indexes:

``` sql
CREATE UNIQUE INDEX uq_games_steam_app_id
ON games (steam_app_id);

CREATE UNIQUE INDEX uq_reviews_game_review
ON reviews (game_id, steam_review_id);

CREATE INDEX idx_reviews_game_created
ON reviews (game_id, review_created_at DESC);

CREATE INDEX idx_reviews_game_language
ON reviews (game_id, language);

CREATE INDEX idx_ingestion_jobs_status_created
ON ingestion_jobs (status, created_at DESC);

CREATE INDEX idx_checkpoints_job
ON collection_checkpoints (job_id);

CREATE INDEX idx_sentiment_review_model
ON sentiment_predictions (review_id, model_id);
```

Additional indexes should be based on query profiling. Avoid creating
indexes for every filter without measuring write and storage overhead.

Partitioning is not required for the MVP. Consider partitioning only
after review volume and query profiling justify it.

## 4.8 Transaction Boundaries

The most important ingestion transaction is:

1.  Upsert review records for one fetched page.
2.  Record batch outcome.
3.  Persist next cursor and checkpoint counters.
4.  Commit all changes together.

If any required write fails, the transaction must roll back. The worker
must not advance to the next cursor.

For NLP processing, prediction writes and processing status updates
should also be transactional where practical.

------------------------------------------------------------------------

# 5. Data Flow Design

## 5.1 End-to-End Data Lifecycle

``` mermaid
flowchart TD
    A["Game registered"] --> B["Metadata retrieval"]
    B --> C["Historical ingestion job"]
    C --> D["Steam Reviews API"]
    D --> E["Validate and map reviews"]
    E --> F["PostgreSQL review upsert"]
    F --> G["Checkpoint commit"]
    G --> H["NLP task queue"]
    H --> I["Language detection"]
    I --> J["Sentiment inference"]
    J --> K["Aspect analysis"]
    K --> L["Topic assignment"]
    L --> M["Store versioned predictions"]
    M --> N["Analytics aggregation"]
    N --> O["Public dashboard and Review Explorer"]
```

## 5.2 Game Registration Flow

1.  Admin submits Steam App ID.
2.  Backend validates App ID.
3.  Game service checks for existing record.
4.  Metadata adapter requests game details.
5.  Mapper normalizes metadata.
6.  Repository persists game.
7.  Admin may trigger historical collection.
8.  Job service creates an ingestion job and publishes a Celery task.

If metadata retrieval fails, the system records the failure and does not
create fabricated metadata.

## 5.3 Historical Collection Flow

``` mermaid
sequenceDiagram
    actor Admin
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Redis
    participant Worker as Celery Worker
    participant Steam as Steam Reviews API

    Admin->>API: Request historical collection
    API->>DB: Create ingestion job and checkpoints
    API->>Redis: Publish task
    API-->>Admin: 202 Accepted + job ID

    Redis->>Worker: Deliver task
    Worker->>DB: Load checkpoint
    Worker->>Steam: Fetch page with cursor
    Steam-->>Worker: Reviews + next cursor
    Worker->>Worker: Validate and map
    Worker->>DB: Begin transaction
    Worker->>DB: Upsert reviews
    Worker->>DB: Save batch and checkpoint
    Worker->>DB: Commit transaction

    loop Until quota or boundary
        Worker->>Steam: Fetch next page
        Steam-->>Worker: Reviews + cursor
        Worker->>DB: Persist batch and checkpoint
    end

    Worker->>DB: Mark job completed/partial
```

### Historical sampling configuration

Default profile:

  Setting                                     Value
  ---------------------------- --------------------
  Maximum initial target         5,000 reviews/game
  Number of temporal buckets                     10
  Target per bucket                       Up to 500
  Page size                                     100
  Historical filter                          Recent
  Languages                           All available
  Review type                                   All
  Purchase type                                 All

The sampling implementation must: - Determine a documented historical
range. - Divide the range into time windows. - Persist each window's
boundaries. - Maintain independent cursor state for each window. - Stop
at quota, end of eligible results, or a terminal error. - Record actual
sample counts. - Document that temporal quota sampling is not random
sampling.

## 5.4 Weekly Incremental Flow

``` mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Scheduler as Scheduler Task
    participant DB as PostgreSQL
    participant Redis
    participant Worker as Incremental Worker
    participant Steam as Steam Reviews API
    participant NLP as NLP Queue

    Beat->>Scheduler: Weekly trigger
    Scheduler->>DB: Find due indexed games
    Scheduler->>DB: Create eligible jobs
    Scheduler->>Redis: Publish per-game tasks

    Redis->>Worker: Deliver task
    Worker->>DB: Load successful watermark
    Worker->>Worker: Calculate overlap boundary
    Worker->>Steam: Request Updated reviews
    Steam-->>Worker: Reviews + cursor
    Worker->>DB: Upsert and checkpoint
    Worker->>Steam: Continue pagination
    Steam-->>Worker: More reviews or end
    Worker->>DB: Commit safe watermark
    Worker->>NLP: Enqueue changed review IDs
```

### Watermark rules

-   Store the watermark in UTC.
-   Use a configurable 14-day overlap by default.
-   Do not advance watermark after a partial or failed collection.
-   Repeated retrieval is safe because review upserts are idempotent.
-   The overlap period is a SteamScoop operational setting, not an
    official Steam guarantee.

## 5.5 Review Update and NLP Reprocessing Flow

1.  Incoming review matches an existing unique key.
2.  Compare source update timestamp.
3.  Ignore stale incoming data.
4.  If newer, compare model-relevant content hash.
5.  Update review source fields.
6.  If text or language changed, create an NLP task.
7.  If only votes changed, skip NLP inference.
8.  Store new predictions under the selected model version.
9.  Refresh affected aggregates.

Content hash should be calculated from canonicalized model-relevant
fields, such as review text and language. It should not include
unrelated author or hardware metadata.

## 5.6 Public Analytics Read Flow

``` mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI
    participant Cache as Redis Cache
    participant DB as PostgreSQL

    User->>UI: Open game dashboard
    UI->>API: GET game analytics
    API->>Cache: Lookup aggregate cache
    alt Cache hit
        Cache-->>API: Cached analytics
    else Cache miss
        API->>DB: Query aggregate tables
        DB-->>API: Aggregate data
        API->>Cache: Store cache entry
    end
    API-->>UI: Analytics + freshness metadata
    UI-->>User: Render dashboard
```

Public read requests must not synchronously trigger Steam collection or
large-scale model inference.

## 5.7 Export Flow

1.  User submits export request.
2.  API validates identity, role, scope, quota, and permitted fields.
3.  API creates export job.
4.  API publishes task to Celery.
5.  Export worker queries authorized data in bounded batches.
6.  Worker creates CSV or JSON output.
7.  Worker stores the file in controlled object storage or an approved
    file location.
8.  Worker marks job complete and records expiry.
9.  User downloads through an authorization-checked route or expiring
    link.
10. Expiry process deletes or disables the file.

------------------------------------------------------------------------

# 6. Background Worker Architecture

## 6.1 Why Background Workers Are Required

Steam collection, NLP inference, aggregation, and export generation can
take longer than an ordinary HTTP request.

Running these operations synchronously would: - Increase API response
times. - Create request timeouts. - Couple public availability to Steam
API availability. - Make retry and recovery difficult. - Waste compute
resources when work is repeated.

Celery workers separate long-running work from request handling.

## 6.2 Technology

-   Celery: task execution and orchestration.
-   Redis: task broker and optional result backend.
-   Celery Beat: periodic scheduling.
-   PostgreSQL: durable job and checkpoint state.

PostgreSQL remains the authoritative source for job lifecycle and
checkpoint data. Celery result backend state must not be the only record
of job completion.

## 6.3 Worker Queues

Suggested queues:

  Queue           Responsibility                                Suggested priority
  --------------- --------------------------------------------- --------------------
  `ingestion`     Historical and incremental Steam collection   Normal
  `nlp`           Sentiment, aspect, and topic processing       Normal
  `aggregation`   Analytics aggregation                         Normal
  `exports`       CSV/JSON generation                           Low
  `maintenance`   Recovery, reconciliation, cleanup             Normal

Queue separation prevents large NLP or export tasks from starving
ingestion tasks.

## 6.4 Task Definitions

  -------------------------------------------------------------------------------
  Task                            Trigger                 Main responsibility
  ------------------------------- ----------------------- -----------------------
  `schedule_due_games`            Weekly Celery Beat      Find games due for
                                                          refresh

  `collect_historical_reviews`    Admin/indexing workflow Initial historical
                                                          sample

  `collect_incremental_reviews`   Weekly scheduler        Collect new/updated
                                                          reviews

  `process_review_batch`          After ingestion or      Run NLP pipeline
                                  content change          

  `aggregate_game_analytics`      After prediction        Refresh aggregates
                                  updates                 

  `recover_failed_jobs`           Every 30 minutes        Identify recoverable
                                                          jobs

  `reconcile_game_reviews`        Scheduled/manual        Revisit defined
                                                          collection ranges

  `generate_export`               User export request     Generate authorized
                                                          export

  `expire_export_files`           Periodic                Remove expired exports
  -------------------------------------------------------------------------------

## 6.5 Celery Configuration

Illustrative configuration:

``` python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "steamscoop",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    beat_schedule={
        "weekly-game-refresh": {
            "task": "app.workers.tasks.schedule_due_games",
            "schedule": crontab(
                day_of_week="mon",
                hour=2,
                minute=0,
            ),
        },
        "recover-ingestion-jobs": {
            "task": "app.workers.tasks.recover_failed_jobs",
            "schedule": 1800.0,
        },
    },
)
```

The weekly schedule uses Monday 02:00 UTC, equivalent to Monday 09:00
WIB. Deployment timezone and schedule must be configured explicitly.

This configuration is a baseline. Production deployment must also define
task time limits, retry policy, queue routing, worker concurrency, and
monitoring.

## 6.6 Task Reliability

Workers must assume that tasks can be delivered more than once.

Therefore: - Tasks must be idempotent. - Durable state must be read from
PostgreSQL. - Task payloads should contain identifiers, not large
datasets. - Retry must be bounded. - Permanent and transient errors must
be distinguished. - A worker crash must not cause checkpoint advancement
without committed data. - Duplicate active jobs must be prevented using
database constraints or atomic job-claim logic.

## 6.7 Retry and Backoff

Suggested behavior:

  -----------------------------------------------------------------------
  Failure                             Action
  ----------------------------------- -----------------------------------
  HTTP 400                            Permanent request/configuration
                                      error; no automatic retry

  HTTP 401/403                        Credential/access investigation

  HTTP 404                            Validate endpoint or App ID

  HTTP 429                            Respect Retry-After when present;
                                      exponential backoff

  HTTP 500--599                       Bounded exponential backoff

  Network timeout                     Bounded retry

  Invalid JSON                        Log response metadata; retry
                                      cautiously

  Database transaction failure        Roll back; retry only if safe

  Model inference failure             Record processing failure and retry
                                      according to policy
  -----------------------------------------------------------------------

Backoff formula:

`delay = min(base_delay * 2^retry_count, maximum_delay) + jitter`

The system must use a shared rate limiter across Steam-facing workers. A
per-worker limiter alone is insufficient when multiple workers share the
same API access pool.

## 6.8 Worker Concurrency

Initial recommendations: - Start with a small number of ingestion
workers. - Keep NLP workers independently configurable. - Use batch
inference where model support permits. - Limit simultaneous Steam
requests globally. - Increase worker concurrency only after measuring
throughput and rate-limit behavior.

Do not assume that adding workers increases Steam API throughput.

## 6.9 Recovery Process

The recovery task should: 1. Query PostgreSQL for stale running or
retryable jobs. 2. Verify worker lease/heartbeat information if
implemented. 3. Check whether an equivalent active job already exists.
4. Load the last committed checkpoint. 5. Mark the old attempt
interrupted where appropriate. 6. Requeue a safe recovery attempt. 7.
Record the recovery event and outcome.

A stale `running` status must not be treated as proof that a worker is
still active.

------------------------------------------------------------------------

# 7. NLP and Analytics Architecture

## 7.1 NLP Pipeline

``` mermaid
flowchart TD
    A["Eligible review IDs"] --> B["Load review text and language"]
    B --> C["Language detection / validation"]
    C --> D{"Supported language?"}
    D -->|No| E["Mark unsupported"]
    D -->|Yes| F["Sentiment model"]
    F --> G["Sentiment prediction"]
    G --> H["Aspect extraction and sentiment"]
    H --> I["Topic assignment"]
    I --> J["Persist versioned predictions"]
    J --> K["Schedule analytics aggregation"]
```

The pipeline may be staged so that MVP sentiment processing can operate
before advanced ABSA and topic modeling are ready.

## 7.2 Model Registry

The model registry should record: - Model name. - Model version. -
Task. - Supported languages. - Artifact reference. - Training/evaluation
metadata. - Evaluation metrics. - Activation status. - Creation
timestamp.

A model must not be considered production-validated solely because it is
registered.

## 7.3 Model Versioning

Predictions must reference immutable model version records.

When a new model is activated: - New tasks use the selected active
version. - Existing predictions remain associated with their original
version. - Reprocessing is an explicit operation. - Evaluation metrics
remain linked to the evaluated model version. - Aggregates must identify
which prediction version they summarize.

## 7.4 Candidate NLP Technologies

  -----------------------------------------------------------------------
  Capability              Candidate technology    Purpose
  ----------------------- ----------------------- -----------------------
  Baseline sentiment      scikit-learn            TF-IDF + Logistic
                                                  Regression / Linear SVM

  Transformer sentiment   Hugging Face            Contextual text
                          Transformers            classification

  Deep learning runtime   PyTorch                 Model inference and
                                                  training

  Embeddings              Sentence Transformers   Semantic
                                                  representations

  Topic modeling          BERTopic                Topic discovery

  Dimensionality          UMAP                    Embedding reduction
  reduction                                       

  Clustering              HDBSCAN                 Density-based topic
                                                  clusters

  Language detection      fastText                Language identification

  Experiment tracking     MLflow                  Experiment and model
                                                  tracking
  -----------------------------------------------------------------------

Technology selection must be validated through experiments. These
libraries are candidates, not a guarantee of model performance.

## 7.5 Analytics Aggregation

Aggregate tables should support: - Total review counts. - Recommendation
counts. - Sentiment counts and ratios. - Aspect-level sentiment. - Topic
frequencies. - Time-bucketed metrics. - Language coverage. - Dataset
freshness.

Every percentage must have a clearly defined denominator. Reviews
without a valid prediction should not silently be counted as neutral.

------------------------------------------------------------------------

# 8. API Architecture

## 8.1 API Design

-   REST API.
-   JSON request/response.
-   Version prefix `/api/v1`.
-   Pydantic validation.
-   Consistent error schema.
-   Server-side pagination.
-   Role-based access control for protected routes.

## 8.2 API Module Groups

### Public

-   `GET /games/search`
-   `GET /games/{app_id}`
-   `GET /games/{app_id}/reviews`
-   `GET /games/{app_id}/analytics`
-   `GET /games/{app_id}/sentiment`
-   `GET /games/{app_id}/aspects`
-   `GET /games/{app_id}/topics`
-   `GET /games/{app_id}/trends`
-   `POST /games/compare`
-   `GET /models`
-   `GET /methodology`

### Authentication

-   `POST /auth/register`
-   `POST /auth/login`
-   `POST /auth/logout`
-   `POST /auth/refresh`
-   `GET /auth/me`

### Research

-   `POST /research/projects`
-   `GET /research/projects`
-   `GET /research/projects/{id}`
-   `PATCH /research/projects/{id}`
-   `POST /research/projects/{id}/games`
-   `POST /research/projects/{id}/analyses`
-   `POST /research/projects/{id}/exports`

### Administration

-   `POST /admin/ingestion/jobs`
-   `GET /admin/ingestion/jobs`
-   `GET /admin/ingestion/jobs/{id}`
-   `POST /admin/ingestion/jobs/{id}/retry`
-   `GET /admin/pipeline-runs`
-   `GET /admin/models`
-   `GET /admin/users`

## 8.3 Asynchronous API Behavior

For ingestion and export requests: - API validates and creates a durable
job record. - API publishes a task. - API returns `202 Accepted` with
job ID. - Client polls a job status endpoint. - Job status is read from
PostgreSQL. - API does not claim completion until the worker commits the
final state.

A transactional outbox pattern MAY be introduced if task publication and
database job creation need stronger delivery guarantees. For a smaller
MVP, use a carefully designed publish-after-commit flow with recovery
for jobs left queued but not dispatched.

------------------------------------------------------------------------

# 9. Security Architecture

## 9.1 Authentication

For authenticated features: - Use secure password hashing such as
Argon2id. - Use secure session cookies or short-lived access tokens with
refresh handling. - Define expiry and logout invalidation. - Avoid
storing secrets in frontend bundles. - Consider CSRF protections when
cookie-based authentication is used.

## 9.2 Authorization

Use role-based access control: - Guest: public resources. - Member:
personal workspace. - Researcher: authorized research and export
capabilities. - Moderator: explicitly scoped moderation permissions. -
Admin: platform operations.

Authorization must be checked in backend services, not only in frontend
route guards.

## 9.3 Secrets Management

Secrets include: - Database credentials. - Redis credentials. - Steam
publisher API key, if legitimately available. - Session signing
secrets. - Object storage credentials. - Email provider credentials.

Secrets must be supplied through environment variables or a managed
secret store and excluded from version control.

## 9.4 Data Minimization

-   Do not store SteamID for standard analytics.
-   Do not store unnecessary hardware metadata.
-   Avoid retaining complete raw Steam responses unless required and
    permitted.
-   Store only normalized fields required for product behavior and
    research.
-   Define retention and deletion policies before public deployment.

------------------------------------------------------------------------

# 10. Caching Strategy

## 10.1 Cacheable Data

Potential cache targets: - Game metadata. - Game-level aggregate
analytics. - Sentiment distribution. - Aspect summaries. - Topic
summaries. - Popular game lists. - Methodology and model registry
metadata.

## 10.2 Cache Rules

-   Cache keys must include relevant query parameters and
    model/aggregation version.
-   Cache entries must have bounded TTL.
-   Aggregation refresh should invalidate or version affected cache
    entries.
-   User-specific and private workspace data must not be placed in
    shared public cache without correct isolation.
-   Redis cache loss must not result in data loss.

Caching is an optimization. PostgreSQL remains the source of truth.

------------------------------------------------------------------------

# 11. Deployment Architecture

## 11.1 Logical Deployment

``` mermaid
flowchart TB
    Browser["User Browser"]

    subgraph Hosting["Application Hosting"]
        Frontend["Frontend Hosting"]
        API["FastAPI API Container"]
        Beat["Celery Beat Container"]
        IngestWorker["Celery Ingestion Worker"]
        NLPWorker["Celery NLP Worker"]
        ExportWorker["Celery Export Worker"]
    end

    subgraph Managed["Data Services"]
        Postgres[("Managed PostgreSQL")]
        Redis[("Managed Redis")]
        ObjectStore[("Object Storage")]
    end

    Steam["Steam APIs"]

    Browser --> Frontend
    Frontend --> API

    API --> Postgres
    API --> Redis

    Beat --> Redis
    Redis --> IngestWorker
    Redis --> NLPWorker
    Redis --> ExportWorker

    IngestWorker --> Postgres
    IngestWorker --> Steam
    NLPWorker --> Postgres
    ExportWorker --> Postgres
    ExportWorker --> ObjectStore
```

## 11.2 Development Environment

Use Docker Compose to run: - Frontend. - FastAPI. - PostgreSQL. -
Redis. - Celery worker. - Celery Beat.

Local development should provide repeatable environment configuration
and database migrations.

## 11.3 Production Environment

Possible hosting arrangement: - Frontend: Vercel or equivalent
static/frontend hosting. - Backend: container hosting such as Render,
Railway, or equivalent. - PostgreSQL: managed PostgreSQL such as Neon or
Supabase, or another managed provider. - Redis: managed Redis such as
Upstash or equivalent. - Workers: separate container processes. - Model
artifacts and exports: object storage where needed.

These are deployment options, not fixed vendor commitments. Provider
selection must consider cost, persistent worker support, networking,
database limits, data residency, and operational reliability.

## 11.4 Environment Separation

At minimum: - Development. - Test/CI. - Production.

Production data and secrets must not be copied into development
environments without an approved sanitization process.

## 11.5 Database Migrations

-   Use Alembic for schema migrations.
-   Migrations must be version-controlled.
-   Production migrations must be reviewed.
-   Destructive changes require backup and rollback planning.
-   Application deployment must be compatible with the migration
    sequence.

------------------------------------------------------------------------

# 12. Observability and Operations

## 12.1 Logging

Use structured logs with: - Timestamp. - Severity. - Service/process
name. - Request or task ID. - Job ID where applicable. - Game ID where
applicable. - Event name. - Error category. - Duration and record counts
where relevant.

Do not log secrets, passwords, tokens, or unnecessary personal
identifiers.

## 12.2 Metrics

Track: - API request rate and latency. - API error rate. - Steam request
count. - HTTP 429 count. - Steam request latency. - Ingestion job
duration. - Reviews fetched, inserted, updated, and skipped. -
Checkpoint recovery count. - Celery queue backlog. - NLP processing
throughput. - NLP failure rate. - Aggregation duration. - Export job
duration. - Database connection utilization. - Cache hit ratio.

## 12.3 Initial Monitoring

For the MVP, structured application logs and a basic admin ingestion
dashboard may be sufficient.

Prometheus and Grafana can be introduced when the number of workers,
services, or operational requirements justify dedicated metrics
infrastructure.

## 12.4 Alerts

Potential alerts: - Repeated HTTP 429 responses. - Ingestion jobs stuck
in running state. - Retry exhaustion. - Worker queue backlog exceeding a
configured threshold. - Database storage or connection pressure. -
Repeated NLP failures. - No successful weekly refresh within the
expected window.

Alert thresholds must be configured from observed baseline behavior
rather than guessed.

------------------------------------------------------------------------

# 13. Testing Strategy

## 13.1 Unit Tests

Test: - Steam response mapping. - Review content hashing. - Sampling
bucket calculation. - Watermark and overlap calculation. - Job state
transitions. - Upsert conflict behavior. - Authorization rules. -
Aggregate calculations. - API schema validation.

## 13.2 Integration Tests

Test: - FastAPI and PostgreSQL integration. - SQLAlchemy transactions. -
Alembic migrations. - Redis and Celery task dispatch. - Steam API client
with mocked HTTP responses. - Atomic review and checkpoint
persistence. - NLP prediction persistence. - Export job generation.

## 13.3 Failure Tests

Test: - HTTP 429 and Retry-After. - Steam API 5xx. - Network timeout. -
Malformed response. - Worker termination between fetch and commit. -
Database failure during page transaction. - Duplicate Celery task
delivery. - Concurrent job creation. - Repeated cursor. - Model
inference failure. - Export worker failure.

## 13.4 End-to-End Tests

Test: - Guest search and game detail. - Review explorer filters. -
Analytics rendering. - Game comparison. - Registration and login. -
Research project creation. - Analysis saving. - Export authorization. -
Admin ingestion lifecycle.

------------------------------------------------------------------------

# 14. Architecture Decisions and Rationale

  -----------------------------------------------------------------------
  Decision                Choice                  Rationale
  ----------------------- ----------------------- -----------------------
  Backend architecture    Modular monolith        Lower operational
                                                  complexity and clear
                                                  internal boundaries

  API framework           FastAPI                 Python ecosystem, type
                                                  validation, async
                                                  support

  Frontend                React + TypeScript      Component model and
                                                  type safety

  Build tooling           Vite                    Lightweight frontend
                                                  development and build

  Database                PostgreSQL              Relational integrity,
                                                  JSONB, transactions

  ORM                     SQLAlchemy              Python database
                                                  abstraction

  Migrations              Alembic                 Versioned schema
                                                  evolution

  Task queue              Celery                  Mature asynchronous
                                                  task execution

  Broker                  Redis                   Simple queue broker and
                                                  cache

  Charts                  Apache ECharts          Flexible analytical
                                                  visualization

  ML baseline             scikit-learn            Establish measurable
                                                  baseline

  Transformer runtime     PyTorch / Hugging Face  Contextual NLP models

  Topic modeling          BERTopic                Embedding-based topic
                                                  discovery

  Containerization        Docker                  Reproducible
                                                  environments

  Testing                 pytest / Playwright     Backend and
                                                  browser-level tests
  -----------------------------------------------------------------------

## 14.1 Technologies Not Required for MVP

The following are intentionally excluded unless a demonstrated
requirement emerges: - Kubernetes. - Kafka. - Apache Spark. - MongoDB. -
GraphQL. - Elasticsearch/OpenSearch. - Microservices. - Dedicated data
warehouse. - LLM API dependency.

Avoiding these technologies reduces operational complexity and cost
while the dataset and user demand are still being validated.

------------------------------------------------------------------------

# 15. Scalability and Future Evolution

## 15.1 Expected Growth Path

### Stage 1 --- MVP

-   One API deployment.
-   One PostgreSQL database.
-   One Redis instance.
-   Small ingestion worker pool.
-   Small NLP worker pool.
-   Precomputed analytics.

### Stage 2 --- Growing Dataset

-   Tune indexes and query plans.
-   Increase worker capacity.
-   Batch NLP inference.
-   Add object storage for artifacts and exports.
-   Add dedicated metrics monitoring.
-   Introduce read replicas if read load justifies them.

### Stage 3 --- Larger Workloads

Potential changes: - Separate ML inference service if GPU or model
lifecycle needs justify it. - Dedicated search engine if PostgreSQL
search becomes insufficient. - Partition review tables after
profiling. - Separate analytical storage or warehouse if reporting
workloads interfere with transactional workloads. - Event-driven
internal processing if task orchestration becomes complex.

These are future options, not MVP dependencies.

## 15.2 Scaling Constraints

Primary expected bottlenecks: - Steam API request limits. - NLP
inference throughput. - PostgreSQL review query patterns. - Aggregate
recomputation. - Export generation. - Model artifact loading and memory.

Scaling should address measured bottlenecks individually.

------------------------------------------------------------------------

# 16. Implementation Sequence

Recommended implementation order:

  -----------------------------------------------------------------------
  Phase                   Workstream              Deliverable
  ----------------------- ----------------------- -----------------------
  1                       Project foundation      Repository,
                                                  configuration, Docker
                                                  Compose, CI

  2                       Database foundation     Core models, Alembic
                                                  migrations,
                                                  repositories

  3                       Steam integration       API client, mapper,
                                                  error handling

  4                       Ingestion reliability   Historical collector,
                                                  checkpoints, upsert

  5                       Background processing   Celery, Redis,
                                                  scheduler, recovery

  6                       NLP baseline            Language handling and
                                                  sentiment predictions

  7                       Analytics API           Aggregates and public
                                                  endpoints

  8                       Frontend MVP            Dashboard, game
                                                  explorer, review
                                                  explorer

  9                       Advanced intelligence   ABSA, topic modeling,
                                                  temporal trends

  10                      Research capabilities   Authentication,
                                                  workspace, exports

  11                      Production hardening    Security,
                                                  observability, backup,
                                                  load testing
  -----------------------------------------------------------------------

Do not begin with advanced infrastructure before the core ingestion and
data model have been validated.

------------------------------------------------------------------------

# 17. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Architectural mitigation
  ----------------------------------- -----------------------------------
  Steam API changes                   Isolated adapter and contract tests

  Rate limiting                       Shared rate limiter and bounded
                                      backoff

  Worker crash                        Transactional checkpoints and
                                      recovery

  Duplicate tasks                     Idempotent upserts and active-job
                                      constraints

  NLP cost                            Batch processing and separate
                                      queues

  Model drift                         Model registry and periodic
                                      evaluation

  Database growth                     Query profiling, retention policy,
                                      measured partitioning

  Public traffic spikes               Cache, pagination, API rate limits

  Export misuse                       Role checks, quotas, expiring
                                      downloads

  Data policy changes                 Source adapter, configurable
                                      retention, policy review

  Misleading analytics                Provenance, sample counts, model
                                      version disclosures
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 18. Open Technical Decisions

The following items require validation before final production
implementation:

1.  Internal primary key strategy: BIGINT or UUID.
2.  Whether to use one schema or multiple PostgreSQL schemas.
3.  Exact Steam Store metadata source and its permitted usage.
4.  Historical sampling date-range defaults and quota reallocation
    algorithm.
5.  Durable task dispatch approach: publish-after-commit recovery or
    transactional outbox.
6.  Exact global Steam request rate policy based on observed responses
    and terms.
7.  Model hosting and inference hardware requirements.
8.  Object storage provider and export expiry.
9.  Authentication session strategy.
10. Cache provider, TTL, and invalidation mechanism.
11. Backup frequency and recovery objectives.
12. Whether topic modeling runs per game or across a broader corpus.
13. Whether multilingual models are loaded into the same worker pool or
    separate queues.
14. Production monitoring and alerting provider.

Each decision should be recorded with owner, date, rationale, and
impact.

------------------------------------------------------------------------

# 19. Final Architecture Summary

SteamScoop uses a modular monolith with independent background workers.

The React frontend communicates with a FastAPI backend through a
versioned REST API. The backend enforces product rules and persists
durable state in PostgreSQL. Redis supports task brokering and optional
caching. Celery workers execute Steam review ingestion, NLP inference,
aggregation, recovery, and export tasks.

Steam review data is collected through the supported Steam Reviews API,
normalized, deduplicated, and persisted with transactional checkpoints.
NLP predictions are versioned and stored independently from source
review data. Public analytics are served from precomputed or cached
results so that user-facing requests do not depend on live Steam API
calls or expensive model inference.

The architecture prioritizes reliability, data provenance,
methodological transparency, security, and operational simplicity.

**Product:** SteamScoop\
**Architecture:** Modular Monolith + Asynchronous Workers\
**Backend:** FastAPI\
**Frontend:** React + TypeScript\
**Database:** PostgreSQL\
**Broker/Cache:** Redis\
**Workers:** Celery\
**Analytics/ML:** scikit-learn, PyTorch, Hugging Face, Sentence
Transformers, BERTopic\
**Visualization:** Apache ECharts\
**Deployment:** Docker-based services

**End of Document**
