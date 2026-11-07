# SteamScoop

# Software Requirements Specification (SRS)

**Document ID:** SS-SRS-001\
**Version:** 1.0\
**Status:** Baseline Specification\
**Date:** 8 November 2026\
**Product:** SteamScoop\
**Product Type:** Public Game Intelligence & Research Web Application\
**Tagline:** Understand Games Through Data.

------------------------------------------------------------------------

## Document Control

  -----------------------------------------------------------------------
  Field                               Value
  ----------------------------------- -----------------------------------
  Document title                      SteamScoop Software Requirements
                                      Specification

  Document version                    1.0

  Product owner                       SteamScoop project owner

  Intended audience                   Product owner, software engineers,
                                      ML engineers, QA engineers,
                                      researchers, academic reviewers

  Normative language                  **MUST** indicates a mandatory
                                      requirement; **SHOULD** indicates a
                                      recommended requirement; **MAY**
                                      indicates an optional capability

  Source specification                SteamScoop PRD v1.0
  -----------------------------------------------------------------------

### Revision History

  -----------------------------------------------------------------------
  Version                 Date                    Description
  ----------------------- ----------------------- -----------------------
  1.0                     2026-11-08              Initial SRS baseline
                                                  derived from SteamScoop
                                                  PRD v1.0

  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional
requirements, non-functional requirements, use cases, business rules,
data requirements, and expected system behavior of SteamScoop.

The document is intended to provide a verifiable engineering
specification for designing, implementing, testing, deploying, and
maintaining the SteamScoop web application.

It translates the product-level objectives into requirements that can be
implemented and validated by engineering and quality assurance teams.

## 1.2 Product Scope

SteamScoop is a public Game Intelligence and Research Platform that
collects publicly accessible Steam game reviews and transforms review
text into structured analytical information.

The platform uses Natural Language Processing (NLP), sentiment analysis,
Aspect-Based Sentiment Analysis (ABSA), topic modeling, and statistical
analytics to help users understand player feedback.

The system provides:

-   Public game discovery and search.
-   Game metadata and review dataset exploration.
-   Review ingestion and synchronization.
-   Sentiment analysis.
-   Aspect-level analysis.
-   Topic modeling.
-   Temporal analytics.
-   Multi-game comparison.
-   Dataset and methodology transparency.
-   Optional research workspaces and saved analyses.
-   Controlled dataset and analysis exports.
-   Administrative ingestion and model management.

SteamScoop does not replace Steam, certify objective game quality, or
claim that Steam reviews represent all players.

## 1.3 Product Objectives

The system shall:

1.  Make game review analytics publicly accessible without mandatory
    registration.
2.  Convert unstructured player feedback into structured analytical
    insights.
3.  Support exploration of individual reviews and aggregate patterns.
4.  Support comparison of multiple indexed games.
5.  Provide transparent data provenance, sampling methodology, and model
    information.
6.  Support repeatable research workflows through optional accounts and
    workspaces.
7.  Collect and process Steam reviews asynchronously without blocking
    public analytics.
8.  Preserve data integrity and support recovery from interrupted
    ingestion jobs.

## 1.4 Intended Audience

  -----------------------------------------------------------------------
  Audience                            Expected use of this document
  ----------------------------------- -----------------------------------
  Product owner                       Confirm scope, priorities, and
                                      acceptance conditions

  Frontend engineers                  Implement user interfaces and
                                      client-side behavior

  Backend engineers                   Implement APIs, business logic,
                                      authorization, and persistence

  Data/ML engineers                   Implement ingestion, NLP pipelines,
                                      model evaluation, and analytics

  QA engineers                        Derive functional, integration,
                                      security, and regression tests

  Researchers and lecturers           Understand analytical assumptions,
                                      limitations, and reproducibility

  Maintainers                         Operate, troubleshoot, and extend
                                      the platform
  -----------------------------------------------------------------------

## 1.5 Definitions and Acronyms

  -----------------------------------------------------------------------
  Term                                Definition
  ----------------------------------- -----------------------------------
  Steam App ID                        Unique numeric identifier for a
                                      game in Steam

  Review                              A user-submitted review retrieved
                                      from Steam

  Recommendation status               Steam's `voted_up` field indicating
                                      whether the reviewer recommends the
                                      game

  Sentiment                           SteamScoop model prediction about
                                      the polarity expressed in review
                                      text

  ABSA                                Aspect-Based Sentiment Analysis;
                                      identifies aspects discussed and
                                      associated sentiment

  Aspect                              A predefined game-related
                                      dimension, such as gameplay or
                                      performance

  Topic modeling                      Unsupervised or semi-supervised
                                      discovery of recurring themes in
                                      review text

  Ingestion                           Retrieval and persistence of game
                                      metadata or reviews from an
                                      external source

  Historical sampling                 Initial collection of reviews from
                                      defined historical time windows

  Incremental collection              Collection of newly created or
                                      updated reviews after initial
                                      ingestion

  Cursor                              Opaque pagination token returned by
                                      the Steam Reviews API

  Checkpoint                          Persisted collection state used to
                                      resume interrupted ingestion

  Watermark                           Timestamp boundary used to identify
                                      the range already processed

  Upsert                              Insert a record or update the
                                      existing record when a uniqueness
                                      conflict occurs

  Provenance                          Information describing where data
                                      came from, when it was collected,
                                      and how it was processed

  Workspace                           Authenticated user's saved research
                                      environment

  Snapshot                            Persisted representation of an
                                      analysis configuration and/or
                                      result at a point in time

  Guest                               Unauthenticated user of public
                                      platform features

  Member                              Authenticated user with personal
                                      workspace capabilities

  Researcher                          User granted enhanced
                                      research-project and export
                                      privileges

  Admin                               Authorized operator with
                                      platform-management privileges

  P0/P1/P2                            Requirement priority: critical for
                                      MVP / important follow-up / future
                                      enhancement
  -----------------------------------------------------------------------

## 1.6 Normative Conventions

-   **MUST**: mandatory for conformance.
-   **MUST NOT**: prohibited behavior.
-   **SHOULD**: recommended unless a documented reason justifies
    otherwise.
-   **SHOULD NOT**: discouraged unless a documented reason justifies
    otherwise.
-   **MAY**: optional behavior.

Each requirement has a unique identifier to support traceability and
testing.

------------------------------------------------------------------------

# 2. Overall Description

## 2.1 Product Perspective

SteamScoop is a web application composed initially of a modular backend
and independently executed background workers.

The system is divided into the following logical subsystems:

1.  **Presentation subsystem:** public website, dashboards, search,
    review explorer, comparison tools, and authenticated workspace.
2.  **Application/API subsystem:** request validation, business rules,
    authentication, authorization, and response composition.
3.  **Steam integration subsystem:** Steam API client, metadata
    retrieval, review retrieval, pagination, rate limiting, and response
    mapping.
4.  **Ingestion subsystem:** job orchestration, historical sampling,
    incremental collection, checkpointing, retries, and recovery.
5.  **NLP subsystem:** language detection, sentiment analysis, aspect
    analysis, and topic modeling.
6.  **Analytics subsystem:** aggregate metrics, temporal summaries,
    comparison datasets, and cached query results.
7.  **Research subsystem:** projects, memberships, saved analyses,
    snapshots, and exports.
8.  **Administration subsystem:** user/role administration, ingestion
    monitoring, model registry, and operational audit logs.

The initial deployment SHOULD use a modular monolith for the API and
separate Celery worker processes for long-running work. The system MUST
NOT require microservices to deliver the MVP.

## 2.2 System Context

External systems:

-   Steam User Reviews API.
-   Steam Store metadata endpoints where available and permitted.
-   Email delivery provider, if account verification or password
    recovery is enabled.
-   Object storage for model artifacts and large export files, if
    required.
-   Hosting, database, and cache services.

SteamScoop is responsible for handling external API failures, validating
returned data, recording collection provenance, and avoiding unbounded
requests triggered by public users.

## 2.3 User Classes and Characteristics

### 2.3.1 Guest

A guest is an unauthenticated user.

Guests can: - Open public dashboards. - Search indexed games. - View
game details and analytics. - Explore reviews. - Filter and sort review
results. - Compare eligible games. - Read methodology and model
documentation.

Guests cannot: - Save persistent workspaces. - Create private research
projects. - Manage platform ingestion. - Change model configurations. -
Access administrative endpoints.

### 2.3.2 Member

A member is an authenticated user.

Members inherit guest capabilities and can: - Create personal research
projects, subject to configured limits. - Save analysis
configurations. - Save snapshots. - View personal export history. -
Manage personal account settings.

### 2.3.3 Researcher

A researcher is an authenticated user granted research privileges.

Researchers can: - Create and manage research projects. - Add project
collaborators when collaboration is enabled. - Export datasets within
configured limits. - Share eligible read-only analysis links. - Access
research-oriented metadata and snapshots.

Researcher status MUST be granted through an explicit authorization
process. A user must not become a researcher solely by registering.

### 2.3.4 Moderator

A moderator is an optional operational role for moderation features if
user-generated platform content is introduced.

Moderators MUST NOT automatically receive ingestion, model-management,
or user-administration privileges.

### 2.3.5 Administrator

An administrator can: - Register and index games. - Trigger or cancel
permitted ingestion jobs. - Inspect job status, logs, and checkpoints. -
Retry failed jobs. - Manage user roles and platform configuration. -
Register and activate model versions. - Inspect system health and audit
logs.

Administrative permissions MUST be enforced by the backend.

## 2.4 Operating Environment

The initial supported environment is:

-   Modern desktop and mobile web browsers.
-   Responsive web interface.
-   Frontend implemented with React and TypeScript.
-   Backend implemented with Python and FastAPI.
-   PostgreSQL as the primary relational database.
-   Redis as task broker/cache where configured.
-   Celery workers for asynchronous jobs.
-   Docker-based development and deployment.

Specific browser versions and hosting limits shall be defined in
deployment configuration.

## 2.5 Design and Implementation Constraints

-   SteamScoop MUST use the currently supported Steam Reviews API
    endpoint and MUST NOT depend on the deprecated legacy review
    endpoint.
-   Steam API pagination MUST use the returned cursor.
-   Public browsing MUST NOT directly trigger unrestricted review
    ingestion.
-   The system MUST handle Steam API rate limiting and transient
    failures.
-   Raw Steam author identifiers and unnecessary personal metadata
    SHOULD NOT be persisted.
