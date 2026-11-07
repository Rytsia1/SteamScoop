# SteamScoop Testing Strategy

**Document:** TESTING_STRATEGY.md\
**Version:** 1.0\
**Status:** Baseline engineering standard\
**Product:** SteamScoop --- Understand Games Through Data

------------------------------------------------------------------------

## 1. Purpose

This document defines the testing strategy for SteamScoop. It
establishes the test levels, responsibilities, environments, quality
gates, test data practices, and release acceptance criteria required to
verify that the platform behaves correctly and that its analytics are
reliable enough for research and public use.

The strategy covers:

1.  Unit testing
2.  Integration testing
3.  API testing
4.  End-to-end (E2E) testing
5.  Machine-learning (ML) evaluation testing
6.  Acceptance testing

It applies to the React + TypeScript frontend, FastAPI backend,
PostgreSQL database, Redis/Celery background-processing system, Steam
integration adapter, and ML/analytics pipelines.

This document complements the System Design, Database Design, API
Specification, ML Specification, and Coding Standards. If an
implementation detail differs from this strategy, update the relevant
documentation and tests together.

## 2. Testing Principles

SteamScoop testing follows these principles:

-   **Risk-based:** prioritize data integrity, ingestion correctness,
    authorization, analytics correctness, and ML validity.
-   **Deterministic where possible:** automated tests must not depend on
    live Steam availability, current public data, or nondeterministic
    model output.
-   **Test at the lowest effective level:** use unit tests for isolated
    logic and higher-level tests for component interactions and user
    workflows.
-   **Reproducible:** record test data versions, model versions,
    configuration, and random seeds where applicable.
-   **Fail safely:** partial ingestion, worker retries, and model
    failures must not silently corrupt published analytics.
-   **Privacy-aware:** fixtures must not contain unnecessary Steam
    account identifiers or personal data.
-   **Observable:** failures should identify the relevant test,
    request/job identifier, model version, and diagnostic context
    without leaking secrets.
-   **Contract-driven:** API schemas, database constraints, and external
    integration assumptions must be verified explicitly.
-   **No false confidence:** mocks are appropriate for isolated
    behavior, but critical database, queue, and API behavior must also
    be exercised against real test infrastructure.

## 3. Scope and Quality Objectives

### 3.1 In scope

  -----------------------------------------------------------------------
  Area                                Main verification concerns
  ----------------------------------- -----------------------------------
  Frontend                            Rendering, interaction, routing,
                                      state, accessibility, error and
                                      loading states

  Backend domain logic                Business rules, validation,
                                      permissions, calculations

  PostgreSQL                          Constraints, transactions,
                                      migrations, query behavior

  Steam adapter                       Request construction, pagination,
                                      rate-limit handling, response
                                      normalization

  Ingestion workers                   Idempotency, checkpoints, retries,
                                      recovery, watermark safety

  ML pipeline                         Data preparation, model quality,
                                      versioning, prediction persistence

  Analytics                           Aggregation correctness, filter
                                      consistency, model-version
                                      attribution

  API                                 Contracts, status codes,
                                      validation, authorization,
                                      pagination, rate limits

  User workflows                      Game discovery, analysis
                                      exploration, comparison, research
                                      workspace, export

  Operations                          Health checks, scheduled jobs,
                                      failure recovery, observability
  -----------------------------------------------------------------------

### 3.2 Quality objectives

The following are initial project targets. They should be calibrated
against the MVP dataset and hosting environment rather than treated as
claims about current performance.

  -----------------------------------------------------------------------
  Quality attribute                   Initial target
  ----------------------------------- -----------------------------------
  Critical business-rule coverage     100% of identified critical rules
                                      have automated tests

  Backend unit-test coverage          At least 80% line coverage for core
                                      domain and service modules

  Frontend unit/component coverage    At least 70% for critical UI and
                                      state logic

  API contract coverage               100% of documented public and
                                      protected endpoint operations have
                                      contract tests

  Critical E2E workflows              100% of release-critical workflows
                                      pass

  Data integrity                      No duplicate logical reviews; no
                                      checkpoint advancement before
                                      durable commit

  ML release gate                     Every promoted model passes the
                                      applicable evaluation thresholds in
                                      the ML Specification

  Security                            No known unresolved critical or
                                      high-severity release-blocking
                                      findings

  Reproducibility                     Every published ML result is
                                      attributable to a dataset snapshot
                                      and model version
  -----------------------------------------------------------------------

Coverage percentages are diagnostic indicators, not substitutes for
meaningful assertions. A test suite can have high line coverage while
failing to verify important outcomes.

