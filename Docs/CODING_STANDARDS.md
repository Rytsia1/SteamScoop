# SteamScoop --- Coding Standards

**Document:** `CODING_STANDARDS.md`\
**Version:** 1.0\
**Status:** Proposed engineering baseline\
**Product:** SteamScoop --- *Understand Games Through Data.*

------------------------------------------------------------------------

## 1. Purpose and scope

This document defines the coding standards for the SteamScoop codebase.
It applies to the frontend, backend API, background workers, data
ingestion, NLP/ML pipelines, database access, tests, and infrastructure
configuration.

The purpose is to keep the codebase consistent, readable, type-safe,
testable, secure, maintainable, and reproducible.

### 1.1 Normative language

-   **MUST**: required for correctness, security, or maintainability.
-   **SHOULD**: recommended unless a documented reason justifies an
    exception.
-   **MAY**: optional practice.

### 1.2 Technology baseline

  -----------------------------------------------------------------------
  Layer                               Standard
  ----------------------------------- -----------------------------------
  Frontend                            React, TypeScript, Vite

  UI styling                          Tailwind CSS

  Client data fetching                TanStack Query

  Visualization                       Apache ECharts

  Backend                             Python, FastAPI, Pydantic

  ORM and migrations                  SQLAlchemy, Alembic

  HTTP client                         HTTPX

  Database                            PostgreSQL

  Background jobs                     Celery

  Broker/cache                        Redis

  Data processing                     Pandas, NumPy

  ML                                  scikit-learn, PyTorch, Hugging
                                      Face, Sentence Transformers,
                                      BERTopic

  Testing                             pytest, Playwright, frontend test
                                      runner

  Static quality                      Ruff, mypy or Pyright, ESLint,
                                      Prettier

  Delivery                            Docker, GitHub Actions
  -----------------------------------------------------------------------

Do not add a major framework or infrastructure dependency without
documenting the problem it solves.

------------------------------------------------------------------------

## 2. General engineering principles

1.  **Clarity over cleverness.** Code should be understandable to a
    contributor who did not write it.
2.  **Single responsibility.** A function or module should have one
    clear reason to change.
3.  **Explicit boundaries.** Separate API, business logic, persistence,
    integrations, and ML processing.
4.  **Validate at boundaries.** Validate external requests, Steam
    responses, configuration, and model outputs.
5.  **Keep source and derived data separate.** Never confuse raw Steam
    fields with model predictions or aggregates.
6.  **Make side effects visible.** Database writes, network calls, file
    access, and job submission should be explicit.
7.  **Prefer deterministic behavior.** Data and ML pipelines should be
    reproducible where practical.
8.  **Fail safely.** Do not hide errors, silently substitute data, or
    return fabricated defaults.
9.  **Keep dependencies controlled.** Pin dependencies and review
    licenses and security advisories.
10. **Document decisions, not obvious syntax.** Comments should explain
    why, assumptions, and non-obvious constraints.

------------------------------------------------------------------------

## 3. Repository and folder structure

Use a monorepo initially. Keep frontend and backend deployable
independently while sharing one repository and CI configuration.

### 3.1 Recommended top-level structure

``` text
steamscoop/
├── apps/
│   ├── web/
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── assets/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   ├── pages/
│   │   │   ├── schemas/
│   │   │   ├── styles/
│   │   │   └── types/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── api/
│       ├── app/
│       │   ├── api/v1/endpoints/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── integrations/steam/
│       │   ├── ingestion/
│       │   ├── intelligence/
│       │   │   ├── sentiment/
│       │   │   ├── absa/
│       │   │   └── topics/
│       │   ├── analytics/
│       │   ├── workers/
│       │   └── main.py
│       ├── alembic/
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── contract/
│       ├── pyproject.toml
│       └── alembic.ini
│
├── ml/
│   ├── datasets/manifests/
│   ├── experiments/
│   ├── notebooks/
│   ├── src/steamscoop_ml/
│   │   ├── data/
│   │   ├── preprocessing/
│   │   ├── sentiment/
│   │   ├── absa/
│   │   ├── topics/
│   │   ├── evaluation/
│   │   └── registry/
│   ├── tests/
│   └── pyproject.toml
│
├── infra/
│   ├── docker/
│   ├── compose/
│   └── scripts/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── ml/
│   └── decisions/
├── scripts/
├── .github/workflows/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── CONTRIBUTING.md
```