-   Model predictions MUST be associated with model versions.
-   Expensive NLP and export operations MUST execute asynchronously.
-   The initial architecture SHOULD remain a modular monolith plus
    background workers.
-   SteamScoop MUST review applicable Steam terms and content policies
    before public deployment or redistribution of review text.

## 2.6 Assumptions and Dependencies

-   Steam makes the required public review data available through its
    supported API at the time of collection.
-   API availability, returned fields, rate limits, and policies may
    change.
-   Not all Steam games will necessarily be indexable or return the same
    amount of data.
-   Review availability and language distribution vary by game.
-   NLP models may not support every language equally.
-   Hosting capacity and model inference costs may constrain throughput.
-   Public availability of a review does not by itself establish
    unrestricted rights to store or redistribute it.

------------------------------------------------------------------------

# 3. System Features and Functional Requirements

## 3.1 Public Access and Navigation

### Description

The platform shall allow users to access core analytical functionality
without registering.

### Requirements

-   **FR-PUB-001 (P0):** The system MUST allow unauthenticated users to
    open the public landing page.
-   **FR-PUB-002 (P0):** The system MUST allow guests to access public
    game search.
-   **FR-PUB-003 (P0):** The system MUST allow guests to view indexed
    game details and available analytics.
-   **FR-PUB-004 (P0):** The system MUST allow guests to explore reviews
    subject to public query limits.
-   **FR-PUB-005 (P0):** The system MUST allow guests to compare
    eligible indexed games.
-   **FR-PUB-006 (P0):** The system MUST expose methodology, data
    coverage, and model information without requiring registration.
-   **FR-PUB-007 (P0):** The system MUST display an understandable empty
    state when no indexed result is available.
-   **FR-PUB-008 (P0):** The system MUST NOT require account creation
    for core public analytics.
-   **FR-PUB-009 (P1):** The system SHOULD provide navigation to account
    and workspace features for authenticated users.

### System behavior

1.  A guest requests a public page.
2.  The frontend requests the corresponding public API resource.
3.  The backend validates parameters and applies public rate limits.
4.  The backend returns available indexed data.
5.  If data is unavailable, the API returns a defined not-found or
    not-yet-indexed response.
6.  The frontend displays a clear explanation and does not silently
    initiate ingestion.

## 3.2 Game Search and Discovery

### Description

Users shall be able to locate Steam games indexed by SteamScoop.

### Requirements

-   **FR-GAME-001 (P0):** The system MUST support searching games by
    title.
-   **FR-GAME-002 (P0):** The system MUST support lookup by Steam App
    ID.
-   **FR-GAME-003 (P0):** Search results MUST identify the game and its
    Steam App ID.
-   **FR-GAME-004 (P0):** Search results SHOULD display available
    metadata such as header image, release date, developer, and
    publisher.
-   **FR-GAME-005 (P0):** The system MUST distinguish indexed games from
    games that are known but not yet indexed.
-   **FR-GAME-006 (P0):** A public search MUST NOT automatically start
    an unbounded ingestion job.
-   **FR-GAME-007 (P1):** The system SHOULD support sorting and
    pagination for search results.
-   **FR-GAME-008 (P1):** The system MAY provide genre or category
    filters when reliable metadata is available.

### System behavior

-   Search input is normalized for whitespace and validated for length.
-   The backend searches the local game catalog first.
-   If an external discovery mechanism is enabled, it must use bounded
    requests and must not imply that the game has already been analyzed.
-   Selecting an indexed game opens its detail page.
-   Selecting an unindexed game displays its indexing status or an
    explanatory message.

## 3.3 Game Metadata Management

### Requirements

-   **FR-META-001 (P0):** The system MUST store a unique Steam App ID
    for every indexed game.
-   **FR-META-002 (P0):** The system MUST store the game title.
-   **FR-META-003 (P1):** The system SHOULD store available developer,
    publisher, release date, and image metadata.
-   **FR-META-004 (P0):** The system MUST record metadata retrieval or
    refresh timestamps.
-   **FR-META-005 (P0):** Metadata refresh MUST NOT overwrite valid data
    with an empty or malformed response without recording the failure.
-   **FR-META-006 (P1):** Administrators SHOULD be able to request a
    metadata refresh.
-   **FR-META-007 (P0):** The system MUST preserve the association
    between a game and its reviews when metadata changes.

## 3.4 Steam Review Ingestion

### Description

The system shall collect reviews using the supported Steam User Reviews
API through controlled asynchronous jobs.

### Requirements

-   **FR-ING-001 (P0):** The system MUST use
    `IUserReviewsService/GetAppReviews` for review retrieval.
-   **FR-ING-002 (P0):** The system MUST send the API request parameters
    through the documented `input_json` parameter.
-   **FR-ING-003 (P0):** The system MUST support cursor-based
    pagination.
-   **FR-ING-004 (P0):** The system MUST support a page size no greater
    than the API maximum of 100.
-   **FR-ING-005 (P0):** The system MUST support historical collection
    using configured date windows.
-   **FR-ING-006 (P0):** The system MUST support incremental collection
    using the Updated filter.
-   **FR-ING-007 (P0):** The system MUST persist successfully collected
    review records.
-   **FR-ING-008 (P0):** The system MUST deduplicate reviews using a
    stable review identifier scoped to the game.
-   **FR-ING-009 (P0):** The system MUST record ingestion job status and
    diagnostic information.
-   **FR-ING-010 (P0):** The system MUST support retry of transient API
    and network failures.
-   **FR-ING-011 (P0):** The system MUST respect rate-limit responses
    and apply backoff.
-   **FR-ING-012 (P0):** The system MUST support recovery from an
    interrupted collection job.
-   **FR-ING-013 (P0):** The system MUST record collection timestamps
    and collection configuration.
-   **FR-ING-014 (P0):** The system MUST keep Steam API calls out of
    synchronous public dashboard request paths.
-   **FR-ING-015 (P1):** The system SHOULD support
    administrator-triggered reconciliation.
-   **FR-ING-016 (P0):** The system MUST record partial completion when
    a job cannot reach its target.
-   **FR-ING-017 (P0):** The system MUST NOT claim that a sample is
    exhaustive unless completeness has been established by the
    collection method.
-   **FR-ING-018 (P0):** The system MUST avoid persisting SteamID and
    unnecessary author or hardware fields.

### Historical sampling behavior

1.  An administrator or approved indexing workflow creates a historical
    collection job.
2.  The system determines the configured collection range.
3.  The range is divided into temporal buckets.
4.  Each bucket receives a target quota, initially up to 500 reviews.
5.  The collector requests pages using the Recent filter and the
    bucket's date range.
6.  Each page is validated, mapped, and upserted.
7.  The page's next cursor and counters are persisted atomically with
    the page data.
8.  The bucket ends when its quota is reached, no more eligible reviews
    are returned, or a terminal error occurs.
9.  Unfilled quota MAY be reallocated according to the configured
    sampling policy.
10. The job records actual sample counts and bucket-level outcomes.

### Incremental collection behavior

1.  The scheduler selects indexed games whose refresh time is due.
2.  The system loads the last successful watermark.
3.  The system calculates the overlap boundary using the configured
    overlap duration.
4.  The collector requests reviews using the Updated filter.
5.  The collector continues pagination until it reaches the boundary or
    the API returns no more eligible results.
6.  New records are inserted; existing records are updated when the
    source version is newer.
7.  Relevant content changes are identified for NLP reprocessing.
8.  The watermark is committed only after the collection run completes
    successfully.
9.  The next refresh time is updated according to the configured
    schedule.

## 3.5 Ingestion Job Management and Checkpointing

### Requirements

-   **FR-JOB-001 (P0):** Every ingestion execution MUST have a unique
    job identifier.
-   **FR-JOB-002 (P0):** Every job MUST identify its game and collection
    type.
-   **FR-JOB-003 (P0):** The system MUST expose job states: queued,
    running, retrying, completed, partial, failed, and cancelled.
-   **FR-JOB-004 (P0):** The system MUST persist cursor checkpoints for
    paginated collection.
-   **FR-JOB-005 (P0):** Historical collection MUST maintain independent
    checkpoint state for each date bucket.
-   **FR-JOB-006 (P0):** Review batch persistence and cursor advancement
    MUST be atomic.
-   **FR-JOB-007 (P0):** A resumed job MUST continue from the latest
    committed checkpoint.
-   **FR-JOB-008 (P0):** The system MUST prevent conflicting active jobs
    for the same game and collection scope unless concurrency is
    explicitly supported.
-   **FR-JOB-009 (P0):** The system MUST record page-level counts for
    fetched, inserted, updated, skipped, and failed records where
    available.
-   **FR-JOB-010 (P1):** Administrators SHOULD be able to inspect job
    and batch logs.
-   **FR-JOB-011 (P0):** A job MUST NOT be marked completed if required
    collection work remains uncommitted.
-   **FR-JOB-012 (P0):** A failed job MUST preserve enough state for
    diagnosis and safe retry.

### Job state transitions

Allowed normal transitions:

-   queued → running
-   running → completed
-   running → partial
-   running → retrying
-   retrying → running
-   running → failed
-   queued → cancelled
-   running → cancelled, if cancellation is safely supported

Terminal states are completed, partial, failed, and cancelled. A retry
operation SHOULD create a new execution attempt or explicitly record a
new attempt within the existing job history.

## 3.6 Review Explorer

### Requirements

-   **FR-REV-001 (P0):** The system MUST display review text when
    permitted by applicable data policies.
-   **FR-REV-002 (P0):** The system MUST display the review's Steam
    recommendation status separately from predicted sentiment.
-   **FR-REV-003 (P0):** The system MUST support pagination.
-   **FR-REV-004 (P0):** The system MUST support filtering by sentiment
    when predictions are available.
-   **FR-REV-005 (P1):** The system SHOULD support filtering by
    language.
-   **FR-REV-006 (P1):** The system SHOULD support filtering by date
    range.
-   **FR-REV-007 (P1):** The system SHOULD support filtering by aspect
    and topic when those predictions are available.
-   **FR-REV-008 (P1):** The system SHOULD support sorting by creation
    date, update date, and helpful votes.
-   **FR-REV-009 (P0):** The system MUST show an appropriate state when
    a review has not yet been processed.
-   **FR-REV-010 (P0):** The system MUST NOT fabricate missing review
    attributes or model predictions.

## 3.7 Sentiment Analysis

### Requirements

-   **FR-SENT-001 (P0):** The system MUST support classifying supported
    review text into positive, negative, or neutral sentiment.