## 4. Test Levels and Responsibilities

  -----------------------------------------------------------------------
  Test level        Primary question  Typical owner     Execution
  ----------------- ----------------- ----------------- -----------------
  Unit              Does an isolated  Feature developer Every pull
                    function or                         request
                    component behave                    
                    correctly?                          

  Integration       Do collaborating  Feature developer Every pull
                    modules and       / backend         request and
                    infrastructure    engineer          before release
                    work together?                      

  API               Does each         Backend engineer  Every pull
                    endpoint honor                      request
                    its documented                      
                    contract and                        
                    access policy?                      

  E2E               Can a user        Team / QA         Pull requests for
                    complete an                         smoke paths; full
                    important                           suite before
                    workflow through                    release
                    the application?                    

  ML evaluation     Is a model        ML owner /        Dataset or model
                    sufficiently      researcher        changes; before
                    accurate, stable,                   promotion
                    and suitable for                    
                    its intended                        
                    task?                               

  Acceptance        Does the          Product owner and MVP milestones
                    delivered product representative    and release
                    satisfy agreed    users             candidates
                    user and business                   
                    criteria?                           
  -----------------------------------------------------------------------

These levels overlap intentionally. For example, an API test may use a
real database and therefore also verify integration behavior. Test
classification should describe the principal purpose, not prevent useful
layered assertions.

## 5. Test Environments and Tooling

### 5.1 Environments

**Local development** - Developers run focused tests while implementing
features. - Docker Compose provides PostgreSQL and Redis where
required. - External Steam calls are replaced with deterministic
fixtures by default.

**Continuous integration** - Runs linting, type checks, unit tests,
selected integration tests, API tests, and frontend build checks. - Uses
isolated test databases and service containers. - Must not use
production credentials or production user data.

**Staging** - Mirrors the intended deployment topology as closely as
practical. - Uses synthetic or approved sanitized datasets. - Used for
full E2E, migration rehearsal, acceptance testing, and operational
checks.

**Production** - No destructive test suites. - Only safe smoke checks,
health checks, and monitored synthetic checks using dedicated test
resources are permitted.

### 5.2 Recommended tools

  -----------------------------------------------------------------------
  Concern                             Recommended tool
  ----------------------------------- -----------------------------------
  Python unit/integration tests       `pytest`

  Python mocks and fixtures           `pytest-mock`, `unittest.mock`

  Coverage                            `coverage.py` / `pytest-cov`

  HTTP/API tests                      FastAPI `TestClient` or HTTPX

  Database tests                      PostgreSQL test service, SQLAlchemy

  Frontend unit/component tests       Vitest, React Testing Library

  Browser E2E                         Playwright

  ML metrics                          scikit-learn metrics, task-specific
                                      evaluation scripts

  ML experiment tracking              MLflow

  Static checks                       Ruff, mypy, ESLint, TypeScript

  Dependency/security checks          Dependency audit and supported
                                      vulnerability scanners

  CI                                  GitHub Actions
  -----------------------------------------------------------------------

Use the tools already established by the repository. Introducing a new
testing dependency should have a clear benefit and be documented.

### 5.3 Suggested repository layout

``` text
apps/
  api/
    tests/
      unit/
      integration/
      api/
      fixtures/
  web/
    src/
      ...
    tests/
      unit/
      components/
    e2e/
ml/
  tests/
    unit/
    integration/
    evaluation/
  datasets/
    test-fixtures/
infra/
  test/
docs/
  TESTING_STRATEGY.md
```

Keep small, synthetic fixtures in version control. Large datasets and
model artifacts should be stored in approved artifact storage, not
committed to Git.

## 6. Unit Testing

### 6.1 Objective

Verify individual functions, classes, React components, hooks, and
domain services in isolation. Unit tests should be fast, deterministic,
and focused on one behavior or rule.

### 6.2 Backend unit tests

Test at least:

-   Input validation and normalization.
-   Business rules and domain invariants.
-   Review deduplication key construction.
-   Cursor and checkpoint state transitions.
-   Watermark calculations.
-   Retry classification and backoff policy.
-   Sentiment label normalization and confidence handling.
-   Aspect and topic mapping.
-   Analytics aggregation functions.
-   Filter composition and date-range boundaries.
-   Permission and role decision functions.
-   Export eligibility and quota calculations.

Examples of critical cases:

  -----------------------------------------------------------------------
  Component               Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  Review normalizer       Optional field is       Normalized record uses
                          missing                 an explicit safe
                                                  default or null

  Review normalizer       Review identifier is    Record is rejected or
                          malformed               quarantined according
                                                  to policy

  Deduplication           Same game and review ID Both resolve to one
                          appear twice            logical review record

  Checkpoint service      Page is committed       Checkpoint advances to
                          successfully            the returned cursor

  Checkpoint service      Page transaction fails  Checkpoint remains
                                                  unchanged

  Watermark service       A sync range is         Watermark does not
                          incomplete              advance

  Permission service      Guest requests a        Access is denied
                          protected research      
                          action                  

  Aggregator              No eligible predictions Returns a defined empty
                          exist                   result, not a
                                                  fabricated zero-valued
                                                  distribution

  Date filter             Review timestamp is at  Behavior matches the
                          the exact end boundary  documented
                                                  inclusive/exclusive
                                                  convention
  -----------------------------------------------------------------------