### 3.2 Folder ownership

  -----------------------------------------------------------------------
  Folder                  Responsibility          Must not contain
  ----------------------- ----------------------- -----------------------
  `api/endpoints`         HTTP parsing,           Complex business logic
                          dependency injection,   
                          response mapping        

  `schemas`               Request/response        Database queries
                          validation and          
                          serialization           

  `models`                SQLAlchemy mappings and HTTP handling
                          relationships           

  `repositories`          Query and persistence   HTTP status decisions
                          operations              

  `services`              Business use cases and  Framework-specific
                          orchestration           response objects where
                                                  avoidable

  `integrations/steam`    Steam transport,        Public API route logic
                          mapping, retry          
                          classification          

  `ingestion`             Collection policy,      UI concerns
                          cursor progression,     
                          batch handling          

  `intelligence`          Inference interfaces    Direct public HTTP
                          and prediction          concerns
                          orchestration           

  `ml/src`                Offline training,       Production secrets
                          evaluation, dataset     
                          preparation             

  `workers`               Celery task entry       Duplicated business
                          points and              rules
                          orchestration           

  `features`              Frontend feature        Backend implementation
                          modules                 details

  `components`            Reusable presentational Feature-specific data
                          UI                      orchestration where
                                                  avoidable
  -----------------------------------------------------------------------

### 3.3 Dependency direction

Preferred backend dependency flow:

``` text
API endpoints
    ↓
Services / use cases
    ↓
Repositories and integration interfaces
    ↓
SQLAlchemy / HTTPX / external systems
```

Rules: - Lower-level modules must not import API endpoint modules. - ORM
models must not import services. - Repositories should not decide HTTP
status codes. - Services should not depend on FastAPI `Request` or
`Response` objects. - Steam-specific response shapes must be mapped into
internal schemas. - Avoid circular imports. Move shared contracts to a
lower-level module when needed.

------------------------------------------------------------------------

## 4. Naming conventions

### 4.1 General naming

  ----------------------------------------------------------------------------------------------
  Element                 Convention              Example
  ----------------------- ----------------------- ----------------------------------------------
  Python modules          `snake_case`            `review_service.py`

  Python functions        `snake_case`            `calculate_sentiment_rate()`

  Python variables        `snake_case`            `review_count`

  Python classes          `PascalCase`            `ReviewRepository`

  Python constants        `UPPER_SNAKE_CASE`      `MAX_PAGE_SIZE`

  TypeScript              `camelCase`             `fetchGameReviews()`
  variables/functions                             

  React components        `PascalCase`            `ReviewTable.tsx`

  React hooks             `use` + `camelCase`     `useGameOverview.ts`

  TypeScript              `PascalCase`            `GameOverview`
  types/interfaces                                

  Database tables/columns `snake_case`, singular  `sentiment_prediction`
                          tables                  

  API paths               plural resource nouns   `/games/{game_id}/reviews`

  Environment variables   `UPPER_SNAKE_CASE`      `DATABASE_URL`

  Celery tasks            module-qualified        `app.workers.ingestion.collect_game_reviews`
                          `snake_case`            

  Test files              `test_*.py`,            `test_review_service.py`
                          `*.test.ts(x)`          
  ----------------------------------------------------------------------------------------------

### 4.2 Boolean and function naming

Use descriptive boolean prefixes: `is_active`, `has_more`, `can_export`,
`should_retry`.