-   **FR-SENT-002 (P0):** Every prediction MUST reference a model
    identifier and version.
-   **FR-SENT-003 (P0):** The system MUST store prediction timestamps.
-   **FR-SENT-004 (P0):** The system MUST store confidence scores when
    the selected model provides a meaningful score.
-   **FR-SENT-005 (P0):** The system MUST allow predictions to be
    recomputed using a new model version without recollecting the
    original review.
-   **FR-SENT-006 (P0):** The system MUST distinguish unavailable,
    pending, successful, and failed inference states.
-   **FR-SENT-007 (P0):** The system MUST NOT treat Steam's
    recommendation flag as the sentiment label.
-   **FR-SENT-008 (P1):** The system SHOULD expose model evaluation
    metrics and supported languages.
-   **FR-SENT-009 (P0):** The system MUST preserve the model version
    used for each displayed prediction.

## 3.8 Aspect-Based Sentiment Analysis

### Requirements

-   **FR-ABSA-001 (P1):** The system SHOULD identify one or more
    relevant game aspects in a review.
-   **FR-ABSA-002 (P1):** The system SHOULD classify sentiment for each
    identified aspect.
-   **FR-ABSA-003 (P1):** Aspect predictions MUST reference the model
    version and aspect taxonomy version.
-   **FR-ABSA-004 (P1):** The system SHOULD store confidence and
    evidence text where supported.
-   **FR-ABSA-005 (P1):** The system MUST support the initial aspect
    taxonomy defined in the PRD or a versioned successor.
-   **FR-ABSA-006 (P1):** The system MUST permit an aspect to be absent
    from a review.
-   **FR-ABSA-007 (P1):** The system MUST distinguish no detected aspect
    from inference failure.
-   **FR-ABSA-008 (P1):** Aspect analytics MUST disclose the number of
    reviews contributing to each metric.

Initial aspects include gameplay, game mechanics, difficulty, graphics,
story, performance, multiplayer, content, pricing, audio, community, and
updates.

## 3.9 Topic Modeling

### Requirements

-   **FR-TOPIC-001 (P1):** The system SHOULD generate topic clusters
    from review text.
-   **FR-TOPIC-002 (P1):** Topic assignments MUST reference a topic
    model version.
-   **FR-TOPIC-003 (P1):** The system SHOULD store topic assignment
    probability or confidence where available.
-   **FR-TOPIC-004 (P1):** The system SHOULD provide representative
    reviews for each topic.
-   **FR-TOPIC-005 (P1):** The system SHOULD display topic frequency and
    distribution.
-   **FR-TOPIC-006 (P1):** Topic labels MUST be presented as
    model-generated or reviewed interpretations.
-   **FR-TOPIC-007 (P1):** The system MUST distinguish
    outlier/unassigned reviews from processing failures.
-   **FR-TOPIC-008 (P1):** Topic model changes MUST be versioned and
    traceable.

## 3.10 Temporal Analytics

### Requirements

-   **FR-TIME-001 (P1):** The system SHOULD aggregate review and
    sentiment metrics over time.
-   **FR-TIME-002 (P1):** The system SHOULD allow users to select a
    supported date range and aggregation interval.
-   **FR-TIME-003 (P1):** The system MUST display sample counts
    alongside temporal percentages or rates.
-   **FR-TIME-004 (P1):** The system SHOULD identify changes in review
    volume and sentiment distribution.
-   **FR-TIME-005 (P1):** The system MUST disclose the data collection
    coverage underlying the time series.
-   **FR-TIME-006 (P1):** The system MUST NOT imply that correlation
    between an update and sentiment change proves causation.

## 3.11 Game Comparison

### Requirements

-   **FR-COMP-001 (P1):** The system SHOULD allow comparison of at least
    two indexed games.
-   **FR-COMP-002 (P1):** The system SHOULD compare review volume and
    sentiment distribution.
-   **FR-COMP-003 (P1):** The system SHOULD compare aspect-level
    sentiment when available.
-   **FR-COMP-004 (P1):** The system SHOULD compare topic distributions
    when available.
-   **FR-COMP-005 (P1):** The system SHOULD compare temporal trends when
    data coverage permits.
-   **FR-COMP-006 (P0):** The system MUST display the review sample size
    for each compared game.
-   **FR-COMP-007 (P0):** The system MUST disclose material differences
    in collection periods, language coverage, and model versions.
-   **FR-COMP-008 (P1):** The system SHOULD prevent or warn about
    comparisons where analytical coverage is materially incompatible.
-   **FR-COMP-009 (P1):** The system SHOULD allow eligible comparison
    results to be saved by authenticated users.

## 3.12 Dataset and Methodology Center

### Requirements

-   **FR-METH-001 (P0):** The system MUST publish the review collection
    source.
-   **FR-METH-002 (P0):** The system MUST describe the historical
    sampling method.
-   **FR-METH-003 (P0):** The system MUST describe incremental
    collection behavior.
-   **FR-METH-004 (P0):** The system MUST display dataset collection or
    refresh timestamps.
-   **FR-METH-005 (P0):** The system MUST publish model names and
    versions used for predictions.
-   **FR-METH-006 (P0):** The system MUST publish available model
    evaluation metrics.
-   **FR-METH-007 (P0):** The system MUST describe known data and model
    limitations.
-   **FR-METH-008 (P1):** The system SHOULD provide dataset export in
    CSV or JSON subject to policy and authorization.
-   **FR-METH-009 (P0):** The system MUST identify Steam as the source
    and must not imply official Valve endorsement.
-   **FR-METH-010 (P0):** The system MUST distinguish observed source
    fields from model-derived fields.

## 3.13 Authentication and Account Management

### Requirements

-   **FR-AUTH-001 (P1):** The system SHOULD support account
    registration.
-   **FR-AUTH-002 (P1):** The system SHOULD support secure login and
    logout.
-   **FR-AUTH-003 (P1):** The system SHOULD support account recovery
    through a verified process.
-   **FR-AUTH-004 (P1):** The system MUST hash passwords using an
    appropriate password hashing algorithm such as Argon2id.
-   **FR-AUTH-005 (P1):** The system MUST enforce server-side
    authorization for protected resources.
-   **FR-AUTH-006 (P1):** The system MUST prevent users from accessing
    another user's private workspace without permission.
-   **FR-AUTH-007 (P1):** The system SHOULD support role assignment by
    authorized administrators.
-   **FR-AUTH-008 (P1):** Institutional email MUST NOT be mandatory for
    general registration unless a future product policy explicitly
    changes this.
-   **FR-AUTH-009 (P1):** The system MUST provide a safe session or
    token invalidation mechanism on logout.

## 3.14 Research Workspace

### Requirements

-   **FR-WS-001 (P1):** Authenticated members MUST be able to create a
    research project within configured limits.
-   **FR-WS-002 (P1):** Project owners MUST be able to edit project
    metadata.
-   **FR-WS-003 (P1):** Project owners MUST be able to add indexed games
    to a project.
-   **FR-WS-004 (P1):** Members MUST be able to save analysis
    configurations.
-   **FR-WS-005 (P1):** The system SHOULD support immutable analysis
    snapshots.
-   **FR-WS-006 (P2):** The system MAY support project collaborators.
-   **FR-WS-007 (P2):** The system MAY support read-only public sharing
    links.
-   **FR-WS-008 (P1):** The system MUST enforce project visibility and
    membership permissions.
-   **FR-WS-009 (P1):** The system MUST record project creation and
    modification timestamps.
-   **FR-WS-010 (P1):** The system MUST prevent unauthorized users from
    modifying or deleting another user's private project.

## 3.15 Export Management

### Requirements

-   **FR-EXP-001 (P1):** Authorized users SHOULD be able to request
    dataset or analysis exports.
-   **FR-EXP-002 (P1):** Large exports MUST execute asynchronously.
-   **FR-EXP-003 (P1):** Every export request MUST have a unique job
    identifier and status.
-   **FR-EXP-004 (P1):** Export requests MUST enforce role-based quotas
    and row/size limits.
-   **FR-EXP-005 (P1):** Exports MUST include relevant provenance and
    model-version metadata.
-   **FR-EXP-006 (P1):** Export content MUST comply with applicable
    Steam data terms and SteamScoop retention and redistribution
    policies.
-   **FR-EXP-007 (P1):** Export files SHOULD expire after a configured
    retention period.
-   **FR-EXP-008 (P1):** Users MUST only access exports they are
    authorized to access.

## 3.16 Administration and Audit

### Requirements

-   **FR-ADM-001 (P0):** Authorized administrators MUST be able to
    inspect ingestion jobs.
-   **FR-ADM-002 (P0):** Authorized administrators MUST be able to
    trigger approved ingestion jobs.
-   **FR-ADM-003 (P0):** Authorized administrators MUST be able to retry
    eligible failed jobs.
-   **FR-ADM-004 (P0):** The system MUST record administrative actions
    that affect users, roles, ingestion, models, or system
    configuration.
-   **FR-ADM-005 (P1):** Administrators SHOULD be able to inspect model
    versions and evaluation results.
-   **FR-ADM-006 (P1):** Administrators SHOULD be able to activate or
    deactivate model versions through a controlled process.
-   **FR-ADM-007 (P0):** Administrative endpoints MUST be inaccessible
    to guests and ordinary members.
-   **FR-ADM-008 (P0):** The system MUST NOT expose secrets, API keys,
    or sensitive operational configuration in public responses or logs.

------------------------------------------------------------------------

# 4. External Interface Requirements

## 4.1 User Interface

The web interface shall provide:

-   Public landing and navigation.
-   Game search and discovery.
-   Game detail dashboard.
-   Review explorer.
-   Aspect and topic analytics.
-   Game comparison interface.
-   Methodology pages.
-   Authentication and workspace interfaces.
-   Administrative ingestion monitor.

The interface MUST provide loading, empty, success, and error states for
asynchronous operations.

Charts MUST provide labels, units, legends, and sample sizes where
relevant. Color MUST NOT be the only means of communicating sentiment
categories.

## 4.2 API Interface

The backend shall expose versioned REST endpoints under `/api/v1`.