Use parameterized tests for boundaries and combinations. Avoid testing
implementation details that are not part of the component's contract.

### 6.3 Frontend unit and component tests

Test:

-   Component rendering for normal, loading, empty, and error states.
-   Search input behavior and debouncing where implemented.
-   Filter state and reset behavior.
-   Chart data transformation before it reaches ECharts.
-   Tooltip and legend configuration where it affects interpretation.
-   Comparison selection limits and validation.
-   Workspace forms and client-side validation.
-   Accessible names, keyboard interaction, and focus behavior.
-   Query-state behavior for success, failure, and refetch.

Mock network boundaries rather than internal state transformations.
Prefer assertions on visible user behavior.

### 6.4 Unit-test conventions

-   Test names should describe the scenario and expected behavior.
-   Arrange, Act, Assert structure is recommended.
-   Each test should be independently runnable.
-   Do not make live network calls.
-   Freeze time when testing time-sensitive logic.
-   Seed random generators when randomness is part of the test.
-   Avoid excessive mocking that makes the test pass even when the real
    component contract is broken.

### 6.5 Unit-test exit criteria

-   All tests pass locally and in CI.
-   Critical domain rules have direct assertions.
-   No flaky tests are knowingly accepted as passing.
-   Coverage targets are met for the relevant critical modules or
    deviations are documented.

## 7. Integration Testing

### 7.1 Objective

Verify that multiple components collaborate correctly using real
infrastructure boundaries where practical.

### 7.2 Backend and database integration

Use a real PostgreSQL test database for tests involving:

-   SQLAlchemy mappings and repository queries.
-   Foreign keys, unique constraints, check constraints, and indexes.
-   Transaction boundaries and rollback.
-   Alembic migrations from a clean database.
-   Review upsert behavior.
-   Analytics query correctness.
-   Research project membership and access restrictions.
-   Export job persistence and state transitions.

Critical ingestion invariant:

> A review page, its ingestion batch accounting, and its next
> cursor/checkpoint must be committed atomically. If the transaction
> fails, none of those durable state changes may be partially applied.

Test this with transaction failures and simulated interruptions. Verify
persisted state by querying the database after the operation.

### 7.3 Redis and Celery integration

Test:

-   Task publication and consumption.
-   Queue routing for ingestion, NLP, aggregation, exports, and
    maintenance.
-   Retry behavior for transient failures.
-   Non-retry behavior for permanent validation failures.
-   Task idempotency when a message is delivered more than once.
-   Worker restart and recovery behavior.
-   PostgreSQL-backed job state as the durable source of truth.

Do not assume Redis contains the only copy of job state. Tests should
verify that pending or interrupted work can be reconstructed from
persisted database state.

### 7.4 Steam adapter integration

The Steam adapter must be tested against recorded fixtures that
represent the current supported response contract.

Cover:

-   Request parameters and serialization, including the `input_json`
    parameter.
-   Cursor-based pagination.
-   Empty pages and terminal cursor behavior.
-   Malformed or unexpected responses.
-   HTTP 429 and `Retry-After` handling when supplied.
-   Timeouts, connection failures, and server errors.
-   Language, review type, purchase type, and filter configuration.
-   Response normalization into the internal review schema.

Live Steam smoke tests may be run manually or on a controlled schedule,
but must not be a required dependency for ordinary pull-request CI. Live
tests must use a small request budget and must not create uncontrolled
ingestion.

### 7.5 ML and analytics integration

Test the full internal path:

1.  Select eligible reviews.
2.  Prepare and validate text inputs.
3.  Resolve the active model version.
4.  Run inference.
5.  Persist predictions with model and dataset provenance.
6.  Aggregate results using the intended model version.
7.  Serve the resulting analytics through repository/service interfaces.

Verify that a model activation change does not silently mix predictions
from incompatible model versions in one published aggregate.

### 7.6 Integration-test exit criteria

-   Database constraints and migrations pass.
-   Critical transactions preserve invariants under failure.
-   Queue and worker behavior is verified with real test services.
-   Steam adapter fixtures cover normal and failure responses.
-   ML predictions and aggregates retain correct version attribution.

## 8. API Testing

### 8.1 Objective

Verify that the HTTP API follows `API_SPECIFICATION.md`, including
schemas, status codes, authorization, pagination, filtering, errors, and
caching behavior.

### 8.2 Contract tests

For each endpoint operation, verify:

-   HTTP method and route.
-   Request path, query, header, and body validation.
-   Response status code.
-   Response JSON schema and required fields.
-   Correct content type.
-   Stable machine-readable error code.
-   Documented pagination structure.
-   Authentication and authorization requirements.
-   OpenAPI output remains consistent with the implemented contract.

Every documented endpoint must have at least one successful contract
test and relevant negative tests.

### 8.3 Endpoint coverage