Prefer verbs that describe behavior: - `create_ingestion_job()` -
`fetch_review_page()` - `normalize_review_text()` -
`predict_sentiment()` - `build_game_analytics()`

Avoid ambiguous names such as `process_data()`, `handle_item()`, or
`do_task()` unless the context is exceptionally clear.

### 4.3 Database naming

-   Table names are singular: `game`, `review`, `pipeline_run`.
-   Primary key: `id`.
-   Foreign keys: `<referenced_entity>_id`, e.g. `game_id`.
-   Timestamps: `<event>_at`, e.g. `steam_created_at`.
-   Index names: `ix_<table>_<columns>`.
-   Unique constraints: `uq_<table>_<columns>`.
-   Foreign keys: `fk_<table>_<column>_<referenced_table>`.

------------------------------------------------------------------------

## 5. Python coding conventions

### 5.1 Formatting and linting

Use Ruff for linting and formatting, PEP 8 as the baseline, and useful
PEP 257-style docstrings for public interfaces. Configure a consistent
maximum line length (recommended 100--120 characters).

``` bash
ruff check .
ruff format --check .
ruff format .
```

### 5.2 Type annotations

-   Add annotations to public functions, service methods, repository
    methods, and non-trivial internal functions.
-   Use concrete collection types such as `list[Review]`,
    `dict[str, int]`, and `Sequence[str]`.
-   Use `X | None` for optional values on supported Python versions.
-   Avoid `Any`; if unavoidable at an external boundary, validate and
    convert it immediately.
-   Use `TypedDict`, dataclasses, or Pydantic models for structured
    data.
-   Use `Protocol` for interfaces where multiple implementations are
    expected.
-   Do not use type ignores without a short explanation.

Example:

``` python
from collections.abc import Sequence

def calculate_positive_rate(
    positive_count: int,
    negative_count: int,
) -> float | None:
    denominator = positive_count + negative_count
    if denominator == 0:
        return None
    return positive_count / denominator
```

### 5.3 Functions, classes, and imports

-   Keep functions focused and reasonably short.
-   Prefer composition over deep inheritance.
-   Avoid classes that only wrap one function without adding state or
    behavior.
-   Avoid global mutable state.
-   Pass dependencies explicitly through constructors or FastAPI
    dependencies.
-   Do not instantiate database engines or HTTP clients repeatedly
    inside request handlers.
-   Group imports: standard library, third-party packages, then local
    modules.
-   Use absolute imports within the application package where practical.
-   Avoid wildcard imports and remove unused imports.

### 5.4 Docstrings and comments

Document public interfaces, non-obvious algorithms, business invariants,
external API quirks, and transformations that affect research results.
Do not write comments that merely repeat the code.

------------------------------------------------------------------------

## 6. TypeScript and React conventions

### 6.1 Type safety

-   Enable `strict: true` in TypeScript.
-   Avoid `any`; use `unknown` at untrusted boundaries and narrow it.
-   Define explicit API request/response types.
-   Prefer discriminated unions for state machines and API result
    variants.
-   Use runtime validation for data crossing trust boundaries where
    appropriate.
-   A TypeScript type does not validate a network response at runtime.

Example:

``` typescript
export type SentimentLabel = "positive" | "negative" | "neutral";

export interface SentimentSummary {
  positiveCount: number;
  negativeCount: number;
  neutralCount: number;
  unclassifiedCount: number;
  modelVersion: string;
}
```

The API uses `snake_case` on the wire; the frontend may use `camelCase`
internally. Map between them consistently in the API client.

### 6.2 Component conventions

-   Use function components.
-   Keep components focused on one UI responsibility.
-   Extract reusable logic into custom hooks.
-   Keep server state in TanStack Query.
-   Keep ephemeral UI state local unless shared state is genuinely
    required.
-   Avoid duplicating API calls across components.
-   Do not place complex business calculations directly inside JSX.
-   Use stable keys when rendering lists.
-   Handle loading, empty, error, and partial-data states explicitly.