Expected public endpoint groups:

  Method   Endpoint                      Purpose
  -------- ----------------------------- ----------------------------------
  GET      `/games/search`               Search indexed games
  GET      `/games/{app_id}`             Retrieve game details
  GET      `/games/{app_id}/reviews`     Retrieve paginated reviews
  GET      `/games/{app_id}/analytics`   Retrieve aggregate analytics
  GET      `/games/{app_id}/sentiment`   Retrieve sentiment distribution
  GET      `/games/{app_id}/aspects`     Retrieve aspect analysis
  GET      `/games/{app_id}/topics`      Retrieve topic analysis
  GET      `/games/{app_id}/trends`      Retrieve temporal metrics
  POST     `/games/compare`              Compare games
  GET      `/models`                     List published models
  GET      `/methodology`                Retrieve methodology information

Authentication, research, export, and administrative routes shall be
separately grouped and protected.

API responses SHOULD include: - Request or correlation identifier. -
Stable error code. - Human-readable error message. - Pagination metadata
where applicable. - Data freshness metadata where relevant.

## 4.3 Steam API Interface

The Steam integration shall:

-   Use
    `https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`.
-   Send documented review parameters through `input_json`.
-   Use a maximum page size of 100.
-   Use cursor pagination.
-   Use Recent for historical traversal and Updated for incremental
    collection.
-   Use date range parameters only as supported by the API and provide
    both boundaries when required.
-   Handle HTTP status codes and malformed responses.
-   Treat HTTP 429 as a rate-limit response.
-   Avoid assuming a universal numeric request quota.
-   Use a publisher key only when legitimately available and authorized.

The Steam Store metadata integration shall be isolated behind an adapter
because Store endpoints may have different documentation and stability
characteristics from the Steamworks Web API.

## 4.4 Database Interface

PostgreSQL shall store relational application data, reviews, model
predictions, collection state, and research metadata.

Redis may be used for: - Celery task brokering. - Short-lived cache
entries. - Distributed rate-limit coordination where configured.

Redis MUST NOT be the sole durable store for ingestion checkpoints or
business-critical job state.

## 4.5 Background Task Interface

Celery tasks shall be used for: - Historical ingestion. - Incremental
ingestion. - NLP inference. - Analytics aggregation. - Export
generation. - Recovery and reconciliation.

Task payloads SHOULD contain identifiers and configuration references
rather than large review payloads.

------------------------------------------------------------------------

# 5. Non-Functional Requirements

## 5.1 Performance

-   **NFR-PERF-001:** Common cached analytics API requests SHOULD target
    a server response time below 500 ms under the agreed baseline load.
-   **NFR-PERF-002:** Public review endpoints MUST use pagination and
    MUST NOT return an unbounded review collection.
-   **NFR-PERF-003:** Large exports MUST run asynchronously.
-   **NFR-PERF-004:** NLP inference MUST NOT execute synchronously in
    ordinary public dashboard requests.
-   **NFR-PERF-005:** Analytics aggregation SHOULD use precomputed
    results or cache where profiling justifies it.
-   **NFR-PERF-006:** Performance targets MUST be validated under a
    documented test environment, dataset size, and concurrency level.

## 5.2 Availability and Reliability

-   **NFR-REL-001:** Public analytics SHOULD target 99% monthly
    availability for the MVP, excluding announced maintenance and
    third-party outages.
-   **NFR-REL-002:** Failure of Steam API ingestion MUST NOT make
    already stored public analytics unavailable.
-   **NFR-REL-003:** Background tasks MUST support bounded retries for
    transient errors.
-   **NFR-REL-004:** Ingestion MUST be idempotent.
-   **NFR-REL-005:** Critical database writes MUST use transactions.
-   **NFR-REL-006:** Checkpoint advancement MUST be atomic with the
    corresponding review batch persistence.
-   **NFR-REL-007:** The system MUST expose partial and failed states
    rather than silently treating incomplete work as successful.
-   **NFR-REL-008:** The system SHOULD define backup and restore
    procedures before public production deployment.

## 5.3 Scalability

-   **NFR-SCALE-001:** The application SHOULD support horizontal scaling
    of Celery workers without creating duplicate active jobs for the
    same collection scope.
-   **NFR-SCALE-002:** Public read operations SHOULD be independently
    scalable from ingestion and ML processing.
-   **NFR-SCALE-003:** The system SHOULD support growth in indexed games
    and reviews without requiring a microservices migration.
-   **NFR-SCALE-004:** Database indexing and partitioning decisions MUST
    be based on measured query and storage behavior.
-   **NFR-SCALE-005:** Rate limiting MUST be coordinated across workers
    where multiple workers share the same Steam API access pool.

## 5.4 Security

-   **NFR-SEC-001:** Passwords MUST be stored using a modern adaptive
    password hashing algorithm.
-   **NFR-SEC-002:** Protected resources MUST be authorized on the
    backend.
-   **NFR-SEC-003:** Administrative actions MUST require an authorized
    role.
-   **NFR-SEC-004:** Secrets and API keys MUST be stored outside source
    control.
-   **NFR-SEC-005:** Public endpoints MUST apply reasonable request and
    query limits.
-   **NFR-SEC-006:** User input MUST be validated and safely
    parameterized.
-   **NFR-SEC-007:** The system MUST use HTTPS in production.
-   **NFR-SEC-008:** Authentication sessions or tokens MUST have defined
    expiry and invalidation behavior.
-   **NFR-SEC-009:** Logs MUST NOT contain passwords, access tokens,
    Steam API keys, or unnecessary personal identifiers.
-   **NFR-SEC-010:** Export downloads MUST verify ownership or
    authorization.
-   **NFR-SEC-011:** Administrative and role changes SHOULD be recorded
    in audit logs.
-   **NFR-SEC-012:** The application SHOULD apply protections against
    common web vulnerabilities, including injection, cross-site
    scripting, cross-site request forgery where applicable, and insecure
    direct object references.

## 5.5 Privacy and Data Minimization

-   **NFR-PRIV-001:** SteamScoop MUST minimize the collection and
    retention of personal data.
-   **NFR-PRIV-002:** SteamID MUST NOT be stored for ordinary review
    sentiment analysis.
-   **NFR-PRIV-003:** Unnecessary author and hardware metadata MUST NOT
    be retained.
-   **NFR-PRIV-004:** Account data MUST be limited to information
    required for authentication and workspace functionality.
-   **NFR-PRIV-005:** The platform MUST publish an appropriate privacy
    policy before public registration is enabled.
-   **NFR-PRIV-006:** Data retention and deletion procedures MUST be
    documented.
-   **NFR-PRIV-007:** Public export behavior MUST comply with applicable
    source terms and platform policy.

## 5.6 Usability and Accessibility

-   **NFR-UX-001:** The interface MUST support common desktop and mobile
    viewport sizes.
-   **NFR-UX-002:** Navigation and terminology MUST remain consistent
    across modules.
-   **NFR-UX-003:** Charts MUST include meaningful titles, labels,
    units, and legends.
-   **NFR-UX-004:** Sentiment MUST NOT be represented by color alone.
-   **NFR-UX-005:** Loading, empty, and error states MUST be
    understandable.
-   **NFR-UX-006:** Analytical terms SHOULD include concise explanations
    or tooltips.
-   **NFR-UX-007:** Core flows SHOULD be operable using keyboard
    navigation.
-   **NFR-UX-008:** The application SHOULD follow WCAG 2.1 AA as a
    design target.

## 5.7 Maintainability

-   **NFR-MAINT-001:** Backend modules MUST have clear responsibility
    boundaries.
-   **NFR-MAINT-002:** Steam-specific request and response handling MUST
    be isolated behind an integration adapter.
-   **NFR-MAINT-003:** Database schema changes MUST be managed through
    versioned migrations.
-   **NFR-MAINT-004:** Public API contracts MUST be documented.
-   **NFR-MAINT-005:** Critical business logic MUST have automated
    tests.
-   **NFR-MAINT-006:** Model versions and evaluation artifacts MUST be
    traceable.
-   **NFR-MAINT-007:** Configuration MUST be environment-driven rather
    than hard-coded.

## 5.8 Observability

-   **NFR-OBS-001:** The system MUST log ingestion job lifecycle events.
-   **NFR-OBS-002:** The system MUST record collection counts and batch
    outcomes.
-   **NFR-OBS-003:** The system SHOULD track HTTP 429 responses and
    retry counts.
-   **NFR-OBS-004:** The system SHOULD track API latency, worker
    duration, and queue backlog.
-   **NFR-OBS-005:** Logs SHOULD use structured fields and correlation
    identifiers.
-   **NFR-OBS-006:** Operational dashboards MUST distinguish live system
    metrics from illustrative or sample data.

## 5.9 Compatibility and Portability

-   **NFR-COMP-001:** The frontend SHOULD support current stable
    versions of major browsers.
-   **NFR-COMP-002:** The application SHOULD run in containerized
    development and deployment environments.
-   **NFR-COMP-003:** Environment-specific configuration MUST be
    externalized.
-   **NFR-COMP-004:** Database and cache dependencies MUST be
    documented.

## 5.10 Research Validity and Transparency

-   **NFR-RESEARCH-001:** The system MUST distinguish observed source
    data from model-derived values.
-   **NFR-RESEARCH-002:** Every model-derived prediction MUST be
    traceable to a model version.
-   **NFR-RESEARCH-003:** Dataset summaries MUST disclose sample size
    and collection period.
-   **NFR-RESEARCH-004:** The system MUST document sampling limitations.
-   **NFR-RESEARCH-005:** The system MUST NOT imply that Steam reviews
    represent all players.
-   **NFR-RESEARCH-006:** The system MUST NOT equate sentiment with
    objective game quality.
-   **NFR-RESEARCH-007:** Comparisons MUST disclose material differences
    in data coverage and model versions.
-   **NFR-RESEARCH-008:** Model evaluation MUST use documented and
    appropriately separated evaluation data.

------------------------------------------------------------------------

# 6. Use Cases

## 6.1 Use Case Summary

  Use Case ID   Use Case                             Primary Actor      Priority
  ------------- ------------------------------------ ------------------ ----------
  UC-001        Search for a game                    Guest              P0
  UC-002        View game analytics                  Guest              P0
  UC-003        Explore and filter reviews           Guest              P0
  UC-004        Compare games                        Guest              P1
  UC-005        Inspect aspects and topics           Guest              P1
  UC-006        Read methodology and model details   Guest              P0
  UC-007        Register and authenticate            Visitor            P1
  UC-008        Create research project              Member             P1
  UC-009        Save an analysis                     Member             P1
  UC-010        Export research data                 Researcher         P1
  UC-011        Register a game for indexing         Admin              P0
  UC-012        Run historical collection            Admin/System       P0
  UC-013        Run weekly incremental collection    Scheduler/System   P0
  UC-014        Recover a failed ingestion job       Admin/System       P0
  UC-015        Process reviews using NLP            Worker/System      P0
  UC-016        Manage model versions                Admin              P1