Prioritize these endpoint families:

  -----------------------------------------------------------------------
  Endpoint family                     Essential test cases
  ----------------------------------- -----------------------------------
  Public games                        Search, filters, sort, pagination,
                                      unknown game

  Game overview                       Existing game, unindexed game,
                                      missing analytics

  Sentiment/aspects/topics            Filter behavior, empty data,
                                      model-version consistency

  Reviews                             Pagination, date/language filters,
                                      malformed cursor

  Review intelligence                 Existing review, missing
                                      prediction, unknown review

  Comparisons                         Valid game set, duplicate game,
                                      unsupported count, incomplete
                                      analytics

  Methodology                         Version and provenance fields are
                                      returned

  Authentication                      Valid credentials, invalid
                                      credentials, expired session/token

  Research projects                   Owner/member/guest access,
                                      membership changes

  Saved analyses                      Validation, ownership,
                                      reproducibility metadata

  Exports                             Accepted asynchronous request, job
                                      status, quota, unauthorized
                                      download

  Admin                               Role enforcement, invalid job
                                      request, audit event creation
  -----------------------------------------------------------------------

### 8.4 Authentication and authorization tests

Test at minimum:

-   Guest can access only public resources.
-   Member can access only workspaces they own or are authorized to
    access.
-   Researcher-only actions require the explicit researcher permission.
-   Admin endpoints reject non-admin roles.
-   Changing a resource ID cannot expose another user's private
    workspace or export.
-   Revoked membership takes effect according to the documented session
    and authorization policy.

Use a role/endpoint matrix so that access rules are reviewed
systematically.

### 8.5 Pagination and filtering tests

-   First page and subsequent cursor pages.
-   Invalid, malformed, expired, or tampered cursor.
-   Stable ordering when records share a timestamp.
-   No duplicate or skipped records across pages under the documented
    consistency model.
-   Empty result sets.
-   Combined filters.
-   Boundary dates and timezone handling.
-   Maximum page size enforcement.

### 8.6 Error and resilience tests

Verify correct behavior for:

-   `400` invalid request.
-   `401` unauthenticated request.
-   `403` insufficient permission.
-   `404` missing resource.
-   `409` conflicting state.
-   `422` schema or semantic validation error, where used by the API
    contract.
-   `429` rate limit exceeded.
-   `500` unexpected server error without stack trace or secret leakage.
-   `503` temporary service unavailability, where applicable.

Do not force all errors into one status code. The implementation must
follow the API specification's documented mapping.

### 8.7 API test exit criteria

-   All endpoint contract tests pass.
-   Public and protected access rules are verified.
-   Error responses are stable and do not disclose internal
    implementation details.
-   OpenAPI schema and API documentation are reviewed for drift.

## 9. End-to-End Testing

### 9.1 Objective

Verify critical user journeys through the browser and deployed
application stack. E2E tests should be few, stable, and representative
rather than attempting to duplicate every unit test.

Use Playwright with dedicated test accounts and seeded staging data.

### 9.2 Critical user journeys

**Journey A --- Public game discovery** 1. Open SteamScoop. 2. Search
for a seeded game. 3. Open its game overview. 4. Inspect sentiment,
aspects, topics, and review trends. 5. Change a filter. 6. Verify that
the displayed result reflects the selected filter and its loading/error
state is handled.

**Journey B --- Review exploration** 1. Open a game's review explorer.
2. Apply language, date, sentiment, or other supported filters. 3. Move
to another page using the cursor. 4. Open a review detail. 5. Verify
that the review's displayed intelligence identifies the relevant model
version or methodology information.

**Journey C --- Game comparison** 1. Select two or more eligible games
within the supported comparison limit. 2. Open the comparison view. 3.
Verify that metrics use consistent definitions and comparable periods.
4. Verify the empty or unavailable state when one game lacks sufficient
data.

**Journey D --- Research workspace** 1. Sign in as a member. 2. Create a
research project. 3. Add eligible games. 4. Save an analysis with
filters and model/version metadata. 5. Reopen the saved analysis. 6.
Verify that ownership and membership restrictions are enforced.

**Journey E --- Export** 1. Submit an export request within the
permitted quota. 2. Verify the API returns an accepted asynchronous job
response. 3. Observe the job status until completion or a controlled
timeout. 4. Download the resulting file. 5. Verify its schema and that
it contains only the requested, authorized data.

**Journey F --- Access control** 1. Sign in as User A and create a
private project. 2. Attempt to access it as User B. 3. Verify that
access is denied without exposing private project contents. 4. Verify
that an authorized member can access it according to the configured
role.

### 9.3 UI state coverage

For critical pages, include:

-   Initial loading.
-   Successful populated state.
-   Empty state.
-   API error state.
-   Partial analytics availability.
-   Invalid filter or query state.
-   Narrow viewport and responsive layout.
-   Keyboard navigation for core controls.

