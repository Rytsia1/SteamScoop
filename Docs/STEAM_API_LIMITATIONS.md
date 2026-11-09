# Steam API Limitations & Unsupported Scenarios

> **Document Version:** 1.0.0  
> **Target Subsystem:** Steam API Integration Adapter (`apps/api/app/integrations/steam`)  
> **Upstream Endpoints:**  
> - Reviews: `https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/`  
> - Storefront Metadata: `https://store.steampowered.com/api/appdetails`  

---

## 1. Executive Summary

This document details the operational constraints, undocumented behaviors, rate-limiting characteristics, and failure modes of Valve's Steam Web API and Storefront endpoints identified during the implementation of the SteamScoop integration adapter.

---

## 2. Review API (`IUserReviewsService/GetAppReviews/v1/`)

### 2.1 Pagination Mechanics & Cursor Looping
* **Page Size Cap**: The maximum page size supported by Steam is **100 reviews per request** (`num_per_page: 100`). Requesting larger values is clamped to 100 by Valve's servers.
* **Initial Cursor**: Ingestion begins with `cursor: "*"`.
* **No `has_more` Boolean**: Steam does not provide a boolean flag indicating whether more pages exist.
* **Cursor Looping on Stream Termination**: When the end of available reviews is reached, Steam does **not** return `null` or an empty cursor. Instead, it returns:
  1. An empty reviews array (`reviews: []`), or
  2. The exact same cursor string received in the request.
  * **Adapter Mitigation**: The `ReviewPage` normalizer detects when `new_cursor == current_cursor` or `len(reviews) == 0` and deterministically sets `has_more = False` to prevent infinite pagination loops.
* **Cursor Encoding**: Cursors are URL-safe base64 strings that may contain `+`, `/`, and `=` characters. When passing via `input_json`, standard JSON string encoding preserves them safely.

### 2.2 Historical Traversal Limits
* **Finite Traversal Window**: For games with massive review corpora (e.g. >500,000 reviews such as *Counter-Strike 2*, *Dota 2*, or *PUBG*), Steam's cursor pagination does **not** allow infinite backwards traversal to the beginning of time. Requests typically time out or return empty results after several thousand pages.
* **Sampling Requirement**: SteamScoop must rely on bounded weekly sampling policies and temporal partitions rather than assuming complete review extraction for high-volume games.
* **Date Range Constraints**: `date_range_start` and `date_range_end` parameters are supported only when **both** boundaries are provided as Unix epoch timestamps. Steam's backend indexing may still omit sporadic historical records across wide historical windows.

### 2.3 Filter Parameter Semantics
* `filter: 1` (**Recent**): Sorts reviews by creation timestamp descending (`steam_created_at DESC`). This is the canonical filter for historical traversal and backfills.
* `filter: 2` (**Updated**): Sorts reviews by last edit timestamp descending (`steam_updated_at DESC`). This is required for incremental sync runs to capture edited reviews without re-reading the entire catalog.
* `filter: 0` (**All / Summary**): Designed for summary cards; sequential cursor traversal is unreliable under filter 0.

### 2.4 User Data & Privacy Protection
* **Author PII**: Steam review objects include an `author` payload containing `steamid`, `num_games_owned`, and `last_played`.
* **Enforced Redaction**: SteamScoop strictly strips `steamid` and author profile information at the adapter boundary (`NormalizedReview`). Only gameplay metadata relevant to analytics (`playtime_forever`, `playtime_at_review`, `playtime_last_two_weeks`) is retained.
* **Whitespace-Only Reviews**: Steam allows players to submit empty review text (e.g. pure whitespace or recommendations without comments). The adapter filters these out prior to persistence to uphold database integrity (`ck_review_text_not_empty`).

---

## 3. Storefront Metadata API (`store.steampowered.com/api/appdetails`)

### 3.1 Rate Limiting Asymmetry
* The Storefront API enforces significantly more aggressive rate limits than the Steamworks Web API.
* Repeated unauthenticated calls from cloud hosting IP ranges (AWS, GCP, Azure) are quickly throttled with HTTP 429.
* **Adapter Mitigation**: Ingestion workers must stagger store metadata refreshes separately from review ingestion batches.

### 3.2 Non-Standard Error Formats
* **HTTP 200 for Missing Resources**: When an App ID does not exist, is region-locked, or has been delisted, Steam returns an HTTP 200 OK with `{"<appid>": {"success": false}}`.
* **Adapter Mitigation**: The normalizer inspects `payload[str(app_id)]["success"]` and raises `SteamGameUnavailableError` (mapped to internal HTTP 404) rather than treating it as a successful response.

### 3.3 Date String Diversity
* Release dates in `data.release_date.date` are unstandardized strings formatted according to the requested locale (`l=english`):
  - `"17 Sep, 2020"` (`%d %b, %Y`)
  - `"Sep 17, 2020"` (`%b %d, %Y`)
  - `"2020-09-17"` (`%Y-%m-%d`)
  - `"September 2020"` (`%B %Y`)
  - `"Coming Soon"` / `"To be announced"` (Unreleased)
* **Adapter Mitigation**: Multi-pattern parsing in `parse_steam_release_date()` attempts standard date formats, falls back to Month-Year date representation (1st of the month), and gracefully returns `None` for unreleased or placeholder titles.

---

## 4. Upstream Reliability & Transport Policies

### 4.1 Transient Failures & Tuesday Maintenance
* Valve conducts routine Steam server maintenance on Tuesdays (~16:00 to 18:00 Pacific Time). During this window, Web API endpoints frequently return HTTP 500, 502, 503, or 504, or terminate TCP connections abruptly.
* **Adapter Policy**: The transport layer treats 5xx codes and socket timeouts as temporary upstream errors, executing bounded exponential backoff with jitter across 3 retries before bubbling `SteamTemporaryServerError`.

### 4.2 Rate Limit Handling (HTTP 429)
* When rate-limited, Steam sometimes returns a `Retry-After` header (seconds or RFC 2822 date).
* If `Retry-After` is missing or invalid, exponential backoff is applied.
* If `Retry-After` exceeds the bounded maximum (`max_retry_after_seconds = 30.0`), the adapter aborts immediately with `SteamRateLimitError` to avoid holding worker threads or database connections hostage.

### 4.3 Security & Credential Protection
* Steam API keys (`STEAM_API_KEY`) must never appear in application logs or exception representations.
* The transport sanitizes all logged request URLs using regex masking (`sanitize_url()`), replacing `key=...` with `key=[REDACTED]`.
* Direct frontend access to Steam endpoints is prohibited; all communication passes through background worker adapters.