## 6.2 UC-001 --- Search for a Game

**Primary actor:** Guest\
**Goal:** Find a game in the SteamScoop catalog.

**Preconditions:** - SteamScoop is available. - The game search endpoint
is operational.

**Trigger:** User submits a game title or Steam App ID.

**Main flow:** 1. User opens Game Explorer. 2. User enters a title or
App ID. 3. Frontend validates basic input. 4. Backend validates and
normalizes the search query. 5. Backend searches the indexed game
catalog. 6. Backend returns matching results. 7. Frontend displays game
title, App ID, and available metadata. 8. User selects a result. 9.
System opens the selected game's detail page.

**Alternative flows:** - A1: No result is found. The system displays an
empty state. - A2: The game exists externally but is not indexed. The
system explains that analytics are not yet available. - A3: The search
service is unavailable. The system displays a retryable error. - A4: The
input is invalid or too long. The system requests corrected input.

**Postconditions:** - No ingestion job is started by an ordinary public
search. - The user may view the selected indexed game.

## 6.3 UC-002 --- View Game Analytics

**Primary actor:** Guest\
**Goal:** Understand aggregate player feedback for a selected game.

**Preconditions:** - The game is indexed. - At least some analytics are
available.

**Main flow:** 1. User opens a game detail page. 2. Frontend requests
game metadata and analytics. 3. Backend retrieves stored aggregates and
freshness metadata. 4. Backend returns review counts, sentiment
distribution, and available analytical sections. 5. Frontend renders the
dashboard. 6. User inspects charts and explanatory information.

**Alternative flows:** - A1: Analytics are not yet computed. Display
processing status. - A2: No reviews are available. Display a no-data
state. - A3: Some modules are unavailable. Render available modules and
mark unavailable modules explicitly. - A4: Cached data is stale. Display
its last successful update timestamp.

**Postconditions:** - The user receives an analytics view with its data
coverage and freshness disclosed.

## 6.4 UC-003 --- Explore and Filter Reviews

**Primary actor:** Guest\
**Goal:** Inspect individual reviews matching selected criteria.

**Preconditions:** - The selected game has stored reviews. - The review
display is permitted by applicable data policy.

**Main flow:** 1. User opens Review Explorer. 2. System displays a
paginated review list. 3. User selects one or more filters. 4. Frontend
sends filter and pagination parameters. 5. Backend validates parameters
and constructs a bounded query. 6. Backend returns matching reviews and
pagination metadata. 7. Frontend displays results. 8. User may change
filters or open another page.

**Alternative flows:** - A1: No reviews match. Display an empty result
state. - A2: A requested prediction is pending. Display pending
status. - A3: A prediction is unavailable. Do not fabricate a label. -
A4: An unsupported filter is supplied. Return a validation error.

**Postconditions:** - The review list reflects the selected filters. -
Steam recommendation and model sentiment remain separate fields.

## 6.5 UC-004 --- Compare Games

**Primary actor:** Guest\
**Goal:** Compare analytical characteristics of two or more indexed
games.

**Preconditions:** - At least two games are indexed. - Comparable
analytics are available.

**Main flow:** 1. User opens Comparison Lab. 2. User selects two or more
games. 3. User selects comparison dimensions. 4. Frontend submits a
comparison request. 5. Backend validates game IDs and supported
dimensions. 6. Backend retrieves comparable aggregate data. 7. Backend
checks coverage and model compatibility. 8. Backend returns comparison
data and warnings. 9. Frontend renders comparison charts and sample
counts.

**Alternative flows:** - A1: One game is not indexed. Request a
different game. - A2: A metric is unavailable for one game. Mark that
metric unavailable. - A3: Model versions differ. Display a comparability
warning. - A4: Date ranges differ materially. Display the
collection-period difference. - A5: Request exceeds comparison limits.
Return a validation error.

**Postconditions:** - Results include sample sizes and relevant
comparability disclosures.

## 6.6 UC-005 --- Inspect Aspects and Topics

**Primary actor:** Guest\
**Goal:** Understand which game aspects and themes are discussed in
reviews.

**Preconditions:** - Aspect or topic processing has been completed for
the selected game.

**Main flow:** 1. User opens Aspect and Topic Intelligence. 2. System
retrieves aspect and topic aggregates. 3. System retrieves
representative review references where permitted. 4. Frontend displays
frequency and sentiment metrics. 5. User selects an aspect or topic. 6.
System displays associated details and representative reviews.

**Alternative flows:** - A1: Analysis is pending. Display processing
state. - A2: No topic was detected. Display an explicit no-topic or
outlier state. - A3: Model version is unavailable. Display the last
valid version or an unavailable state. - A4: The selected aspect has
insufficient sample size. Display a low-sample warning.

**Postconditions:** - The user can inspect aspect and topic information
with model and sample metadata.

## 6.7 UC-006 --- Read Methodology and Model Details

**Primary actor:** Guest\
**Goal:** Understand how SteamScoop collected and analyzed its data.

**Main flow:** 1. User opens Methodology Center. 2. System displays
source information and collection methodology. 3. User selects a model
or analytical method. 4. System displays model version, supported
languages, evaluation metrics, and limitations. 5. User reviews the
information.

**Postconditions:** - Methodology is accessible without
authentication. - Source-derived data and model-derived results are
clearly distinguished.

## 6.8 UC-007 --- Register and Authenticate

**Primary actor:** Visitor\
**Goal:** Create an account and access workspace functionality.

**Preconditions:** - Registration is enabled. - The visitor has a valid
email address and acceptable credentials.

**Main flow:** 1. Visitor opens registration. 2. Visitor submits
required account information. 3. Backend validates the request. 4.
Backend checks account uniqueness. 5. Backend hashes the password. 6.
Backend creates the account. 7. Verification is performed if configured.
8. User logs in. 9. Backend establishes an authenticated session or
token pair. 10. Frontend displays authenticated navigation.

**Alternative flows:** - A1: Email is already registered. Display a safe
conflict message. - A2: Password fails policy. Request a compliant
password. - A3: Verification fails or expires. Offer a safe retry
process. - A4: Authentication fails. Do not reveal whether a password or
account identifier alone was incorrect.

**Postconditions:** - A valid authenticated session exists. - User
receives only the default role unless additional privileges are
explicitly granted.

## 6.9 UC-008 --- Create Research Project

**Primary actor:** Member\
**Goal:** Organize games and analytical work in a research project.

**Preconditions:** - User is authenticated. - User is within configured
project limits.

**Main flow:** 1. User opens My Workspace. 2. User selects Create
Project. 3. User enters project title and optional description. 4.
Frontend submits the request. 5. Backend validates ownership and project
limits. 6. Backend creates the project. 7. Frontend displays the new
project.

**Alternative flows:** - A1: User is not authenticated. Redirect to
login. - A2: Project limit is reached. Explain the limit. - A3: Input is
invalid. Return field-level validation errors.

**Postconditions:** - The project is associated with its owner. -
Default visibility is private unless explicitly configured otherwise.

## 6.10 UC-009 --- Save an Analysis

**Primary actor:** Member\
**Goal:** Preserve an analysis configuration for later use.

**Preconditions:** - User is authenticated. - The target project exists
and the user has permission.

**Main flow:** 1. User performs an analysis. 2. User selects Save
Analysis. 3. User provides a title and selects a project. 4. Frontend
submits filters, selected games, date range, and analytical dimensions.
5. Backend validates the configuration. 6. Backend stores the analysis
configuration and relevant version metadata. 7. System confirms
successful saving.

**Alternative flows:** - A1: Project is unavailable or unauthorized.
Reject the request. - A2: Filter configuration is invalid. Return
validation details. - A3: Analysis data has changed since the original
view. Record the configuration and snapshot timestamp; do not imply that
a live query is an immutable snapshot.

**Postconditions:** - The analysis configuration is associated with the
selected project. - Snapshot behavior is explicit.

## 6.11 UC-010 --- Export Research Data

**Primary actor:** Researcher\
**Goal:** Export an authorized dataset or analysis result.

**Preconditions:** - User is authenticated and has export permission. -
Requested data is eligible for export under platform policy.

**Main flow:** 1. Researcher selects Export. 2. Researcher chooses
format and permitted fields. 3. Frontend submits export request. 4.
Backend checks role, quotas, data policy, and request size. 5. Backend
creates an export job. 6. Worker generates the export. 7. Worker records
completion or failure. 8. User retrieves the authorized file before
expiry.

**Alternative flows:** - A1: User lacks export permission. Reject the
request. - A2: Request exceeds quota. Explain the applicable limit. -
A3: Requested fields are not eligible for redistribution. Exclude or
reject them with an explanation. - A4: Export worker fails. Preserve
error state and permit safe retry. - A5: File expires. Require a new
export request.

**Postconditions:** - Export job and provenance are recorded. - Only
authorized users can retrieve the generated file.

## 6.12 UC-011 --- Register a Game for Indexing

**Primary actor:** Admin\
**Goal:** Add a game to the SteamScoop indexed catalog.

**Preconditions:** - Administrator is authenticated and authorized. - A
valid Steam App ID is available.

**Main flow:** 1. Administrator opens ingestion administration. 2.
Administrator enters a Steam App ID. 3. Backend validates the
identifier. 4. System checks whether the game already exists. 5. System
retrieves metadata through the configured Steam Store adapter. 6. System
validates and stores available metadata. 7. System marks the game as
registered or metadata-pending. 8. Administrator may request initial
historical collection.

**Alternative flows:** - A1: App ID already exists. Return the existing
game record. - A2: Metadata source is unavailable. Record the failure
and allow retry. - A3: App ID is invalid or not resolvable. Reject or
mark unverified. - A4: Game is not eligible under platform policy. Do
not index it.

**Postconditions:** - Game registration is recorded. - No duplicate game
record is created.

## 6.13 UC-012 --- Run Historical Collection

**Primary actor:** Admin/System\
**Goal:** Collect an initial temporal sample of reviews for an indexed
game.

**Preconditions:** - Game is registered. - No conflicting active
historical job exists. - Steam API integration is operational.