Charts must be checked for meaningful labels, units, date ranges, and
empty states. E2E tests should not rely only on pixel-perfect
screenshots because chart rendering can vary across browsers and
environments.

### 9.4 E2E stability practices

-   Seed known data before each test suite or use an isolated database
    snapshot.
-   Use stable accessible selectors such as role and label.
-   Avoid arbitrary sleep calls; wait for observable state.
-   Keep tests independent and clean up created resources.
-   Use deterministic test accounts and synthetic data.
-   Capture traces, screenshots, and browser logs on failure.
-   Do not use production accounts or production user data.

### 9.5 E2E exit criteria

-   All critical journeys pass in staging.
-   No critical navigation, authorization, or data-display defects
    remain.
-   Responsive and accessibility smoke checks pass for core flows.
-   Failed tests are investigated rather than blindly retried until
    green.

## 10. ML Evaluation Testing

### 10.1 Objective

Verify that each ML model is fit for its declared task, evaluated
against an appropriate held-out dataset, and safe to promote into
published SteamScoop analytics.

ML evaluation is separate from ordinary software unit testing. A
pipeline can execute without errors while producing poor or misleading
predictions.

### 10.2 Evaluation dataset requirements

Each evaluation run must record:

-   Dataset snapshot identifier and creation date.
-   Data source and collection scope.
-   Language and sampling criteria.
-   Annotation guidelines and label definitions.
-   Annotator process and adjudication method, where applicable.
-   Train, validation, and test split identifiers.
-   Duplicate and near-duplicate handling.
-   Model code/configuration version.
-   Random seed and relevant environment information.

Avoid leakage between training and evaluation data. Where feasible,
split by game or time period in addition to random review-level
splitting to measure generalization beyond reviews that resemble
training examples.

Keep a final test set untouched during model selection. Do not
repeatedly tune against the same final test set.

### 10.3 Sentiment evaluation

Sentiment model outputs must be evaluated against human-labeled examples
using the declared label taxonomy.

Recommended metrics:

-   Macro F1 as a primary metric for class imbalance.
-   Per-class precision, recall, and F1.
-   Confusion matrix.
-   Accuracy as a secondary metric.
-   Calibration metrics or reliability plots when confidence scores are
    exposed or used.
-   Performance by language, game, review length, and relevant time
    slice.

Steam's `voted_up` field represents the reviewer's recommendation, not
the model's sentiment label. It may be used as a comparison signal or
weak label only when the methodology explicitly says so. It must not be
treated as ground-truth sentiment without validation.

**Initial release gate:** macro F1 of at least 0.75 on the approved
in-scope test set, with no in-scope class below 0.60 F1. These are
provisional project thresholds and must be reviewed against annotation
quality, class distribution, and the intended languages before model
promotion. A model that misses a threshold must not be promoted merely
because its accuracy is high.

### 10.4 Aspect-based sentiment analysis (ABSA)

Evaluate aspect extraction and aspect sentiment separately.

**Aspect detection** - Micro and macro precision, recall, and F1. -
Per-aspect support and performance. - Multi-label exact-match score as a
secondary metric, if useful.

**Aspect sentiment** - Per-aspect sentiment macro F1. - Confusion matrix
for sentiment labels within each aspect. - Performance on reviews
mentioning multiple aspects. - Explicit review of ambiguous and implicit
aspect examples.

The aspect taxonomy must be versioned. If taxonomy definitions change,
record the taxonomy version and evaluate the impact on historical
predictions and aggregates.

### 10.5 Topic modeling evaluation

Topic models require both quantitative and human evaluation.

Measure, as appropriate:

-   Topic coherence.
-   Topic diversity.
-   Topic prevalence and coverage.
-   Topic stability across seeds or resampled datasets.
-   Duplicate or highly overlapping topics.
-   Human interpretability and usefulness.

A topic model must not be promoted solely because it has a favorable
coherence score. Reviewers should inspect representative documents, top
terms, topic labels, and low-confidence or outlier assignments.

For BERTopic or other stochastic pipelines, record seeds and relevant
library/configuration versions. If exact determinism is not achievable,
define acceptable variance across repeated runs.

### 10.6 Baseline and candidate comparison

Every proposed model should be compared with a documented baseline.

Examples: - TF-IDF + Logistic Regression. - TF-IDF + Linear SVM. - A
transformer-based classifier, only when measured gains justify its
operational cost.

Comparison must use the same evaluation split and label definitions.
Report quality, inference latency, memory footprint, model size, and
operational complexity. Do not promote a more expensive model for a
negligible or statistically uncertain improvement.

### 10.7 Robustness and failure testing

Evaluate:

-   Very short reviews.
-   Long reviews.
-   Empty or whitespace-only text.
-   URLs, emojis, repeated punctuation, and unusual Unicode.
-   Negation, sarcasm, mixed sentiment, and slang.
-   Code-switching and unsupported languages.
-   Duplicated reviews.
-   Spam-like or off-topic text.
-   Distribution changes across games and time.