Suggested feature structure:

``` text
features/
└── game-intelligence/
    ├── api/gameIntelligenceApi.ts
    ├── components/
    │   ├── SentimentChart.tsx
    │   └── AspectBreakdown.tsx
    ├── hooks/useGameIntelligence.ts
    ├── types/gameIntelligence.ts
    └── utils/formatMetrics.ts
```

### 6.3 Hooks, styling, and accessibility

-   Follow React hook rules; never call hooks conditionally or inside
    loops.
-   Avoid effects for values that can be derived during render.
-   Keep effect dependencies correct.
-   Prefer TanStack Query for remote data rather than manually managing
    request lifecycle in `useEffect`.
-   Use Tailwind utility classes consistently.
-   Provide semantic HTML, accessible labels, keyboard navigation, and
    visible focus states.
-   Charts must have textual summaries or accessible alternatives.
-   Do not encode meaning through color alone.

Suggested quality commands:

``` bash
npm run lint
npm run typecheck
npm run test
npm run build
```

------------------------------------------------------------------------

## 7. API and backend conventions

### 7.1 Thin endpoint handlers

Endpoint handlers should: 1. Parse and validate input. 2. Resolve
authentication/authorization dependencies. 3. Call a service/use case.
4. Map the result to a response schema. 5. Set the correct HTTP status.

They should not contain multi-step business workflows or complex SQL.

Example:

``` python
@router.get("/games/{game_id}", response_model=GameResponse)
def get_game(
    game_id: UUID,
    service: GameService = Depends(get_game_service),
) -> GameResponse:
    game = service.get_public_game(game_id)
    return GameResponse(data=GameRead.model_validate(game))
```

This is illustrative; exact dependency and serialization patterns should
follow the project's SQLAlchemy and Pydantic versions.

### 7.2 Pydantic schemas

-   Use separate request and response models.
-   Reject unexpected fields for sensitive mutation requests where
    appropriate.
-   Apply explicit length, range, and format constraints.
-   Do not expose ORM models directly.
-   Exclude password hashes, internal payloads, private storage URIs,
    and secret configuration.
-   Use stable enum definitions.
-   Use `ConfigDict(from_attributes=True)` where ORM attribute
    validation is intended.

### 7.3 Service and repository responsibilities

**Service layer** - Enforces business rules. - Coordinates transactions
and integrations. - Decides which domain errors to raise. - Does not
construct framework-specific HTTP responses.

**Repository layer** - Encapsulates SQLAlchemy queries. - Uses explicit
filters and ordering. - Does not silently swallow database exceptions. -
Does not commit transactions unless transaction ownership is explicitly
assigned.

Recommended default: transaction boundaries are controlled by the
service/unit-of-work layer.

### 7.4 Database sessions and HTTP clients

-   Use one scoped SQLAlchemy session per request/task unit of work.
-   Do not share a session across concurrent tasks or threads.
-   Close sessions reliably and use explicit transaction boundaries.
-   Avoid lazy-loading ORM relationships during response serialization
    if it causes hidden queries.
-   Do not hold database transactions open while waiting for external
    HTTP calls.
-   Reuse configured HTTPX clients where appropriate.
-   Set connect/read/write/pool timeouts.
-   Configure bounded retries only for retryable operations.
-   Respect upstream rate-limit responses and `Retry-After`.
-   Validate response status and schema.
-   Never log authorization headers or API keys.
-   Do not let arbitrary user input select an upstream URL.

------------------------------------------------------------------------

## 8. Error handling conventions

### 8.1 Error categories

Separate validation, domain/business-rule, authentication/authorization,
database/infrastructure, external provider, ML/data-processing, and
unexpected programming errors.

### 8.2 Error handling rules

1.  Never use a bare `except:` clause.
2.  Catch the narrowest useful exception type.
3.  Do not silently ignore exceptions.
4.  Do not return success-shaped data after a failed operation.
5.  Preserve the original exception as the cause when re-raising.
6.  Translate low-level exceptions at the appropriate application
    boundary.