**Main flow:** 1. Admin or approved workflow requests historical
collection. 2. Job service creates an ingestion job. 3. Celery receives
the task. 4. Worker loads or creates bucket checkpoints. 5. Worker
requests a page from Steam. 6. Worker validates and maps reviews. 7.
Worker upserts the review batch. 8. Worker commits the next cursor and
counters in the same transaction. 9. Worker repeats until the bucket
quota or boundary is reached. 10. Worker records bucket outcome. 11.
System completes or marks the overall job partial. 12. Newly inserted or
changed reviews are queued for NLP processing.

**Alternative flows:** - A1: HTTP 429 occurs. Worker applies bounded
backoff and retries. - A2: Worker crashes. Recovery resumes from the
latest committed cursor. - A3: API returns no more reviews. Bucket
completes with the actual count. - A4: API returns malformed data.
Record failure and do not advance the checkpoint for that batch. - A5:
Quota is not reached. Mark actual count and sampling limitation.

**Postconditions:** - Successfully collected reviews are persisted
once. - Checkpoints accurately represent committed work. - The job
outcome is recorded.

## 6.14 UC-013 --- Run Weekly Incremental Collection

**Primary actor:** Scheduler/System\
**Goal:** Collect new and updated reviews for indexed games.

**Preconditions:** - Weekly schedule is enabled. - Game is due for
refresh. - No conflicting active incremental job exists.

**Main flow:** 1. Celery Beat triggers the weekly scheduler. 2.
Scheduler selects due games. 3. Scheduler creates one eligible job per
game. 4. Workers load each game's last successful watermark. 5. Workers
calculate the overlap boundary. 6. Workers request Updated reviews. 7.
Workers upsert records and record content changes. 8. Workers continue
until the watermark boundary or end of results. 9. The system commits
the new watermark after successful completion. 10. Changed review
content is queued for NLP processing. 11. Analytics aggregation is
scheduled after processing.

**Alternative flows:** - A1: No watermark exists. Route the game to
initial collection or a defined bootstrap process. - A2: HTTP 429
occurs. Apply global rate limiting and retry. - A3: One game's job
fails. Other games may continue independently. - A4: A review is updated
but its text is unchanged. Update source metadata without unnecessary
NLP inference. - A5: The job is partial. Do not advance the successful
watermark beyond the fully processed boundary.

**Postconditions:** - New and updated reviews are persisted. - The
watermark reflects only successfully processed coverage. - The next
refresh time is scheduled.

## 6.15 UC-014 --- Recover a Failed Ingestion Job

**Primary actor:** Admin/System\
**Goal:** Resume or retry an interrupted collection.

**Preconditions:** - A job is failed, retrying, or interrupted. - A
valid checkpoint exists where applicable.

**Main flow:** 1. Recovery scheduler or administrator identifies the
job. 2. System inspects the last committed checkpoint. 3. System
verifies that no conflicting active job exists. 4. System creates or
resumes an execution attempt. 5. Worker loads the saved cursor and
collection configuration. 6. Worker resumes collection. 7. System
records the recovery attempt and final result.

**Alternative flows:** - A1: Checkpoint is invalid. Mark the job as
requiring manual intervention. - A2: Source API configuration is
invalid. Do not retry indefinitely. - A3: Job is cancelled. Do not
resume without an explicit new request. - A4: No checkpoint exists.
Restart only if the operation is idempotent and safe.

**Postconditions:** - Recovery history is retained. - Already committed
reviews are not duplicated.

## 6.16 UC-015 --- Process Reviews Using NLP

**Primary actor:** Worker/System\
**Goal:** Generate model predictions for eligible reviews.

**Preconditions:** - Review records exist. - A compatible model version
is available. - Review content is eligible for processing.

**Main flow:** 1. Ingestion or reprocessing creates an NLP task. 2.
Worker loads eligible review records. 3. Worker detects or validates
language. 4. Worker selects a compatible model. 5. Worker executes
sentiment inference. 6. Worker executes configured aspect and topic
processing. 7. Worker stores predictions with model and taxonomy
versions. 8. Worker marks processing status. 9. Aggregation is
scheduled.

**Alternative flows:** - A1: Language is unsupported. Record unsupported
status; do not invent predictions. - A2: Model is unavailable. Keep the
task pending or mark failed. - A3: Inference fails. Record error and
allow bounded retry. - A4: Review content has not changed and the same
model version already has a valid prediction. Skip redundant
inference. - A5: A newer model is activated. Reprocessing occurs through
an explicit model migration or batch job.

**Postconditions:** - Predictions are versioned and traceable. - Failed
or unsupported inference is distinguishable from neutral sentiment.

## 6.17 UC-016 --- Manage Model Versions

**Primary actor:** Admin\
**Goal:** Register, evaluate, and activate model versions.

**Preconditions:** - Administrator has model-management permission. -
Model artifact and evaluation information are available.

**Main flow:** 1. Admin registers model metadata. 2. System validates
required metadata. 3. Admin attaches evaluation results and
supported-language information. 4. System stores model version and
artifact reference. 5. Authorized admin activates the model for a
supported task. 6. New inference jobs use the active compatible model.
7. Existing predictions retain their original model references.

**Alternative flows:** - A1: Evaluation metadata is missing. Model may
be registered as experimental but must not be presented as validated. -
A2: Model artifact is unavailable. Activation is rejected. - A3: Model
is incompatible with a language or task. It cannot be selected for that
task. - A4: Model is deactivated. Existing predictions remain available
with their historical version metadata.

**Postconditions:** - Model history remains traceable. - Model
activation does not silently rewrite historical predictions.

------------------------------------------------------------------------

# 7. Business Rules

Business rules define constraints that apply across multiple system
features.

## 7.1 Public Access Rules

-   **BR-001:** Core public analytics MUST be accessible without login.
-   **BR-002:** Authentication MUST be required for persistent personal
    workspaces.
-   **BR-003:** Public search MUST NOT trigger unrestricted ingestion.
-   **BR-004:** Public users MUST NOT access administrative or private
    research resources.
-   **BR-005:** Public API requests MUST be subject to configurable rate
    and resource limits.

## 7.2 Game Identity Rules

-   **BR-006:** Steam App ID MUST uniquely identify a game record.
-   **BR-007:** A game MUST NOT have duplicate catalog records for the
    same Steam App ID.
-   **BR-008:** Reviews MUST be associated with a valid game record.
-   **BR-009:** Metadata refresh MUST preserve the game's identity and
    review relationships.

## 7.3 Review Identity and Deduplication Rules

-   **BR-010:** A Steam review MUST be uniquely identified by
    `(game_id, steam_review_id)`.
-   **BR-011:** Repeated retrieval of the same review MUST NOT create
    duplicate records.
-   **BR-012:** A newer source update MAY replace older stored review
    content.
-   **BR-013:** A stale source response MUST NOT overwrite a newer
    stored review version.
-   **BR-014:** Source collection timestamps MUST be distinct from Steam
    review creation and update timestamps.

## 7.4 Collection Rules

-   **BR-015:** Initial historical sampling MUST target no more than
    5,000 reviews per game under the default profile.
-   **BR-016:** The initial sampling target MUST NOT be interpreted as a
    permanent storage cap.
-   **BR-017:** The default historical sampling profile SHOULD use 10
    temporal buckets with up to 500 reviews per bucket.
-   **BR-018:** Actual collected counts MUST be stored even when a
    bucket cannot reach its quota.
-   **BR-019:** The default page size MUST NOT exceed 100 reviews.
-   **BR-020:** Historical traversal SHOULD use the Recent filter.
-   **BR-021:** Incremental synchronization SHOULD use the Updated
    filter.
-   **BR-022:** The default incremental refresh cadence MUST be weekly.
-   **BR-023:** The default incremental overlap window SHOULD be 14 days
    and MUST be configurable.
-   **BR-024:** The incremental watermark MUST advance only after the
    corresponding collection range is successfully committed.
-   **BR-025:** The system MUST use the API-returned cursor and MUST NOT
    construct or guess cursor values.
-   **BR-026:** The system MUST apply bounded retry and backoff for
    transient failures.
-   **BR-027:** HTTP 429 MUST trigger rate-limit handling.
-   **BR-028:** The system MUST NOT assume an undocumented universal
    Steam request quota.
-   **BR-029:** Conflicting active jobs for the same game and scope MUST
    be prevented unless explicit concurrency controls exist.
-   **BR-030:** Failed or partial jobs MUST retain their collection
    configuration and checkpoint history.

## 7.5 Data Processing Rules

-   **BR-031:** Steam recommendation status and NLP sentiment MUST be
    stored and displayed as separate concepts.
-   **BR-032:** A review MUST NOT receive a prediction from a model that
    does not support its language or task.
-   **BR-033:** A prediction MUST reference its model version.
-   **BR-034:** Aspect predictions MUST reference an aspect taxonomy
    version.
-   **BR-035:** Topic assignments MUST reference a topic model version.
-   **BR-036:** A review's NLP output SHOULD be recomputed when
    model-relevant text or language changes.
-   **BR-037:** Changes to vote counts alone SHOULD NOT trigger NLP
    inference.
-   **BR-038:** Failed inference MUST NOT be represented as neutral
    sentiment.
-   **BR-039:** Unsupported language MUST be distinguishable from
    inference failure.
-   **BR-040:** Analytics MUST be computed from a clearly defined set of
    eligible reviews and prediction versions.

## 7.6 Comparison Rules

-   **BR-041:** A comparison MUST include at least two valid games.
-   **BR-042:** A comparison MUST display review sample counts.
-   **BR-043:** Comparisons MUST disclose material differences in data
    coverage.
-   **BR-044:** Metrics generated by incompatible model versions MUST be
    marked or warned.
-   **BR-045:** Missing metrics MUST be represented as unavailable, not
    zero.
-   **BR-046:** A difference in sentiment MUST NOT be described as proof
    of objective game quality.

## 7.7 Account and Workspace Rules

-   **BR-047:** New accounts MUST receive only the default member role.
-   **BR-048:** Researcher and administrator privileges MUST require
    explicit authorization.
-   **BR-049:** Private projects MUST be accessible only to their owner
    and explicitly authorized collaborators.
-   **BR-050:** Project visibility MUST be checked on every protected
    backend request.
-   **BR-051:** Public sharing MUST be opt-in and read-only by default.
-   **BR-052:** Users MUST NOT modify another user's private project
    without permission.

## 7.8 Export Rules

-   **BR-053:** Export access MUST be role- and policy-controlled.
-   **BR-054:** Export requests MUST be subject to quotas and size
    limits.