Unsupported or low-confidence inputs should follow a documented fallback
policy. The system must not silently present an unreliable prediction as
certain.

### 10.8 Model versioning and promotion

A model version must be immutable after release and linked to:

-   Model artifact and checksum.
-   Source code commit.
-   Training and evaluation dataset snapshots.
-   Preprocessing and taxonomy versions.
-   Hyperparameters and random seeds.
-   Evaluation report.
-   Approval status and activation timestamp.

Promotion sequence:

1.  Train candidate.
2.  Run data validation and evaluation.
3.  Compare with the current production model.
4.  Review per-class, per-language, and per-aspect performance.
5.  Review latency and resource use.
6.  Obtain approval from the designated ML owner.
7.  Activate the model version.
8.  Run post-deployment monitoring.
9.  Roll back if quality or operational safeguards fail.

Do not overwrite historical predictions when a new model is activated.
Store predictions with their model version and ensure each published
aggregate declares the model version used.

### 10.9 Drift monitoring

Monitor signals such as:

-   Input language distribution.
-   Review length and text characteristics.
-   Sentiment distribution.
-   Aspect prevalence.
-   Topic prevalence and outlier rate.
-   Prediction confidence distribution.
-   Performance on a periodically refreshed human-labeled audit sample.

A distribution shift is an investigation trigger, not proof of model
failure. Re-evaluate on a newly labeled sample before retraining or
changing the active model.

### 10.10 ML evaluation exit criteria

A model may be promoted only when:

-   Evaluation data and labels are documented.
-   No known train/test leakage remains.
-   Required metrics meet approved thresholds.
-   Per-class and relevant subgroup results are reviewed.
-   Robustness checks are acceptable.
-   Model artifact and provenance are reproducible.
-   Operational cost is acceptable.
-   Evaluation report and approval are recorded.

## 11. Acceptance Testing

### 11.1 Objective

Confirm that SteamScoop satisfies the agreed product requirements and is
usable for its intended audience. Acceptance testing validates outcomes
from the perspective of students, lecturers, researchers, developers,
and community users---not only implementation correctness.

### 11.2 Participants

Recommended acceptance participants:

-   Product owner or project lead.
-   Developer representative.
-   QA/test representative.
-   Representative student or game-development community users.
-   Research-oriented reviewer, such as a lecturer or researcher, for
    methodology and export workflows.

Participation does not imply institutional endorsement. If the platform
is piloted in a university community, obtain the appropriate permission
before presenting it as an official institutional service.

### 11.3 Acceptance scenarios

  -------------------------------------------------------------------------------
  ID                      Scenario                Acceptance condition
  ----------------------- ----------------------- -------------------------------
  AT-01                   Discover a Steam game   User can find and open an
                                                  indexed game without signing in

  AT-02                   Understand game         User can interpret sentiment
                          sentiment               distribution and its definition

  AT-03                   Explore review trends   User can filter and inspect
                                                  trends with clear date and
                                                  sample context

  AT-04                   Inspect aspects         User can identify common
                                                  aspects and understand how
                                                  aspect sentiment is calculated

  AT-05                   Explore topics          User can inspect topic labels
                                                  and representative review
                                                  examples, where available

  AT-06                   Compare games           User can compare supported
                                                  games using consistent metric
                                                  definitions

  AT-07                   Understand methodology  User can find collection date,
                                                  sampling scope, model version,
                                                  and limitations

  AT-08                   Create a research       Authorized member can create
                          project                 and reopen a workspace

  AT-09                   Save an analysis        Saved analysis preserves its
                                                  filters and relevant provenance

  AT-10                   Export data             Authorized user can request and
                                                  retrieve an allowed export

  AT-11                   Enforce permissions     Guest/member/researcher/admin
                                                  access matches the role policy

  AT-12                   Handle missing data     User sees a clear unavailable
                                                  or insufficient-data state, not
                                                  misleading charts
  -------------------------------------------------------------------------------

### 11.4 Acceptance criteria for analytical trust

The product must communicate that:

-   Steam reviews are not representative of every player.
-   Review recommendation (`voted_up`) is distinct from model-predicted
    sentiment.
-   Collection is sampled and follows the documented policy.
-   Results depend on collection date, filters, language, and model
    version.
-   Aspect and topic outputs are model-derived and may contain errors.
-   Game sentiment is not an objective measure of game quality.
-   Comparisons are meaningful only when the metric definitions and data
    scope are comparable.

### 11.5 Acceptance procedure

1.  Prepare a staging environment with a documented, seeded dataset.
2.  Share the test scenarios and expected outcomes with participants.
3.  Participants complete tasks without developer intervention where
    possible.
4.  Record completion, confusion, defects, and qualitative feedback.
5.  Classify findings by severity and product impact.
6.  Fix release-blocking defects and rerun affected scenarios.
7.  Obtain explicit acceptance or record the remaining limitations and
    decision owner.