7.  Log unexpected errors with a correlation/request ID.
8.  Never return stack traces or raw SQL errors to clients.
9.  Avoid duplicate logging at every layer; log once at the boundary
    that owns the failure.
10. Retry only transient failures and only with a bounded policy.

### 8.3 Domain exceptions

Define stable application exceptions:

``` python
class DomainError(Exception):
    """Base class for expected application errors."""


class GameNotFoundError(DomainError):
    """Raised when a public game cannot be found."""


class ActiveIngestionJobError(DomainError):
    """Raised when an incompatible active job already exists."""
```

Map domain exceptions to the API error envelope in centralized exception
handlers.

### 8.4 Logging

Use structured logs with timestamp, level, service/module, request ID or
job ID, event name, stable error code, duration, and relevant
non-sensitive resource IDs.

Never log: - Passwords or password hashes. - Access/refresh tokens. -
Steam publisher API keys. - Database credentials. - Raw session
cookies. - Unnecessary user identifiers. - Full review text by default.

### 8.5 Celery task errors

-   Make tasks idempotent where possible.
-   Set retry limits and backoff explicitly.
-   Distinguish retryable from terminal failures.
-   Persist durable job status and counters in PostgreSQL.
-   Do not rely on Redis broker state as the only record of progress.
-   Do not retry deterministic validation failures indefinitely.
-   Ensure a task retry cannot advance a cursor without committing
    corresponding data.

------------------------------------------------------------------------

## 9. Type safety and data contracts

### 9.1 Boundary validation

Validate data at HTTP request entry, Steam API response entry,
database-to-API serialization, ML model output, export input/field
selection, and environment/configuration loading.

Static type annotations do not replace runtime validation for external
data.

### 9.2 Avoid ambiguous values

-   Use `None`/`null` only when it has a defined meaning.
-   Do not use `0` to mean missing.
-   Do not use empty strings to mean unknown.
-   Use explicit status enums for lifecycle states.
-   Distinguish missing prediction, low-confidence prediction, and
    neutral sentiment.

### 9.3 Numeric and time safety

-   Use integer types for counts.
-   Use `NUMERIC`/`Decimal` for monetary values.
-   Use bounded numeric types for confidence and probabilities.
-   Validate confidence in `[0, 1]`.
-   Document score scales and denominators.
-   Store timestamps as timezone-aware UTC values using PostgreSQL
    `TIMESTAMPTZ`.
-   Never compare naive and aware datetimes.
-   Use explicit inclusive/exclusive range semantics.
-   Convert to local timezone only for display.
-   Do not assume the server's local timezone.

------------------------------------------------------------------------

## 10. Security practices

### 10.1 Secrets and configuration

-   Keep `.env` files out of Git.
-   Commit `.env.example` with placeholders only.
-   Load secrets from environment/secret manager.
-   Validate required settings at application startup.
-   Never hardcode secrets in source code, notebooks, tests,
    Dockerfiles, or CI configuration.
-   Rotate exposed secrets immediately.

### 10.2 Authentication and authorization

-   Use secure password hashing such as Argon2id if password
    authentication is enabled.
-   Use secure, HttpOnly, SameSite session cookies.
-   Apply CSRF protection to cookie-authenticated mutations.
-   Enforce authorization in backend services or dependencies.
-   Check object-level access for every private project, analysis,
    snapshot, and export.
-   Do not trust role claims supplied by the browser.
-   Avoid exposing whether private resources exist when that creates an
    information leak.

### 10.3 Input and output safety

-   Validate and constrain all user input.
-   Use parameterized SQL and ORM query APIs.
-   Never interpolate raw user input into SQL, shell commands, or file
    paths.
-   Render Steam review text as untrusted text, never as trusted HTML.
-   Sanitize or escape data at the output context.
-   Validate uploaded files if upload functionality is introduced.
-   Restrict export columns to an allowlist.