-   **BR-055:** Large exports MUST execute asynchronously.
-   **BR-056:** Export files MUST have a configured expiry or retention
    period.
-   **BR-057:** Export metadata MUST include relevant source,
    collection, and model provenance.
-   **BR-058:** Review text MUST NOT be redistributed unless permitted
    by applicable terms and policy.
-   **BR-059:** Export links MUST NOT bypass ownership or authorization
    checks.

## 7.9 Privacy and Governance Rules

-   **BR-060:** SteamID MUST NOT be retained for standard SteamScoop
    review analytics.
-   **BR-061:** Unnecessary author and hardware fields MUST be
    discarded.
-   **BR-062:** SteamScoop MUST provide appropriate source attribution.
-   **BR-063:** SteamScoop MUST NOT imply that it is operated, endorsed,
    or certified by Valve unless an explicit agreement establishes that
    relationship.
-   **BR-064:** Data retention and deletion MUST follow the published
    platform policy.
-   **BR-065:** Applicable Steam terms MUST be reviewed before public
    redistribution or commercial use.

## 7.10 Analytical Integrity Rules

-   **BR-066:** Steam reviews MUST NOT be described as representative of
    all players.
-   **BR-067:** Sentiment MUST NOT be described as objective game
    quality.
-   **BR-068:** Topic labels MUST be described as analytical
    interpretations.
-   **BR-069:** Percentages SHOULD be displayed with sample counts.
-   **BR-070:** Sampling and language limitations MUST be disclosed.
-   **BR-071:** Correlation between updates and sentiment changes MUST
    NOT be presented as causation without an appropriate causal research
    design.

------------------------------------------------------------------------

# 8. System Behavior and State Models

## 8.1 General Request Lifecycle

For ordinary API requests:

1.  Client sends an HTTP request.
2.  API gateway or application middleware applies request limits and
    correlation identifiers.
3.  Authentication is evaluated if the route is protected.
4.  Authorization is evaluated for the requested resource.
5.  Input is validated.
6.  Application service applies business rules.
7.  Data is retrieved or modified through repositories.
8.  Transaction is committed if applicable.
9.  API returns a structured response.
10. Errors are mapped to stable error codes without exposing secrets or
    internal stack traces.

## 8.2 Public Analytics Behavior

-   Public analytics requests SHOULD read stored or precomputed data.
-   The system SHOULD use cache for frequently requested aggregate
    results.
-   Cache entries MUST be invalidated or versioned when relevant
    analytics are refreshed.
-   If a dataset is stale, the response MUST include its last successful
    update time where available.
-   A public request MUST NOT wait for a full historical ingestion or
    large NLP job.
-   If data is unavailable, the system MUST return an explicit state.

## 8.3 Ingestion Job Lifecycle

### States

  -----------------------------------------------------------------------
  State                               Meaning
  ----------------------------------- -----------------------------------
  queued                              Job has been accepted but has not
                                      started

  running                             Worker is executing the job

  retrying                            A transient failure occurred and a
                                      retry is scheduled

  completed                           Required work completed
                                      successfully

  partial                             Some work completed, but the
                                      configured target or scope was not
                                      fully achieved

  failed                              Job cannot proceed without
                                      intervention or retry policy is
                                      exhausted

  cancelled                           Job was explicitly cancelled
  -----------------------------------------------------------------------

### State behavior

-   A queued job becomes running when claimed by a worker.
-   A running job may become retrying after a transient failure.
-   A retrying job returns to running when a retry begins.
-   A running job becomes completed only after all required work is
    committed.
-   A running job becomes partial when a defined portion completed but
    the job cannot fulfill its full scope.
-   A job becomes failed when a permanent error occurs or retry policy
    is exhausted.
-   A job becomes cancelled only after safe cancellation handling.
-   Terminal jobs MUST NOT silently return to running. A new attempt or
    explicit retry event MUST be recorded.

## 8.4 Checkpoint and Transaction Behavior

For every fetched page:

1.  Request the page using the current committed cursor.
2.  Validate response structure and review records.
3.  Map records into internal review schema.
4.  Begin database transaction.
5.  Upsert all valid records in the page.
6.  Record batch counts and status.
7.  Persist the next cursor and checkpoint counters.
8.  Commit the transaction.
9.  Only after commit may the worker request the next page.

If the transaction fails: - Review upserts and checkpoint advancement
MUST roll back together. - The worker MUST NOT proceed using an
uncommitted cursor. - Recovery MUST resume from the last committed
checkpoint.

## 8.5 Review Update Behavior

When an incoming review matches an existing
`(game_id, steam_review_id)`:

1.  Compare source update timestamps.
2.  Ignore a stale source version.
3.  If the source version is newer, compare relevant content fields.
4.  Update source fields and collection timestamp.
5.  Determine whether model-relevant content changed.
6.  If text or language changed, enqueue applicable NLP reprocessing.
7.  If only vote counts or other non-model fields changed, update those
    fields without unnecessary NLP inference.
8.  Preserve historical predictions and their model versions.

## 8.6 Watermark Behavior

-   A watermark represents successfully processed coverage, not merely
    the newest timestamp observed in a response.
-   The overlap window allows recently updated reviews to be retrieved
    again.
-   Duplicate retrieval is safe because review upsert is idempotent.
-   The watermark MUST NOT advance beyond a failed or uncommitted page.
-   If a job is partial, the system MUST retain the last safe watermark
    and record the incomplete range.
-   Watermark timestamps MUST use a consistent timezone representation,
    preferably UTC.

## 8.7 NLP Processing Behavior

-   Ingestion and NLP processing are independent pipelines.
-   A successfully collected review may remain pending NLP processing.
-   Each NLP task identifies the review, task type, and target model
    version.
-   Workers MUST verify that the prediction does not already exist for
    the same review and model version unless reprocessing is explicitly
    requested.
-   Unsupported languages MUST receive an explicit unsupported status.
-   Model failures MUST be recorded separately from valid neutral
    predictions.
-   A model activation MUST NOT silently overwrite old predictions.
-   New model versions SHOULD be evaluated before being used as the
    default production model.

## 8.8 Analytics Aggregation Behavior

-   Aggregates MUST use a defined eligible review population.
-   The system MUST define whether reviews without predictions are
    excluded from sentiment denominators.
-   Review counts and sentiment counts MUST be consistent for a given
    aggregation version.
-   Aggregates SHOULD record computation time and relevant model
    version.
-   When new predictions are committed, affected aggregates MUST be
    scheduled for refresh.
-   If aggregation fails, the last valid aggregate may remain available
    but MUST retain its previous freshness timestamp.
-   Missing values MUST NOT be converted to zero unless zero is the
    actual measured value.

## 8.9 Comparison Behavior

-   The backend validates all requested games and dimensions.
-   The backend retrieves compatible metrics.
-   The backend calculates or retrieves comparison values.
-   The backend includes sample counts and coverage metadata.
-   Incompatible or unavailable metrics are marked.
-   The frontend renders warnings next to affected comparisons.
-   The system MUST NOT conceal important differences in collection
    coverage.

## 8.10 Export Behavior

-   Export requests are validated before job creation.
-   Export job records include requester, scope, format, requested
    fields, and policy decision.
-   Export workers read only authorized and eligible data.
-   Export files are stored in a controlled location.
-   Downloads require an authorization check or a suitably protected
    expiring link.
-   Expired exports are deleted or made inaccessible according to
    retention policy.
-   Export failure MUST NOT alter source review or analytical records.

## 8.11 Scheduled Behavior

Default schedule:

-   Weekly incremental collection: Monday at 09:00 WIB, represented as
    02:00 UTC, subject to deployment configuration.
-   Failed-job recovery scan: every 30 minutes.
-   Analytics aggregation: after relevant NLP processing, with optional
    periodic reconciliation.
-   Metadata refresh: configurable and independent from review
    collection.

The scheduler MUST avoid creating duplicate active jobs. Missed
schedules SHOULD be handled through a due-job query rather than assuming
the scheduler ran at the exact scheduled instant.

## 8.12 Rate-Limit Behavior

-   All Steam requests SHOULD pass through a shared rate limiter.
-   HTTP 429 MUST trigger a pause or backoff.
-   If a valid `Retry-After` header is provided, the client SHOULD
    respect it.
-   Retries MUST include jitter where appropriate to avoid synchronized
    worker retries.
-   Rate-limit events MUST be logged.
-   The system MUST NOT respond to rate limits by spawning additional
    workers or increasing request concurrency.

## 8.13 Error Handling Behavior

Errors should be categorized as:

  -----------------------------------------------------------------------
  Category                Examples                Expected behavior
  ----------------------- ----------------------- -----------------------
  Validation              Invalid App ID,         Reject request; no
                          malformed filters       retry

  Authorization           Guest requests admin    Return access denied
                          route                   

  Not found               Unknown indexed game    Return not found

  Rate limit              HTTP 429                Backoff and retry
                                                  within limits

  Transient external      HTTP 5xx, timeout       Bounded retry

  Permanent external      Invalid request,        Fail and require
                          revoked access          intervention

  Data validation         Malformed review record Quarantine or skip
                                                  according to policy; do
                                                  not advance unsafe
                                                  checkpoint

  Database                Transaction failure     Roll back and retry
                                                  safely where
                                                  appropriate

  Model                   Inference exception     Record failed
                                                  processing state

  Internal                Unexpected application  Log correlation ID and
                          error                   return generic error
  -----------------------------------------------------------------------

Public responses MUST NOT expose stack traces, credentials, internal
hostnames, or sensitive database details.

------------------------------------------------------------------------

# 9. Data Requirements

## 9.1 Core Entities

### Game

Minimum fields:

-   `id`
-   `steam_app_id`
-   `name`
-   `developer`
-   `publisher`
-   `header_image`
-   `release_date`
-   `created_at`
-   `updated_at`
-   `last_metadata_refresh_at`
-   `next_refresh_at`
-   `is_indexed`

Constraints: - `steam_app_id` MUST be unique. - Required identifiers
MUST be non-null.

### Review

Minimum fields:

-   `id`
-   `game_id`
-   `steam_review_id`
-   `review_text`
-   `language`
-   `recommended`
-   `playtime_forever`
-   `playtime_at_review`
-   `votes_up`
-   `votes_funny`
-   `steam_purchase`
-   `received_for_free`
-   `review_created_at`
-   `review_updated_at`
-   `first_collected_at`
-   `last_collected_at`
-   `source_payload_hash`