### 11.6 Defect severity

  -----------------------------------------------------------------------
  Severity                Definition              Release handling
  ----------------------- ----------------------- -----------------------
  Critical                Data loss/corruption,   Block release
                          major privacy breach,   
                          privilege escalation,   
                          or platform unusable    

  High                    Core workflow broken,   Block release unless
                          materially misleading   formally waived with
                          analytics, or serious   mitigation
                          security issue          

  Medium                  Important feature       Fix before release
                          degraded with a         where practical;
                          reasonable workaround   otherwise document

  Low                     Cosmetic or minor       May be scheduled after
                          usability issue         release
  -----------------------------------------------------------------------

### 11.7 Acceptance exit criteria

-   All release-critical acceptance scenarios pass.
-   No unresolved critical defects remain.
-   High-severity defects are resolved or formally accepted with a
    documented mitigation and owner.
-   Methodology and limitation disclosures are visible and
    understandable.
-   Product owner or designated approver records the acceptance
    decision.

## 12. Test Data Management

### 12.1 Data categories

Use three categories:

1.  **Synthetic fixtures:** hand-crafted records for deterministic edge
    cases.
2.  **Sanitized snapshots:** approved subsets of collected data with
    unnecessary personal information removed.
3.  **Evaluation datasets:** versioned and access-controlled datasets
    with documented labels and split assignments.

Do not copy production user records into local or CI environments.

### 12.2 Steam review fixtures

Fixtures should cover:

-   Positive and negative `voted_up` values.
-   Different languages.
-   Different purchase types.
-   Empty and long review text.
-   Missing optional fields.
-   Updated reviews.
-   Duplicate logical review IDs.
-   Cursor continuation and terminal pages.
-   HTTP 429, timeout, malformed JSON, and server error responses.

Do not retain SteamID or unnecessary author, hardware, or profile
information in test fixtures. Use synthetic identifiers when an
identifier is required to test parsing.

### 12.3 Test data lifecycle

-   Fixtures must have an owner and documented purpose.
-   Evaluation datasets must be versioned and access-controlled.
-   Expired temporary data must be deleted.
-   Test exports must be stored only in approved test storage and
    removed after use.
-   Test data must not be mistaken for production analytics.

## 13. CI/CD Quality Gates

### 13.1 Pull-request checks

Recommended required checks:

1.  Formatting and linting.
2.  Static type checking.
3.  Backend unit tests.
4.  Frontend unit/component tests.
5.  Critical database and service integration tests.
6.  API contract tests for changed endpoint groups.
7.  Frontend production build.
8.  Dependency and secret scanning.
9.  Migration validation when database schema changes.

Run the smallest relevant test set during development, but do not bypass
required CI checks before merging.

### 13.2 Release-candidate checks

Before a release candidate is approved:

-   Run the complete backend and frontend test suites.
-   Run all critical integration and API tests.
-   Run the critical E2E journeys in staging.
-   Validate migrations from the prior supported release.
-   Run ML evaluation gates for any model or taxonomy change.
-   Complete acceptance scenarios.
-   Review security and dependency findings.
-   Verify backup and recovery procedures relevant to the release.
-   Confirm observability and rollback procedures.

### 13.3 Suggested CI commands

Adapt commands to the actual repository scripts and configuration.

``` bash
# Backend
ruff check apps/api
ruff format --check apps/api
mypy apps/api
pytest apps/api/tests/unit
pytest apps/api/tests/integration
pytest apps/api/tests/api

# Frontend
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build

# Browser E2E
npx playwright test

# Database migrations
alembic upgrade head
```

ML evaluation commands should be explicit and tied to a dataset snapshot
and model configuration. Do not make a generic test command silently
download an unpinned dataset or model.

## 14. Regression Testing

A regression test should be added whenever a defect reveals a missing
assertion or violated contract.

High-priority regression areas:

-   Steam API pagination and cursor persistence.
-   Review upsert and deduplication.
-   Ingestion retries and watermark advancement.
-   Model-version mixing in analytics.
-   Date and timezone filters.
-   Public versus private workspace access.
-   Export authorization and quota enforcement.
-   Empty, partial, and stale analytics states.
-   API response schema compatibility.
-   Migration rollback and forward compatibility where supported.

For production incidents, reproduce the failure with a deterministic
fixture before applying the fix where feasible.

## 15. Performance and Reliability Checks

Although detailed load testing may be outside the MVP's first delivery,
the release process should verify the most important resource and
reliability risks.

Test or measure:

-   Game search latency under expected catalog size.
-   Analytics query latency for common dashboard filters.
-   Review pagination under expected page sizes.
-   Export job memory and execution time.
-   Worker throughput and queue backlog behavior.
-   Database query plans for high-volume review and prediction tables.
-   Cache invalidation after ingestion or model activation.
-   Recovery after worker termination during a job.

Use representative synthetic data volumes. Record environment, dataset
size, concurrency, and measurement method. Do not publish benchmark
claims without reproducible evidence.