### 10.4 External API and database safety

-   Use HTTPS and restrict outbound destinations to configured
    providers.
-   Set timeouts and bounded retries.
-   Validate Steam response shape and numeric ranges.
-   Handle `429` and transient upstream errors safely.
-   Do not expose upstream credentials to frontend clients.
-   Use a least-privilege database account.
-   Separate migration credentials from runtime credentials where
    practical.
-   Require TLS for managed production database connections.
-   Back up production data and test restore procedures.
-   Do not use production credentials or personal data in local
    development fixtures.

### 10.5 Dependency and supply-chain security

-   Pin dependencies or use a lockfile.
-   Review package provenance and licenses.
-   Run dependency vulnerability checks in CI.
-   Remove unused dependencies.
-   Do not install packages from untrusted URLs or repositories without
    review.
-   Keep base container images updated.

### 10.6 ML-specific safety

-   Treat review text as untrusted user-generated content.
-   Do not execute code or follow instructions contained in reviews.
-   Do not send review text to third-party services unless approved by
    data policy.
-   Do not infer sensitive personal attributes from reviews.
-   Keep model artifacts and training datasets access-controlled.
-   Record model and dataset provenance.
-   Avoid publishing examples that expose unnecessary personal
    information.

------------------------------------------------------------------------

## 11. Data and ML code quality

### 11.1 Separate experiments from production

-   Notebooks are for exploration, not production orchestration.
-   Move reusable logic from notebooks into importable Python modules.
-   Production workers must call versioned preprocessing and inference
    interfaces.
-   Avoid hidden state and order-dependent notebook execution.
-   Keep dataset manifests and experiment configurations under version
    control.
-   Do not commit large raw datasets or model weights unless explicitly
    approved.

### 11.2 Deterministic pipelines

-   Record random seeds.
-   Record dataset and model versions.
-   Pin preprocessing configuration.
-   Use stable train/validation/test split identifiers.
-   Preserve evaluation scripts.
-   Make ingestion and prediction writes idempotent.
-   Document nondeterministic operations where exact reproducibility is
    not possible.

### 11.3 Metric correctness

-   Never conflate Steam recommendation with model sentiment.
-   Include denominators with percentages.
-   Keep unclassified/low-confidence counts visible.
-   Version aspect taxonomy and topic models.
-   Do not compare incompatible topic IDs across retraining.
-   Record model version in prediction and aggregate outputs.
-   Test aggregate calculations against independently computed fixtures.

### 11.4 Dataset quality

Check nulls, duplicates, language distribution, class distribution,
timestamp validity, duplicate/near-duplicate leakage across splits,
sampling policy, and annotation disagreements.

Keep test data isolated from training and tuning.

------------------------------------------------------------------------

## 12. Testing standards

### 12.1 Test pyramid

  -----------------------------------------------------------------------
  Test type               Purpose                 Examples
  ----------------------- ----------------------- -----------------------
  Unit                    Validate isolated logic Sentiment score
                                                  formula, cursor policy

  Integration             Validate components     Repository +
                          together                PostgreSQL, Steam
                                                  adapter

  Contract                Validate API schemas    Pydantic response
                          and behavior            contract, error
                                                  envelope

  ML evaluation           Validate predictive     Macro F1, per-class
                          quality                 metrics

  End-to-end              Validate user workflows Search game, inspect
                                                  reviews, compare games

  Security                Validate access         Private project access,
                          boundaries              export authorization
  -----------------------------------------------------------------------

### 12.2 Test requirements

-   Test normal, boundary, and failure cases.
-   Avoid external network dependencies in unit tests.
-   Use deterministic fixtures.
-   Test business rules independently from FastAPI.
-   Use a disposable PostgreSQL database or isolated test schema for
    integration tests.
-   Test migrations from an empty database.
-   Test unique constraints, foreign keys, transaction rollback, and
    atomic cursor persistence.
