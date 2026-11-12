# SteamScoop --- API Specification

**Document:** `API_SPECIFICATION.md`\
**Version:** 1.0\
**Status:** Proposed baseline for MVP\
**Product:** SteamScoop --- *Understand Games Through Data.*

------------------------------------------------------------------------

## 1. Purpose and scope

This document defines the HTTP API contract between the SteamScoop
frontend and FastAPI backend. It specifies endpoint paths, HTTP methods,
request and response schemas, authentication, authorization, pagination,
filtering, error handling, and API compatibility rules.

The API supports: - Public game discovery and game intelligence. -
Review exploration and sentiment/aspect/topic analysis. - Game
comparisons. - Methodology and dataset transparency. - Optional accounts
and research workspaces. - Asynchronous data exports. - Restricted
administrative operations for catalog indexing, ingestion, and
model/pipeline monitoring.

The API is a public-facing application API. Steam Web API calls and
internal ML service calls are performed by backend adapters/workers and
are **not** exposed as direct public endpoints.

### 1.1 Design principles

1.  Public analytics endpoints are read-only and do not trigger
    arbitrary Steam ingestion.
2.  All public responses use a stable, documented envelope.
3.  Expensive operations such as ingestion, model inference, and exports
    are asynchronous.
4.  Authentication is optional for public analytics, but required for
    personal workspaces and privileged operations.
5.  Authorization is enforced by the backend, never only by frontend
    visibility.
6.  Pagination, filtering, sorting, and export limits are explicit and
    bounded.
7.  API responses expose model provenance and data limitations where
    relevant.
8.  API contracts use stable identifiers, not database implementation
    details.
9.  Internal stack traces, secrets, and raw upstream error bodies are
    never returned.
10. Breaking changes require a new API version or a documented migration
    window.

------------------------------------------------------------------------

## 2. API conventions

### 2.1 Base URL and versioning

Production base URL:

``` text
https://api.steamscoop.example.com/api/v1
```

The hostname is a placeholder and must be replaced during deployment.

All public application endpoints are versioned under `/api/v1`. Internal
health and metrics endpoints may be hosted separately and must not be
publicly exposed without access controls.

### 2.2 Content types

-   Request body: `application/json`
-   Response body: `application/json`
-   CSV export: `text/csv`
-   XLSX export: appropriate spreadsheet MIME type
-   JSON export: `application/json`

The API should return UTF-8 JSON.

### 2.3 Naming and serialization

-   JSON properties use `snake_case`.
-   Resource IDs are UUID strings unless explicitly identified as Steam
    IDs.
-   Timestamps use ISO 8601 with UTC offset, normally `Z`.
-   Dates use `YYYY-MM-DD`.
-   Enum values are lowercase strings.
-   Empty collections are `[]`, not `null`.
-   Optional values may be `null`.
-   Monetary values, if introduced, are serialized as decimal strings or
    documented numeric values; do not use binary floating-point for
    financial calculations.

### 2.4 Standard success envelope

Single-resource response:

``` json
{
  "data": {
    "id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "name": "Example Game"
  },
  "meta": {
    "request_id": "req_01JEXAMPLE"
  }
}
```

Collection response:

``` json
{
  "data": [],
  "meta": {
    "request_id": "req_01JEXAMPLE",
    "pagination": {
      "limit": 20,
      "has_more": false,
      "next_cursor": null
    }
  }
}
```

The examples are illustrative. Actual IDs and values will be generated
by the service.