## 16. Security and Privacy Testing

Include security tests in the normal test lifecycle:

-   Authentication and authorization bypass attempts.
-   Object-level authorization for projects, saved analyses, and
    exports.
-   Input validation and injection resistance.
-   Rate-limit behavior.
-   Secret and token leakage checks.
-   Unsafe file type and export path handling.
-   Dependency vulnerability checks.
-   Sensitive data exposure in logs and error responses.
-   CSRF/session protections where applicable to the chosen
    authentication mechanism.

Do not store Steam account identifiers or unnecessary author data merely
to make tests easier. Test audit logging without placing credentials,
tokens, or review-author personal data in log messages.

## 17. Test Reporting and Traceability

### 17.1 Test report contents

For each CI or release test run, retain:

-   Commit SHA and branch.
-   Test suite and environment.
-   Pass, fail, skip, and retry counts.
-   Coverage summary where applicable.
-   Failed test names and diagnostic artifacts.
-   Database migration result.
-   Dataset and model version for ML evaluation.
-   Known deviations and approved waivers.

### 17.2 Requirement traceability

Maintain traceability between:

-   SRS requirement IDs.
-   API endpoint operations.
-   Database invariants.
-   ML specification release gates.
-   Test case IDs.
-   Acceptance scenario IDs.

A requirement is not considered verified solely because a related screen
or endpoint exists. Its expected behavior must be asserted by an
appropriate test or explicitly accepted as a documented manual check.

### 17.3 Suggested test case identifier format

``` text
UT-<MODULE>-<NNN>   Unit test
IT-<MODULE>-<NNN>   Integration test
API-<AREA>-<NNN>    API test
E2E-<FLOW>-<NNN>    End-to-end test
ML-<TASK>-<NNN>     ML evaluation test
AT-<NNN>            Acceptance test
```

Examples:

-   `UT-INGEST-001`
-   `IT-DB-004`
-   `API-RESEARCH-003`
-   `E2E-EXPORT-001`
-   `ML-SENTIMENT-002`
-   `AT-07`

## 18. MVP Release Checklist

### Engineering

-   [ ] Backend and frontend unit tests pass.
-   [ ] Critical integration tests pass against PostgreSQL and
    Redis/Celery test services.
-   [ ] API contract tests pass for all MVP endpoints.
-   [ ] Critical E2E journeys pass in staging.
-   [ ] Database migrations are validated.
-   [ ] No unresolved critical security findings remain.
-   [ ] Logging and health checks are operational.

### Data and ingestion

-   [ ] Steam adapter fixtures cover pagination and failure cases.
-   [ ] Review upserts are idempotent.
-   [ ] Review page, batch accounting, and checkpoint are atomic.
-   [ ] Incomplete syncs do not advance the watermark.
-   [ ] Retry and recovery behavior is verified.
-   [ ] Collection policy and sample limitations are disclosed.

### ML and analytics

-   [ ] Sentiment model passes its approved evaluation gate.
-   [ ] Aspect model passes its approved evaluation gate, if enabled.
-   [ ] Topic model has quantitative and human review, if enabled.
-   [ ] Model versions and dataset provenance are recorded.
-   [ ] Aggregates do not silently mix model versions.
-   [ ] Empty and insufficient-data states are handled correctly.

### Product acceptance

-   [ ] Public users can discover and inspect indexed games without
    login.
-   [ ] Comparison metrics use consistent definitions.
-   [ ] Research workspace access rules are verified.
-   [ ] Export permissions and quotas are enforced.
-   [ ] Methodology and limitations are visible.
-   [ ] Acceptance decision is recorded by the designated approver.

## 19. Open Decisions

The following items should be finalized as implementation and evaluation
data become available:

1.  Final macro-F1 and per-class thresholds for each supported language.
2.  Minimum human-labeled evaluation sample size per language and class.
3.  Whether the MVP enables ABSA and topic modeling at launch or stages
    them after sentiment.
4.  Exact E2E browser matrix and supported viewport sizes.
5.  Performance targets based on expected indexed-game and review
    volumes.
6.  Whether acceptance testing is conducted with an external pilot
    community and what approvals are required.
7.  Final test coverage thresholds after the first stable implementation
    baseline.

Changes to these decisions must be reflected in this document and, where
relevant, the ML Specification, SRS, API Specification, or System
Design.

## 20. Final Testing Policy

SteamScoop is ready for an MVP release only when its critical software
workflows, data-integrity invariants, API contracts, ML evaluation
gates, and user acceptance scenarios have been verified.

The platform must prefer transparent limitations over unsupported
certainty. A technically successful pipeline is not sufficient if its
data is incomplete, its model quality is unverified, or its analytics
could mislead users.

**Testing standard:** every critical requirement must have a defined
verification method, every release-blocking defect must be resolved or
formally dispositioned, and every published analytical result must
remain traceable to its data scope and model version.