-   Use HTTP mocking for Steam adapter tests.
-   Verify API response schemas, authorization, pagination, and error
    envelopes.
-   Test ML preprocessing edge cases, output schema, probability bounds,
    model loading, and fixed evaluation metrics.

Example test name:

``` python
def test_incremental_job_does_not_advance_watermark_on_failed_batch():
    ...
```

A test name should communicate the behavior being protected.

------------------------------------------------------------------------

## 13. Code quality gates

### 13.1 Required checks

Backend:

``` bash
ruff check .
ruff format --check .
mypy app
pytest
```

Frontend:

``` bash
npm run lint
npm run typecheck
npm run test
npm run build
```

Database:

``` bash
alembic upgrade head
```

The exact mypy target and frontend script names must match repository
configuration.

### 13.2 Quality expectations

-   No unresolved lint errors.
-   No unreviewed type-check failures.
-   Tests pass.
-   Migrations apply from a clean database.
-   No committed secrets.
-   No accidental dataset/model artifact commits.
-   No API contract breaking changes without a versioning/deprecation
    plan.
-   No unbounded retry loops.
-   No public endpoint that bypasses authorization or rate limits.

### 13.3 Code review checklist

Reviewers should check: - Is the change in the correct module? - Are
names and types clear? - Are business rules enforced in the backend? -
Are external inputs validated? - Are errors handled without hiding
failures? - Are database operations transactional and idempotent where
required? - Are security and privacy implications addressed? - Are tests
sufficient? - Are docs and OpenAPI contracts updated? - Are metrics and
model versions correctly represented?

### 13.4 Complexity and abstraction

-   Do not introduce abstractions without a concrete use case.
-   Avoid giant service classes and generic "manager" modules.
-   Avoid deep inheritance trees.
-   Prefer small pure functions for calculations.
-   Use interfaces where multiple implementations or test substitution
    are expected.
-   Refactor repeated logic only after confirming the repetition is
    truly the same concept.

------------------------------------------------------------------------

## 14. Git and collaboration conventions

### 14.1 Branch naming

Suggested patterns: - `feature/game-explorer` -
`feature/sentiment-dashboard` - `fix/review-pagination` -
`refactor/steam-adapter` - `docs/api-specification` -
`test/ingestion-recovery`

### 14.2 Commit messages

Use Conventional Commits:

``` text
feat(api): add game overview endpoint
fix(ingestion): preserve cursor on failed batch
docs(ml): document sentiment evaluation
test(reviews): cover cursor pagination
refactor(db): isolate review query repository
chore(deps): update fastapi dependencies
```

### 14.3 Pull requests

Every pull request should include purpose/scope, implementation summary,
linked issue/task, test evidence, migration notes, API/OpenAPI changes,
screenshots for meaningful UI changes, and security/privacy impact where
relevant.

Keep pull requests focused. Avoid mixing unrelated refactors with
feature work.

### 14.4 Generated and large files

Do not commit by default: - `.env` files; - virtual environments; -
`node_modules`; - build output; - logs; - local database files; - raw
review dumps; - model checkpoints; - large notebook outputs.

Use approved artifact/object storage for datasets and model files. Test
fixtures should be synthetic or appropriately anonymized and small.

------------------------------------------------------------------------

## 15. Documentation standards

Update documentation when a change affects architecture, API contracts,
database schema/migrations, ingestion/sampling policy, model
version/evaluation methodology, environment configuration, deployment,
or operations.

Recommended documentation: - `README.md`: setup and project overview. -
`CONTRIBUTING.md`: workflow and local development. - `SYSTEM_DESIGN.md`:
architecture. - `DATABASE_DESIGN.md`: database design. -
`ML_SPECIFICATION.md`: ML methodology and lifecycle. -
`API_SPECIFICATION.md`: API contracts. - `CODING_STANDARDS.md`:
engineering standards. - Architecture Decision Records (ADRs):
significant design choices.