### 2.5 Standard error envelope

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "details": [
      {
        "field": "limit",
        "issue": "Must be between 1 and 100."
      }
    ],
    "request_id": "req_01JEXAMPLE"
  }
}
```

Clients should branch on `error.code`, not parse human-readable
messages.

### 2.6 Request correlation

Every request receives a server-generated request ID. Return it in: -
`meta.request_id` for successful responses; - `error.request_id` for
errors; - the `X-Request-ID` response header.

If a client sends `X-Request-ID`, the server may accept it only after
validating length and allowed characters. It must not allow arbitrary
values to inject log content.

------------------------------------------------------------------------

## 3. HTTP status code policy

  -----------------------------------------------------------------------------
  Status                        Meaning                 Typical use
  ----------------------------- ----------------------- -----------------------
  `200 OK`                      Request succeeded       Reads, updates,
                                                        completed synchronous
                                                        actions

  `201 Created`                 Resource created        Account, project, saved
                                                        analysis

  `202 Accepted`                Work accepted           Export, admin
                                asynchronously          ingestion, reprocessing

  `204 No Content`              Succeeded with no       Delete/archive action
                                response body           where appropriate

  `400 Bad Request`             Malformed request       Invalid JSON or
                                                        malformed cursor

  `401 Unauthorized`            Missing/invalid         Protected endpoint
                                authentication          without valid session

  `403 Forbidden`               Authenticated but not   Insufficient role or
                                permitted               project permission

  `404 Not Found`               Resource unavailable    Unknown resource or
                                                        resource intentionally
                                                        hidden

  `409 Conflict`                State conflict          Duplicate resource,
                                                        invalid transition,
                                                        active job conflict

  `413 Content Too Large`       Request too large       Export configuration or
                                                        body exceeds limit

  `422 Unprocessable Entity`    Valid JSON but invalid  Schema validation
                                fields/semantics        

  `429 Too Many Requests`       Rate limit exceeded     Client request quota

  `500 Internal Server Error`   Unexpected backend      Unhandled internal
                                error                   failure

  `502 Bad Gateway`             Invalid upstream        Steam or external
                                response                provider failure

  `503 Service Unavailable`     Temporarily unavailable Maintenance or
                                                        overloaded service

  `504 Gateway Timeout`         Upstream timeout        External dependency
                                                        timeout
  -----------------------------------------------------------------------------

Use `Retry-After` on `429` and temporary `503` responses when a useful
retry interval is known.

------------------------------------------------------------------------

## 4. Authentication and authorization

### 4.1 Public access

The following capabilities do not require an account: - Game search and
game details. - Public game analytics. - Public review exploration. -
Public aspect and topic insights. - Public comparisons. - Methodology
and dataset documentation.

Anonymous users are subject to stricter rate limits and export
restrictions.

### 4.2 Authentication model

For browser-based first-party clients, prefer secure server-managed
sessions: - Session cookie: `HttpOnly`, `Secure`, and an appropriate
`SameSite` policy. - CSRF protection for state-changing
cookie-authenticated requests. - Session rotation after login and
privilege changes. - Logout invalidates the server-side session.

If bearer tokens are used for a separate client, use short-lived access
tokens and a secure refresh-token rotation strategy. Do not store
long-lived secrets in browser local storage.

Authentication endpoints in this specification are optional until
account functionality is enabled.

### 4.3 Roles

  -----------------------------------------------------------------------
  Role                                Scope
  ----------------------------------- -----------------------------------
  Guest                               Public analytics and discovery

  Member                              Guest access plus personal
                                      workspace

  Researcher                          Member access plus explicitly
                                      granted research/export
                                      capabilities

  Moderator                           Optional moderation functions

  Admin                               Catalog, ingestion, model and
                                      platform administration
  -----------------------------------------------------------------------

A role does not automatically grant access to every research project.
Project membership and project-level permissions are evaluated
separately.

### 4.4 Authorization rules

-   The backend resolves the authenticated user from a trusted
    session/token.
-   The backend checks role and resource ownership/membership on every
    protected request.
-   Project owners can manage their own project and memberships.
-   Editors can modify project analyses and configuration within project
    policy.
-   Viewers can read shared project content.
-   Only authorized administrators can enqueue ingestion, change catalog
    state, or activate models.
-   A user must not access another user's private project by changing a
    UUID in the URL.
-   Return `404` rather than `403` for private resources when revealing
    their existence would be undesirable.
-   Frontend role checks are convenience only; they are not security
    controls.

### 4.5 CSRF, CORS, and secrets

-   Restrict CORS to explicitly configured frontend origins.
-   Never use wildcard origins with credentialed cookies.
-   Apply CSRF protection to cookie-authenticated mutation endpoints.
-   Store Steam publisher keys, database credentials, and signing
    secrets in a server-side secret manager/environment configuration.
-   Never return upstream credentials or model artifact storage
    credentials.

------------------------------------------------------------------------

## 5. Pagination, filtering, and sorting

### 5.1 Cursor pagination

Use cursor pagination for review lists and other collections that may
grow or change while a user browses.

Request parameters: - `limit`: default `20`, minimum `1`, maximum
`100`. - `cursor`: opaque URL-safe token returned by the API. - `sort`:
documented sort key and direction, if supported.

Response metadata:

``` json
{
  "pagination": {
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJrZXkiOiJleGFtcGxlIn0"
  }
}
```

Rules: - The cursor is opaque. Clients must not decode, construct, or
modify it. - A cursor is bound to the resource, filters, and sort order
that created it. - Invalid or incompatible cursors return
`400 INVALID_CURSOR`. - The server should use deterministic ordering
with a unique tie-breaker. - Cursor pagination should be keyset-based,
not a large SQL `OFFSET`. - A cursor may expire; if so, return a
documented cursor-expired error and require a fresh request.

### 5.2 Offset pagination

Offset pagination may be used for small administrative tables where
page-number navigation is useful.

Parameters: - `page`: default `1`. - `page_size`: default `20`, maximum
`100`.

Do not use offset pagination for large review corpora or high-churn
data.

### 5.3 Filtering

-   Each endpoint documents its allowed filters.
-   Unknown query parameters should be rejected or ignored consistently;
    recommended behavior is `422` for unsupported filter names to catch
    client mistakes.
-   Filter values must be validated and parameterized.
-   Date intervals use inclusive `from` and exclusive `to` semantics:
    `created_at >= from AND created_at < to`.
-   Maximum date-range windows may be enforced for expensive analytics.

### 5.4 Sorting

Only allowlisted sort keys are accepted. Never interpolate raw user
input into SQL `ORDER BY`.

Examples: - `created_at_desc` - `created_at_asc` - `votes_up_desc` -
`confidence_desc`

The API must document null ordering and tie-breaker behavior.

------------------------------------------------------------------------

## 6. Resource and endpoint catalogue

All paths below are relative to `/api/v1`.

### 6.1 System and methodology

  -----------------------------------------------------------------------------------------
  Method            Endpoint                  Auth                        Purpose
  ----------------- ------------------------- --------------------------- -----------------
  `GET`             `/health`                 Public or                   Basic service
                                              infrastructure-restricted   health

  `GET`             `/methodology`            Public                      Current
                                                                          collection and
                                                                          analysis
                                                                          methodology

  `GET`             `/methodology/models`     Public                      Public model
                                                                          cards and
                                                                          versions

  `GET`             `/methodology/datasets`   Public                      Dataset and
                                                                          sampling
                                                                          descriptions
  -----------------------------------------------------------------------------------------

Health endpoints must not disclose database credentials, internal
hostnames, stack traces, or detailed infrastructure topology. A separate
restricted readiness endpoint may test dependencies.

### 6.2 Games

  ---------------------------------------------------------------------------------------
  Method            Endpoint                       Auth              Purpose
  ----------------- ------------------------------ ----------------- --------------------
  `GET`             `/games`                       Public            Search/list indexed
                                                                     games

  `GET`             `/games/genres`                Public            Genre filter values

  `GET`             `/games/{game_id}`             Public            Game details

  `GET`             `/games/{game_id}/overview`    Public            Summary metrics and
                                                                     coverage

  `GET`             `/games/{game_id}/analytics`   Public            Time-series
                                                                     aggregate analytics

  `GET`             `/games/{game_id}/sentiment`   Public            Sentiment
                                                                     distribution/trend

  `GET`             `/games/{game_id}/aspects`     Public            Aspect-level insight

  `GET`             `/games/{game_id}/topics`      Public            Topic summary and
                                                                     prevalence

  `GET`             `/games/{game_id}/reviews`     Public            Paginated review
                                                                     explorer
  ---------------------------------------------------------------------------------------

### 6.3 Review intelligence

  -------------------------------------------------------------------------------------------
  Method            Endpoint                              Auth              Purpose
  ----------------- ------------------------------------- ----------------- -----------------
  `GET`             `/reviews/{review_id}`                Public            Review detail and
                                                                            available
                                                                            predictions

  `GET`             `/reviews/{review_id}/intelligence`   Public            Combined
                                                                            sentiment,
                                                                            aspects, and
                                                                            topics
  -------------------------------------------------------------------------------------------

### 6.4 Comparison

  Method   Endpoint         Auth     Purpose
  -------- ---------------- -------- --------------------------------
  `POST`   `/comparisons`   Public   Compare a bounded set of games

A comparison is a read-only analytical query. It must not create
ingestion jobs.

### 6.5 Authentication and account

  Method   Endpoint           Auth     Purpose
  -------- ------------------ -------- --------------------------------
  `POST`   `/auth/register`   Public   Register account, if enabled
  `POST`   `/auth/login`      Public   Start authenticated session
  `POST`   `/auth/logout`     Member   End current session
  `GET`    `/auth/me`         Member   Current user profile and roles

Registration and login may be disabled for a public analytics-only
pilot. If disabled, return `404 FEATURE_DISABLED` or omit the routes
from the published OpenAPI document.

### 6.6 Research workspace

  -----------------------------------------------------------------------------------------------------------------
  Method            Endpoint                                                    Auth              Purpose
  ----------------- ----------------------------------------------------------- ----------------- -----------------
  `GET`             `/projects`                                                 Member            List accessible
                                                                                                  projects

  `POST`            `/projects`                                                 Member            Create project

  `GET`             `/projects/{project_id}`                                    Project member    Read project

  `PATCH`           `/projects/{project_id}`                                    Owner/editor      Update project

  `DELETE`          `/projects/{project_id}`                                    Owner             Archive/delete
                                                                                                  project per
                                                                                                  policy

  `GET`             `/projects/{project_id}/games`                              Project member    List selected
                                                                                                  games

  `POST`            `/projects/{project_id}/games`                              Owner/editor      Add game to
                                                                                                  project

  `DELETE`          `/projects/{project_id}/games/{game_id}`                    Owner/editor      Remove game

  `GET`             `/projects/{project_id}/analyses`                           Project member    List saved
                                                                                                  analyses

  `POST`            `/projects/{project_id}/analyses`                           Owner/editor      Save analysis
                                                                                                  configuration

  `GET`             `/projects/{project_id}/analyses/{analysis_id}`             Project member    Read saved
                                                                                                  analysis

  `PATCH`           `/projects/{project_id}/analyses/{analysis_id}`             Owner/editor      Update saved
                                                                                                  analysis

  `DELETE`          `/projects/{project_id}/analyses/{analysis_id}`             Owner/editor      Delete saved
                                                                                                  analysis

  `POST`            `/projects/{project_id}/analyses/{analysis_id}/snapshots`   Owner/editor      Create
                                                                                                  reproducibility
                                                                                                  snapshot

  `GET`             `/projects/{project_id}/analyses/{analysis_id}/snapshots`   Project member    List snapshots
  -----------------------------------------------------------------------------------------------------------------

Membership-management endpoints can be added when collaboration is
implemented. They must enforce owner-only invitations and role changes.

### 6.7 Exports

  -----------------------------------------------------------------------------------------
  Method            Endpoint                          Auth                Purpose
  ----------------- --------------------------------- ------------------- -----------------
  `POST`            `/exports`                        Member/researcher   Create
                                                                          asynchronous
                                                                          export

  `GET`             `/exports/{export_id}`            Request owner/admin Check export
                                                                          status

  `GET`             `/exports/{export_id}/download`   Request owner/admin Download
                                                                          completed export

  `DELETE`          `/exports/{export_id}`            Request owner/admin Cancel queued
                                                                          export or revoke
                                                                          artifact
  -----------------------------------------------------------------------------------------

### 6.8 Administration

  --------------------------------------------------------------------------------------------------------
  Method            Endpoint                                    Auth              Purpose
  ----------------- ------------------------------------------- ----------------- ------------------------
  `GET`             `/admin/games`                              Admin             List catalog records and
                                                                                  indexing status

  `POST`            `/admin/games`                              Admin             Add a game to controlled
                                                                                  catalog

  `PATCH`           `/admin/games/{game_id}`                    Admin             Update catalog/indexing
                                                                                  state

  `POST`            `/admin/games/{game_id}/metadata-refresh`   Admin             Queue metadata refresh

  `POST`            `/admin/games/{game_id}/ingestion-jobs`     Admin             Queue
                                                                                  historical/incremental
                                                                                  collection

  `GET`             `/admin/ingestion-jobs`                     Admin             List collection jobs

  `GET`             `/admin/ingestion-jobs/{job_id}`            Admin             Job detail and counters

  `POST`            `/admin/ingestion-jobs/{job_id}/cancel`     Admin             Cancel a cancellable job

  `POST`            `/admin/ingestion-jobs/{job_id}/retry`      Admin             Retry a recoverable
                                                                                  failed/partial job

  `GET`             `/admin/pipeline-runs`                      Admin             List NLP/aggregation
                                                                                  runs

  `GET`             `/admin/pipeline-runs/{run_id}`             Admin             Pipeline detail

  `GET`             `/admin/models`                             Admin             List registered models

  `POST`            `/admin/models/{model_id}/activate`         Admin             Activate approved model
                                                                                  version
  --------------------------------------------------------------------------------------------------------

Administrative endpoints must be absent from guest navigation and
protected by server-side authorization regardless of route
discoverability.

------------------------------------------------------------------------

## 7. Endpoint contracts

The schemas below are conceptual API contracts. Implement them as
Pydantic request/response models and publish them through FastAPI
OpenAPI. UUIDs and example values are illustrative.

### 7.1 `GET /games`

Search and list indexed games.

**Query parameters**

  ------------------------------------------------------------------------------
  Parameter          Type                          Required Rules
  ------------------ ---------------- --------------------- --------------------
  `q`                string                              No Search game name;
                                                            all-digit values
                                                            also match
                                                            `steam_app_id`
                                                            exactly; bounded
                                                            length

  `genre`            string                              No Exact supported
                                                            genre filter (see
                                                            `GET /games/genres`)

  `catalog_status`   string                              No `indexed` (default)
                                                            or `pending`;
                                                            ignored when
                                                            `upcoming=true`

  `is_free`          boolean                             No Free-to-play filter

  `year_from`        integer                             No Release year lower
                                                            bound (1970-2100)

  `year_to`          integer                             No Release year upper
                                                            bound, inclusive

  `upcoming`         boolean                             No Only games whose
                                                            `release_date` is
                                                            after today; covers
                                                            `indexed` and
                                                            `pending`

  `limit`            integer                             No Default 20, max 100

  `cursor`           string                              No Opaque cursor

  `sort`             string                              No `name_asc`,
                                                            `name_desc`,
                                                            `recently_updated`,
                                                            `release_desc`,
                                                            `release_asc`
                                                            (release sorts omit
                                                            undated games)
  ------------------------------------------------------------------------------

**Response `200`**

``` json
{
  "data": [
    {
      "id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
      "steam_app_id": 123456,
      "name": "Example Game",
      "header_image_url": "https://example.invalid/header.jpg",
      "developers": ["Example Studio"],
      "genres": ["Action", "RPG"],
      "release_date": "2024-05-01",
      "is_free": false,
      "catalog_status": "indexed",
      "is_active": true,
      "review_count": 1200,
      "steam_positive_percentage": 87.5,
      "model_sentiment_positive_rate": 0.8123
    }
  ],
  "meta": {
    "request_id": "req_example",
    "pagination": {
      "limit": 20,
      "has_more": false,
      "next_cursor": null
    }
  }
}
```

Public endpoint behavior: - Only publicly indexed/active games are
returned. - Internal indexing failures and administrative notes are not
exposed. - `steam_app_id` is a public Steam application identifier, not
a user identifier. - `steam_positive_percentage` (0-100) and
`model_sentiment_positive_rate` (0-1) are computed over stored reviews
and are `null` when no votes / classifications exist.

### 7.1a `GET /games/genres`

Distinct genre labels across publicly indexed games, sorted
alphabetically. Response `data` is `string[]`, e.g.
`["Action", "Indie", "RPG"]`.

### 7.2 `GET /games/{game_id}`

Returns public game metadata.

Response data fields: - `id` - `steam_app_id` - `name` -
`short_description` - `header_image_url` - `developers` - `publishers` -
`genres` - `categories` - `release_date` - `is_free` - `data_coverage`

`data_coverage` should include the latest collection timestamp, number
of stored reviews, and supported language scope where known. Do not
imply complete Steam review coverage when SteamScoop only holds a
sample.

### 7.3 `GET /games/{game_id}/overview`

Returns the main summary card and collection coverage.

**Query parameters** - `model_version` (optional; defaults to currently
published model set) - `from` (optional date) - `to` (optional date)

**Response data**

``` json
{
  "data": {
    "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "review_count": 4200,
    "steam_recommendation": {
      "recommended_count": 3300,
      "not_recommended_count": 900,
      "positive_rate": 0.7857
    },
    "model_sentiment": {
      "positive_count": 2800,
      "negative_count": 1100,
      "neutral_count": 200,
      "unclassified_count": 100,
      "positive_rate": 0.6829,
      "model_version": "1.0.0"
    },
    "coverage": {
      "collected_at": "2026-11-01T02:00:00Z",
      "sampled": true,
      "language_scope": ["all"],
      "collection_policy": "weekly_hybrid_sample"
    }
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

The example numbers are illustrative. Define the denominator for each
rate in implementation and expose it in methodology. `positive_rate` for
model sentiment should exclude neutral and unclassified records if that
is the published formula; the formula must be consistent across
endpoints.

### 7.4 `GET /games/{game_id}/analytics`

Returns time-bucketed aggregates.

**Query parameters** - `period`: `day`, `week`, or `month`; default
`week`. - `from`: inclusive date. - `to`: exclusive date. -
`model_version`: optional published model version key.

**Response data**

``` json
{
  "data": {
    "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "period": "week",
    "model_version": "sentiment-1.0.0",
    "points": [
      {
        "period_start": "2026-10-05",
        "period_end": "2026-10-12",
        "review_count": 120,
        "positive_count": 80,
        "negative_count": 30,
        "neutral_count": 10,
        "steam_recommended_count": 92,
        "steam_not_recommended_count": 28
      }
    ]
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

Rules: - `period_end` is exclusive. - Missing buckets should either be
omitted or returned with zero counts; choose one policy and keep it
consistent. - Model version must be explicit in response metadata. - A
trend is descriptive, not causal.

### 7.5 `GET /games/{game_id}/sentiment`

Returns sentiment distribution and optionally time series.

Query parameters: - `from`, `to` - `model_version` - `include_trend`
(boolean, default false)

Response includes: - counts by `positive`, `negative`, `neutral`, and
`unclassified`; - denominator and coverage; - model key/version; -
optional time-series points.

Do not return only percentages; include counts and denominator so users
can interpret sample size.

### 7.6 `GET /games/{game_id}/aspects`

Returns aspect-level counts and sentiment.

Query parameters: - `from`, `to` - `model_version` - `limit` (default
20, max 100) - `sort`: `mentions_desc`, `negative_rate_desc`,
`positive_rate_desc`

Response data:

``` json
{
  "data": {
    "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "taxonomy_version": "aspects-1.0",
    "aspects": [
      {
        "aspect_key": "performance",
        "display_name": "Performance & Stability",
        "mention_count": 540,
        "positive_count": 70,
        "negative_count": 410,
        "neutral_count": 60,
        "negative_rate": 0.7593
      }
    ],
    "model_version": "absa-1.0.0"
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

The example values are illustrative. Rates must specify their
denominator in methodology.

### 7.7 `GET /games/{game_id}/topics`

Returns topic summaries.

Query parameters: - `model_version` (required if multiple incompatible
topic models are published; otherwise defaults to current) - `limit`
(default 20, max 100) - `include_outliers` (default false)

Response fields: - topic ID/key; - label and description; -
representative terms; - review count and prevalence; - outlier flag; -
topic model version; - corpus scope and generation time.

Topic IDs are version-specific. Clients must not assume topic ID
continuity across model releases.

### 7.8 `GET /games/{game_id}/reviews`

Paginated review explorer.

**Query parameters**

  -----------------------------------------------------------------------
  Parameter               Type                    Rules
  ----------------------- ----------------------- -----------------------
  `limit`                 integer                 Default 20, max 100

  `cursor`                string                  Opaque

  `language`              string                  Optional language code

  `steam_recommended`     boolean                 Filters Steam
                                                  `voted_up`

  `sentiment`             string                  `positive`, `negative`,
                                                  `neutral`,
                                                  `unclassified`

  `aspect`                string                  Aspect key

  `topic_id`              UUID                    Topic ID from selected
                                                  model version

  `from`                  timestamp/date          Inclusive

  `to`                    timestamp/date          Exclusive

  `sort`                  string                  `created_at_desc`,
                                                  `created_at_asc`,
                                                  `votes_up_desc`

  `model_version`         string                  Required when a filter
                                                  depends on a
                                                  non-default model
  -----------------------------------------------------------------------

**Response data**

``` json
{
  "data": [
    {
      "id": "0a2e1b1e-59f5-4e7f-9bd0-2f0d4f2f2e1a",
      "steam_review_id": "76561190000000000",
      "review_text": "Example review text.",
      "language": "english",
      "voted_up": true,
      "votes_up": 14,
      "steam_created_at": "2026-10-12T10:30:00Z",
      "sentiment": {
        "label": "positive",
        "confidence": 0.91,
        "model_version": "1.0.0"
      }
    }
  ],
  "meta": {
    "request_id": "req_example",
    "pagination": {
      "limit": 20,
      "has_more": true,
      "next_cursor": "opaque_cursor_value"
    }
  }
}
```

Important: - `steam_review_id` is a review identifier, not a Steam
account identifier. - Never expose SteamID, author profile, avatar, or
other unnecessary author metadata. - Review text is untrusted
user-generated content. Render it as text, not trusted HTML. - If the
requested sentiment/model output is unavailable, return a documented
null prediction or filter behavior; do not silently substitute a
different model version.

### 7.9 `GET /reviews/{review_id}`

Returns one review and source metadata that is approved for public
display.

Response includes: - review ID; - game ID; - review text; - language; -
Steam recommendation flag; - helpful/funny vote counts; - review
timestamp; - collection timestamp; - source and coverage notes.

Do not expose private author information or raw source payload.

### 7.10 `GET /reviews/{review_id}/intelligence`

Returns all currently published intelligence for a review.

Response data:

``` json
{
  "data": {
    "review_id": "0a2e1b1e-59f5-4e7f-9bd0-2f0d4f2f2e1a",
    "sentiment": {
      "label": "mixed",
      "confidence": 0.78,
      "model_version": "sentiment-1.0.0"
    },
    "aspects": [
      {
        "aspect_key": "gameplay",
        "sentiment": "positive",
        "confidence": 0.94
      },
      {
        "aspect_key": "performance",
        "sentiment": "negative",
        "confidence": 0.89
      }
    ],
    "topics": [
      {
        "topic_id": "6b54c7ac-21a4-4f62-a9a3-5e6d5e4f9a10",
        "label": "Performance issues",
        "score": 0.82,
        "model_version": "topic-1.0.0"
      }
    ]
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

The sentiment example above uses `mixed`, which is not part of the
default three-class sentiment contract. Production responses must use
the label schema declared by the selected model. If mixed sentiment is
needed, add it through a deliberate schema/version change; otherwise
represent mixed opinions through aspect outputs and a documented overall
label policy.

### 7.11 `POST /comparisons`

Compares two to five indexed games using a bounded, read-only request.

**Request**

``` json
{
  "game_ids": [
    "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "0a2e1b1e-59f5-4e7f-9bd0-2f0d4f2f2e1a"
  ],
  "period": {
    "from": "2026-01-01",
    "to": "2026-11-01"
  },
  "metrics": [
    "review_volume",
    "steam_recommendation",
    "model_sentiment",
    "aspect_sentiment"
  ],
  "model_version": "published-model-set-1"
}
```

**Response `200`**

``` json
{
  "data": {
    "games": [
      {
        "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
        "name": "Example Game",
        "review_volume": 4200,
        "steam_recommendation_rate": 0.78,
        "model_positive_rate": 0.71
      }
    ],
    "period": {
      "from": "2026-01-01",
      "to": "2026-11-01"
    },
    "model_version": "published-model-set-1"
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

Validation: - `game_ids` must contain 2--5 unique IDs. - Every game must
be publicly indexed. - `metrics` must contain only allowlisted metric
keys. - Maximum date range is configurable. - Return `422` for invalid
combinations and `404` if a requested game is not available. - The
response must indicate missing metric coverage rather than treating
missing data as zero.

### 7.12 `GET /methodology`

Returns: - collection method and date; - hybrid sampling policy; -
historical sample target and temporal bucket policy; - weekly refresh
policy; - review filters and language scope; - known coverage
limitations; - definitions of Steam recommendation and model
sentiment; - data retention and export notes.

The values must reflect the actual active configuration, not hard-coded
aspirational policy.

### 7.13 `GET /methodology/models`

Returns public model cards: - model key and version; - task; - supported
languages; - label schema; - evaluation dataset version; - headline
metrics and per-class metric links where published; -
training/evaluation date; - known limitations; - status (`active` or
`deprecated`).

Do not expose private artifact URIs, training secrets, or internal
filesystem paths.

### 7.14 `GET /methodology/datasets`

Returns dataset documentation: - dataset identifier/version; - source
and collection window; - sample policy; - language scope; - annotation
process; - inclusion/exclusion rules; - limitations; - access/export
policy.

Do not expose restricted training examples or annotator personal data.

------------------------------------------------------------------------

## 8. Authentication endpoint contracts

These endpoints are optional and should be enabled only when account
functionality is implemented.

### 8.1 `POST /auth/register`

Request:

``` json
{
  "email": "user@example.com",
  "password": "Strong-password-example",
  "display_name": "Researcher"
}
```

Response `201`:

``` json
{
  "data": {
    "id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "email": "user@example.com",
    "display_name": "Researcher",
    "status": "pending"
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

Requirements: - Validate email and password policy. - Hash passwords
using Argon2id. - Never return password hashes. - Apply registration
abuse protection. - Email verification policy must be explicit before
enabling registration. - Do not reveal whether an email exists through
overly detailed error messages.

### 8.2 `POST /auth/login`

Request:

``` json
{
  "email": "user@example.com",
  "password": "Strong-password-example"
}
```

Response `200`: - Set secure session cookie. - Return user profile and
roles in `data`. - Do not return password hash or session secret in
JSON.

Invalid credentials return a generic `401 INVALID_CREDENTIALS`.

### 8.3 `POST /auth/logout`

Invalidates the current session and clears the cookie. Return `204`.

### 8.4 `GET /auth/me`

Returns the current authenticated user's ID, email, display name,
account status, and role keys.

------------------------------------------------------------------------

## 9. Research workspace contracts

### 9.1 `POST /projects`

Request:

``` json
{
  "name": "Action RPG Review Study",
  "description": "Compare player feedback across selected games.",
  "visibility": "private"
}
```

Response `201` returns the created project and owner identity.

### 9.2 `GET /projects`

Returns only projects the current user is authorized to view. Supports
cursor pagination.

### 9.3 `PATCH /projects/{project_id}`

Accepts partial updates to `name`, `description`, and `visibility`.
Unknown fields are rejected.

### 9.4 `POST /projects/{project_id}/games`

Request:

``` json
{
  "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a"
}
```

Duplicate association returns `409 RESOURCE_ALREADY_EXISTS` or an
idempotent `200`; choose one policy and document it. Recommended
behavior for this resource is idempotent success.

### 9.5 Saved analysis

Request:

``` json
{
  "name": "Negative performance feedback",
  "description": "Find performance-related negative reviews.",
  "analysis_type": "review_explorer",
  "query_config": {
    "game_ids": ["9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a"],
    "aspect": "performance",
    "sentiment": "negative",
    "period": {
      "from": "2026-01-01",
      "to": "2026-11-01"
    },
    "model_version": "published-model-set-1"
  }
}
```

The server validates `query_config` against an allowlisted schema for
`analysis_type`. Do not accept arbitrary SQL, ORM expressions, or raw
query fragments.

### 9.6 Analysis snapshots

A snapshot captures: - exact filters and selected games; - data cutoff
time; - model versions and taxonomy versions; - aggregate/result
summary; - optional artifact reference.

Snapshots are immutable. Updating the saved analysis configuration
creates no implicit mutation of previous snapshots.

------------------------------------------------------------------------

## 10. Export API contracts

### 10.1 `POST /exports`

Exports are asynchronous.

Request:

``` json
{
  "format": "csv",
  "scope": {
    "type": "game_reviews",
    "game_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a"
  },
  "filters": {
    "language": "english",
    "sentiment": "negative",
    "from": "2026-01-01",
    "to": "2026-11-01"
  },
  "fields": [
    "review_text",
    "language",
    "voted_up",
    "steam_created_at",
    "sentiment"
  ]
}
```

Response `202`:

``` json
{
  "data": {
    "export_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "status": "queued",
    "created_at": "2026-11-08T09:00:00Z"
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

### 10.2 `GET /exports/{export_id}`

Response includes: - `export_id`; - `status`: `queued`, `running`,
`succeeded`, `failed`, `expired`, `cancelled`; - `row_count` when
available; - `created_at`, `finished_at`, `expires_at`; - sanitized
error code if failed.

### 10.3 `GET /exports/{export_id}/download`

-   Only the requester or authorized administrator can download.
-   The artifact must be stored privately.
-   Use a short-lived signed download URL or stream through the API.
-   Expired artifacts return `410 EXPORT_EXPIRED`.
-   The response must not expose permanent storage credentials or bucket
    internals.

### 10.4 Export safeguards

-   Enforce role-specific row limits.
-   Enforce maximum date range and concurrent export count.
-   Apply field allowlists.
-   Exclude Steam account identifiers and unnecessary author data.
-   Include a methodology/provenance manifest where appropriate.
-   Audit export creation and administrative access.
-   Public/anonymous export, if enabled, must be separately bounded and
    rate-limited.

------------------------------------------------------------------------

## 11. Administrative API contracts

### 11.1 `POST /admin/games/{game_id}/ingestion-jobs`

Request:

``` json
{
  "job_type": "incremental",
  "collection_config": {
    "review_type": "all",
    "purchase_type": "all",
    "languages": ["all"],
    "overlap_days": 14
  },
  "reason": "Scheduled recovery after upstream interruption."
}
```

Response `202`:

``` json
{
  "data": {
    "job_id": "9bb4b74d-52d2-4d70-9d2e-c9d23a7f2c6a",
    "game_id": "0a2e1b1e-59f5-4e7f-9bd0-2f0d4f2f2e1a",
    "job_type": "incremental",
    "status": "queued"
  },
  "meta": {
    "request_id": "req_example"
  }
}
```

Rules: - `job_type` is `historical` or `incremental`. - Collection
configuration is validated against backend policy. - Public users cannot
call this endpoint. - The endpoint queues work; it does not
synchronously collect reviews. - Active-job conflicts return
`409 ACTIVE_JOB_EXISTS`. - Do not accept arbitrary upstream URLs or
arbitrary API parameters from the client.

### 11.2 `GET /admin/ingestion-jobs`

Supports filters: - `status`; - `job_type`; - `game_id`; - `from`,
`to`; - cursor pagination.

### 11.3 `POST /admin/ingestion-jobs/{job_id}/retry`

Only failed or recoverable partial jobs can be retried. The backend must
verify checkpoint state and idempotency before enqueueing. Return `202`
with the job state or a new retry job ID, according to the chosen
job-history policy.

### 11.4 Model activation

`POST /admin/models/{model_id}/activate` must: - require admin
authorization; - verify model approval status; - verify task
compatibility and required artifacts; - record the actor and activation
event; - avoid changing historical predictions; - update the active
model selection atomically.

------------------------------------------------------------------------

## 12. Error handling specification

### 12.1 Error codes

  -------------------------------------------------------------------------------
  Code                                                 HTTP Meaning
  ---------------------------- ---------------------------- ---------------------
  `VALIDATION_ERROR`                                    422 Field or semantic
                                                            validation failed

  `MALFORMED_REQUEST`                                   400 Invalid JSON or
                                                            request encoding

  `INVALID_CURSOR`                                      400 Cursor malformed or
                                                            incompatible

  `CURSOR_EXPIRED`                                      400 Cursor no longer
                                                            valid

  `UNAUTHENTICATED`                                     401 Authentication
                                                            required

  `INVALID_CREDENTIALS`                                 401 Login failed

  `FORBIDDEN`                                           403 Insufficient
                                                            permission

  `RESOURCE_NOT_FOUND`                                  404 Resource unavailable

  `FEATURE_DISABLED`                                    404 Optional feature not
                                                            enabled

  `RESOURCE_ALREADY_EXISTS`                             409 Duplicate resource

  `ACTIVE_JOB_EXISTS`                                   409 Conflicting active
                                                            ingestion job

  `INVALID_STATE_TRANSITION`                            409 Operation not allowed
                                                            in current state

  `RATE_LIMITED`                                        429 Request quota
                                                            exceeded

  `PAYLOAD_TOO_LARGE`                                   413 Request exceeds
                                                            configured limit

  `UPSTREAM_TIMEOUT`                                    504 Upstream dependency
                                                            timed out

  `UPSTREAM_UNAVAILABLE`                                502 Upstream service
                                                            failed

  `SERVICE_UNAVAILABLE`                                 503 Service temporarily
                                                            unavailable

  `EXPORT_EXPIRED`                                      410 Export artifact
                                                            expired

  `INTERNAL_ERROR`                                      500 Unexpected server
                                                            error
  -------------------------------------------------------------------------------

### 12.2 Validation errors

Return field-specific details without exposing internal validator
traces.

Example:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "details": [
      {
        "field": "game_ids",
        "issue": "Provide between 2 and 5 unique game IDs."
      }
    ],
    "request_id": "req_example"
  }
}
```

### 12.3 Upstream Steam errors

Steam API failures must be translated into stable application errors: -
`429` from Steam: respect `Retry-After` if present; use bounded
backoff. - Timeout: retry according to job policy. - Invalid response
schema: record an upstream schema error and stop unsafe processing. -
Upstream unavailable: mark the batch/job appropriately. - Do not return
raw Steam response bodies to public clients.

Public analytics endpoints should normally serve the latest committed
dataset even if the latest background collection failed. Collection
failure must not make read-only analytics unavailable unless the
database/read service itself is unavailable.

### 12.4 Internal errors

-   Return generic `INTERNAL_ERROR`.
-   Log stack trace server-side with request ID.
-   Redact tokens, passwords, API keys, review text where not needed,
    and private user data.
-   Never expose SQL, filesystem paths, environment variables, or
    tracebacks.

------------------------------------------------------------------------

## 13. Rate limiting and abuse prevention

Apply limits by endpoint class and identity:

  Class                      Suggested policy
  -------------------------- ----------------------------------------
  Public game/search reads   Moderate per-IP and per-route limit
  Public analytics reads     Separate quota; cache common responses
  Review explorer            Bounded page size and query complexity
  Authentication             Strict per-IP/account attempt limits
  Workspace mutations        Per-user quota
  Exports                    Role-based concurrent and daily quotas
  Admin endpoints            Low-volume, privileged access only

Exact numerical limits should be set after load testing and deployment
topology are known. Do not treat these initial policies as universal
fixed values.

Return: - `429 RATE_LIMITED`; - `Retry-After` where possible; - optional
`RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset` headers
according to the chosen standard.

Do not rely only on IP address for authenticated quotas. Use user
identity and route class as appropriate.

------------------------------------------------------------------------

## 14. Caching and consistency

### 14.1 Cacheable endpoints

Potentially cache: - game catalog search; - game details; - game
overview; - aggregate analytics; - methodology and model cards.

Review pages may be cached briefly if cache keys include filters, sort,
cursor, and model version.

### 14.2 Cache headers

Use appropriate: - `Cache-Control`; - `ETag`; - `Last-Modified`.

Do not publicly cache private workspace, account, export-status, or
administrative responses.

### 14.3 Consistency contract

-   Review ingestion and NLP inference are asynchronous.
-   Public analytics reflect the latest successfully committed
    aggregate, not necessarily the newest source review.
-   Responses should expose `data_cutoff_at` or `computed_at` when
    freshness matters.
-   A successful ingestion job does not imply NLP predictions or
    aggregates have already been refreshed.
-   If the UI needs end-to-end freshness, expose separate collection and
    analytics timestamps.

------------------------------------------------------------------------

## 15. API security requirements

1.  Validate path, query, and body inputs with Pydantic.
2.  Use parameterized SQL/ORM queries.
3.  Apply request body and query length limits.
4.  Use allowlists for sort keys, filter keys, fields, and export
    formats.
5.  Enforce object-level authorization on project, analysis, snapshot,
    and export resources.
6.  Use secure session handling and CSRF protection where cookies
    authenticate mutations.
7.  Restrict CORS to approved origins.
8.  Apply rate limits and abuse controls.
9.  Redact secrets and personal data from logs.
10. Treat review text and external metadata as untrusted content.
11. Do not return private author metadata.
12. Audit sensitive administrative operations and export actions.
13. Use TLS in production.
14. Keep API and Steam publisher keys server-side.
15. Validate all asynchronous job state transitions.

------------------------------------------------------------------------

## 16. OpenAPI and contract management

FastAPI should generate the OpenAPI document from explicit Pydantic
request and response models.

Requirements: - Every endpoint has a summary, description, tags,
response codes, and examples. - Request and response models are
separate; do not serialize ORM entities directly. - Mark
sensitive/internal fields as excluded. - Document enum values and
constraints. - Document authentication requirements per route. - Include
reusable error response schemas. - Add examples for cursor pagination
and asynchronous job responses. - Keep the generated OpenAPI document in
CI as a reviewable artifact. - Detect breaking schema changes in pull
requests.

### 16.1 Contract tests

For every endpoint, test: - success response schema; - required and
optional fields; - invalid input behavior; - authentication and
authorization; - pagination determinism; - filter and sort validation; -
not-found behavior; - rate-limit behavior where practical; - error
envelope consistency.

For asynchronous endpoints, test: - initial `202` response; - status
lifecycle; - duplicate submission behavior; - retry and cancellation
rules; - artifact expiry and authorization.

### 16.2 Backward compatibility

Non-breaking changes: - adding optional response fields; - adding a new
endpoint; - adding a new optional query parameter; - adding a new enum
value only when clients are designed to tolerate unknown values.

Potentially breaking changes: - removing or renaming fields; - changing
field types; - changing enum meaning; - changing pagination semantics; -
changing default filters or model version behavior; - changing
authentication requirements; - changing error codes or response
envelope.

For breaking changes, introduce `/api/v2` or provide a clearly
documented deprecation period.

### 16.3 Deprecation

When deprecating an endpoint or field: - publish a replacement; -
document migration instructions; - emit a deprecation response header
where appropriate; - communicate a removal date; - monitor usage before
removal.

------------------------------------------------------------------------

## 17. Suggested FastAPI project mapping

``` text
app/
├── main.py
├── api/
│   └── v1/
│       ├── router.py
│       └── endpoints/
│           ├── health.py
│           ├── games.py
│           ├── reviews.py
│           ├── comparisons.py
│           ├── methodology.py
│           ├── auth.py
│           ├── projects.py
│           ├── analyses.py
│           ├── exports.py
│           └── admin/
│               ├── games.py
│               ├── ingestion.py
│               └── models.py
├── schemas/
│   ├── common.py
│   ├── game.py
│   ├── review.py
│   ├── analytics.py
│   ├── comparison.py
│   ├── auth.py
│   ├── project.py
│   ├── export.py
│   └── admin.py
├── services/
├── repositories/
├── security/
├── integrations/
└── workers/
```

This is a suggested organization, not a requirement to create one
service per endpoint. Keep business logic in services and data access in
repositories; endpoint handlers should remain thin.

------------------------------------------------------------------------

## 18. MVP endpoint implementation priority

### Phase 1 --- Public analytics

1.  `GET /health`
2.  `GET /games`
3.  `GET /games/{game_id}`
4.  `GET /games/{game_id}/overview`
5.  `GET /games/{game_id}/analytics`
6.  `GET /games/{game_id}/reviews`
7.  `GET /reviews/{review_id}/intelligence`
8.  `GET /methodology`
9.  `GET /methodology/models`

### Phase 2 --- Intelligence expansion

1.  `GET /games/{game_id}/sentiment`
2.  `GET /games/{game_id}/aspects`
3.  `GET /games/{game_id}/topics`
4.  `POST /comparisons`
5.  `GET /methodology/datasets`

### Phase 3 --- Accounts and research

1.  Authentication endpoints
2.  Project CRUD
3.  Project game selection
4.  Saved analyses
5.  Analysis snapshots

### Phase 4 --- Exports and administration

1.  Export job lifecycle
2.  Admin catalog operations
3.  Admin ingestion operations
4.  Pipeline monitoring
5.  Model activation

The public read API should be usable before accounts, exports, and
administrative UI are complete.

------------------------------------------------------------------------

## 19. Traceability to system requirements

  -----------------------------------------------------------------------
  Requirement area                    API support
  ----------------------------------- -----------------------------------
  Public game discovery               `/games`

  Game intelligence dashboard         `/games/{id}/overview`,
                                      `/analytics`, `/sentiment`

  Review exploration                  `/games/{id}/reviews`,
                                      `/reviews/{id}`

  ABSA insights                       `/games/{id}/aspects`

  Topic intelligence                  `/games/{id}/topics`

  Game comparison                     `/comparisons`

  Research workspace                  `/projects`, `/analyses`,
                                      `/snapshots`

  Reproducibility                     `/methodology`,
                                      `/methodology/models`, snapshots

  Data export                         `/exports`

  Controlled collection               `/admin/.../ingestion-jobs`

  Model operations                    `/admin/models`,
                                      `/admin/pipeline-runs`

  Security and governance             Authentication, RBAC, audit, export
                                      controls
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 20. Final API contract summary

SteamScoop's API is a versioned FastAPI application interface with
public read-only analytics and optional authenticated research
capabilities.

The main contract boundaries are:

-   **Public read API:** indexed games, reviews, intelligence,
    comparisons, and methodology.
-   **Identity API:** optional account/session management.
-   **Research API:** private projects, saved analyses, and immutable
    snapshots.
-   **Export API:** asynchronous, quota-controlled export jobs.
-   **Admin API:** restricted catalog, ingestion, pipeline, and model
    operations.

The most important behavioral guarantees are: 1. Public reads never
trigger unbounded ingestion or model inference. 2. Expensive work
returns `202 Accepted` and exposes a durable job status. 3. Cursor
pagination is opaque, deterministic, and bounded. 4. Authentication and
object-level authorization are enforced server-side. 5. Errors use
stable machine-readable codes. 6. Analytics identify their data cutoff
and model versions. 7. Steam recommendation and ML sentiment remain
separate. 8. OpenAPI schemas and contract tests are maintained as part
of CI.

This specification is the proposed API baseline for implementation.
Before production, finalize exact rate limits, export quotas, account
activation policy, maximum date ranges, and any endpoint-specific
freshness guarantees.