Constraints: - `(game_id, steam_review_id)` MUST be unique. - `game_id`
MUST reference an existing game. - Steam author identifiers SHOULD NOT
be stored.

### Model

Minimum fields:

-   `id`
-   `model_name`
-   `model_version`
-   `task`
-   `supported_languages`
-   `artifact_reference`
-   `status`
-   `created_at`

### Sentiment Prediction

Minimum fields:

-   `id`
-   `review_id`
-   `model_id`
-   `sentiment`
-   `confidence`
-   `prediction_status`
-   `predicted_at`

Constraints: - A review/model/task combination MUST have a defined
uniqueness policy. - Historical model predictions MUST remain traceable.

### Ingestion Job

Minimum fields:

-   `id`
-   `game_id`
-   `job_type`
-   `status`
-   `target_reviews`
-   `collected_reviews`
-   `started_at`
-   `completed_at`
-   `error_message`
-   `created_at`

### Collection Checkpoint

Minimum fields:

-   `id`
-   `job_id`
-   `game_id`
-   `collection_type`
-   `window_start`
-   `window_end`
-   `cursor`
-   `last_seen_created_at`
-   `last_seen_updated_at`
-   `pages_completed`
-   `reviews_collected`
-   `completed`
-   `updated_at`

### Research Project

Minimum fields:

-   `id`
-   `owner_id`
-   `title`
-   `description`
-   `visibility`
-   `status`
-   `created_at`
-   `updated_at`

## 9.2 Data Provenance

The system SHOULD retain sufficient metadata to identify:

-   Source service.
-   Steam App ID.
-   Collection job.
-   Collection timestamp.
-   Collection type.
-   Sampling window.
-   Collection filter configuration.
-   Model name and version.
-   Prediction timestamp.
-   Aggregation version or computation timestamp.

## 9.3 Data Retention

Retention periods MUST be configurable and documented before public
launch.

The system SHOULD distinguish: - Account data. - Review content. -
Derived predictions. - Operational logs. - Export files. - Model
artifacts. - Research snapshots.

Deleting or expiring one category MUST NOT unintentionally delete
unrelated records.

Any retention of review text and any redistribution must be reviewed
against applicable Steam terms and platform policy.

------------------------------------------------------------------------

# 10. API Error and Response Conventions

## 10.1 General Error Structure

The API SHOULD use a consistent structure:

``` json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested game is not indexed.",
    "request_id": "correlation-id"
  }
}
```

## 10.2 Expected HTTP Status Codes

  Status        Meaning
  ------------- ------------------------------------------
  200           Successful read or operation
  201           Resource created
  202           Asynchronous operation accepted
  400           Invalid request
  401           Authentication required or invalid
  403           Authenticated but unauthorized
  404           Resource not found
  409           Conflict or duplicate active operation
  422           Semantic validation failure
  429           Application rate limit exceeded
  500           Unexpected internal error
  502/503/504   Upstream or service availability failure

## 10.3 Pagination

Paginated review responses SHOULD include: - Items. - Page size. -
Next-page token or cursor appropriate to the internal API. - Whether
more results are available. - Total count only when it can be provided
accurately and efficiently.

Internal public API pagination SHOULD be decoupled from the Steam source
cursor. The Steam cursor is an ingestion concern and should not be
exposed as a stable public pagination contract unless explicitly
designed and secured.

------------------------------------------------------------------------

# 11. Testing and Verification Requirements

## 11.1 Unit Testing

Unit tests MUST cover: - Request validation. - Steam response mapping. -
Review hashing. - Upsert decisions. - Watermark calculation. - Sampling
bucket calculation. - Job state transitions. - Authorization rules. -
Analytics calculations. - Model routing by language and task.

## 11.2 Integration Testing

Integration tests SHOULD cover: - Steam API client with mocked
responses. - Database transactions. - Review deduplication. - Atomic
checkpoint persistence. - Celery task dispatch. - Redis broker
behavior. - NLP task orchestration. - Export authorization and expiry.

## 11.3 Failure and Recovery Testing

Tests MUST cover: - HTTP 429. - HTTP 5xx. - Network timeout. - Malformed
API response. - Worker termination during collection. - Database failure
during batch persistence. - Retry exhaustion. - Duplicate task
delivery. - Concurrent job creation. - Invalid or repeated cursor. -
Partial historical bucket completion. - Failed NLP inference.

## 11.4 End-to-End Testing

End-to-end tests SHOULD cover: - Guest game search. - Guest game
analytics. - Review filtering. - Game comparison. - Account registration
and login. - Workspace creation. - Analysis saving. - Export request and
download. - Admin game registration. - Admin ingestion monitoring.

## 11.5 Acceptance Verification

A requirement is accepted only when: 1. Its implementation is available
in the intended environment. 2. Its expected behavior is documented. 3.
Its relevant test cases pass. 4. Authorization and data-policy
constraints are verified where applicable. 5. Failure states are tested
for critical asynchronous workflows.

------------------------------------------------------------------------

# 12. MVP Release Boundary

## 12.1 Mandatory MVP Capabilities

The initial public MVP MUST include:

-   Public landing page.
-   Game search for indexed games.
-   Game detail page.
-   Steam metadata integration.
-   Steam review ingestion.
-   Historical sampling with configured limits.
-   Weekly incremental collection.
-   Cursor checkpointing and recovery.
-   Review deduplication and upsert.
-   Sentiment analysis.
-   Review Explorer.
-   Basic aggregate dashboard.
-   Dataset freshness information.
-   Methodology and model transparency.
-   Administrative ingestion monitoring.
-   Basic security and rate limiting.

## 12.2 Deferred Capabilities

The following MAY be deferred to later releases:

-   Advanced ABSA.
-   Topic modeling.
-   Multilingual inference beyond validated languages.
-   Advanced temporal analytics.
-   Game Comparison Lab.
-   User registration and workspaces.
-   Collaboration.
-   Shareable research links.
-   Large-scale dataset export.
-   Community-generated content.

The exact release boundary must be approved by the product owner before
implementation planning.

------------------------------------------------------------------------

# 13. Traceability Matrix

  -----------------------------------------------------------------------
  Product objective                   Related requirements
  ----------------------------------- -----------------------------------
  Public accessibility                FR-PUB-001 to FR-PUB-009

  Game discovery                      FR-GAME-001 to FR-GAME-008

  Reliable data ingestion             FR-ING-001 to FR-ING-018;
                                      FR-JOB-001 to FR-JOB-012

  Review intelligence                 FR-REV-001 to FR-REV-010

  Sentiment analytics                 FR-SENT-001 to FR-SENT-009

  Aspect intelligence                 FR-ABSA-001 to FR-ABSA-008

  Topic intelligence                  FR-TOPIC-001 to FR-TOPIC-008

  Temporal analytics                  FR-TIME-001 to FR-TIME-006

  Game comparison                     FR-COMP-001 to FR-COMP-009

  Research transparency               FR-METH-001 to FR-METH-010;
                                      NFR-RESEARCH-001 to
                                      NFR-RESEARCH-008

  Research workflows                  FR-AUTH-001 to FR-AUTH-009;
                                      FR-WS-001 to FR-WS-010

  Controlled data export              FR-EXP-001 to FR-EXP-008

  Platform operations                 FR-ADM-001 to FR-ADM-008

  Security and privacy                NFR-SEC-001 to NFR-SEC-012;
                                      NFR-PRIV-001 to NFR-PRIV-007
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 14. Open Decisions and Items Requiring Validation

The following decisions must be finalized before or during
implementation:

1.  **Steam content retention:** Confirm applicable Steam terms for
    storing and displaying review text.
2.  **Redistribution policy:** Determine which fields may be included in
    CSV/JSON exports.
3.  **Historical date range:** Define the default start date and
    treatment of games with limited review history.
4.  **Sampling reallocation:** Decide whether unused quota from sparse
    time buckets is redistributed and how.
5.  **Neutral sentiment:** Define annotation policy and whether the
    selected model reliably supports a neutral class.
6.  **Aspect taxonomy:** Finalize labels, definitions, and annotation
    guidelines.
7.  **Language support:** Publish only languages with validated model
    performance.
8.  **Model evaluation targets:** Confirm targets after establishing an
    annotated baseline dataset.
9.  **Researcher role assignment:** Define who can grant researcher
    privileges.
10. **Export quotas:** Set role-based row, file-size, and frequency
    limits.
11. **Workspace collaboration:** Decide whether collaboration belongs in
    the first research release or a later release.
12. **Availability target:** Validate the proposed 99% monthly target
    against hosting budget and operational capacity.
13. **Performance baseline:** Define representative query, data volume,
    concurrency, and measurement environment for the 500 ms target.
14. **Retention periods:** Set approved retention periods for review
    content, logs, exports, and account data.
15. **Reconciliation cadence:** Define how often SteamScoop revisits
    older reviews that may have been missed by incremental
    synchronization.

Open decisions MUST be recorded and resolved by the responsible product
or engineering owner. They MUST NOT be silently converted into
assumptions in production behavior.

------------------------------------------------------------------------

# 15. Final System Definition

SteamScoop is a public Game Intelligence and Research Web Application
that collects, processes, and analyzes Steam user reviews to provide
structured insights into player sentiment, game aspects, recurring
topics, and temporal patterns.

The system combines public analytical access with optional authenticated
research workflows.

Its core engineering principles are:

1.  Public-first access.
2.  Controlled and recoverable data ingestion.
3.  Idempotent data persistence.
4.  Asynchronous NLP and analytics processing.
5.  Versioned and traceable model predictions.
6.  Transparent sampling and data provenance.
7.  Secure, role-based access to private research features.
8.  Responsible interpretation of user-generated review data.

**Product name:** SteamScoop\
**Product category:** Public Game Intelligence & Research Platform\
**Tagline:** Understand Games Through Data.

------------------------------------------------------------------------

## References

-   Steam User Reviews API:
    https://partner.steamgames.com/doc/webapi/IUserReviewsService
-   Steam Web API Overview: https://partner.steamgames.com/doc/webapi
-   FastAPI Documentation: https://fastapi.tiangolo.com/
-   Celery Documentation: https://docs.celeryq.dev/en/stable/
-   PostgreSQL Documentation: https://www.postgresql.org/docs/current/
-   React Documentation: https://react.dev/
-   scikit-learn Documentation: https://scikit-learn.org/stable/
-   Hugging Face Documentation: https://huggingface.co/docs

**End of Document**