Avoid copying the same detailed specification into multiple documents.
Link to the source of truth.

------------------------------------------------------------------------

## 16. Environment and configuration standards

-   Use typed settings management (for example, Pydantic Settings).
-   Separate development, test, staging, and production configuration.
-   Provide safe defaults only for non-secret local settings.
-   Fail fast when required production secrets/configuration are
    missing.
-   Never use production credentials in test environments.
-   Keep `.env.example` synchronized with required variables.

Example:

``` env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/steamscoop
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

All values above are placeholders. Never commit real credentials.

------------------------------------------------------------------------

## 17. Performance and reliability standards

-   Paginate potentially large result sets.
-   Avoid N+1 database queries.
-   Select only the columns needed by a response.
-   Add indexes based on measured query patterns.
-   Use bounded HTTP timeouts and worker concurrency.
-   Keep long-running operations out of synchronous request handlers.
-   Use caching only when invalidation and freshness behavior are
    understood.
-   Monitor slow queries, queue depth, job age, and task failures.
-   Measure before optimizing.

### 17.1 Ingestion-specific invariants

-   Review upsert key is `(game_id, steam_review_id)`.
-   Review upsert, batch record, and cursor checkpoint are committed
    atomically per page.
-   Incremental watermark advances only after the complete requested
    range is committed.
-   Steam cursors are opaque and must not be synthesized.
-   Handle upstream rate limits with bounded backoff.
-   Public requests never enqueue uncontrolled ingestion.

### 17.2 ML-specific invariants

-   Every prediction identifies model and pipeline provenance.
-   Model versions are immutable.
-   A new model version does not overwrite historical predictions.
-   Training and inference preprocessing must be compatible.
-   Aggregate results identify the model-version combination used.
-   Unclassified and low-confidence outputs are not silently counted as
    neutral.

------------------------------------------------------------------------

## 18. Definition of Done

A code change is complete when applicable criteria are satisfied:

-   [ ] Implementation follows module boundaries and naming conventions.
-   [ ] Public interfaces have appropriate type annotations.
-   [ ] Input and external data are validated.
-   [ ] Error handling is explicit and does not hide failures.
-   [ ] Authorization and privacy implications are addressed.
-   [ ] Database changes include reviewed Alembic migrations.
-   [ ] Unit/integration/contract tests are added or updated.
-   [ ] Lint, format, type checks, tests, and build pass.
-   [ ] API/OpenAPI documentation is updated where relevant.
-   [ ] ML/data provenance is recorded where relevant.
-   [ ] No secrets, private data, or large unapproved artifacts are
    committed.
-   [ ] Operational impact and rollback/recovery behavior are
    understood.

Not every checkbox applies to every change, but any skipped security,
migration, or data-integrity requirement must have an explicit reason.

------------------------------------------------------------------------

## 19. Exceptions and standard evolution

These standards are a living engineering document.

An exception is acceptable when a clear technical constraint exists, the
exception is limited in scope, the reason is documented in the pull
request or an ADR, and security/data integrity are not weakened without
explicit review.

When a convention changes: 1. Update this document. 2. Update
formatter/linter/type-checker configuration. 3. Apply the change
consistently in touched modules. 4. Avoid unrelated mass refactors
unless separately planned.

------------------------------------------------------------------------

## 20. Final standard

SteamScoop should favor code that is explicit, typed, testable, secure,
and reproducible.

The most important engineering expectations are: 1. Keep
modular-monolith boundaries clear. 2. Validate all external inputs and
outputs. 3. Enforce authorization on the backend. 4. Make database
writes and background jobs safe to retry. 5. Preserve the distinction
between source data and ML interpretation. 6. Version models,
preprocessing, and analytical outputs. 7. Test business invariants, not
only happy paths. 8. Keep CI quality gates practical and mandatory. 9.
Document non-obvious decisions and API/data contract changes. 10. Prefer
measured simplicity over premature complexity.
