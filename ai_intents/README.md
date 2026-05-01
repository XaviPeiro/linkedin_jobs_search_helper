# MongoDB Ingestion Plan

## Summary

Use MongoDB as the first durable store for already collected third-party job data. Jobs behave like external documents at this stage: fields are incomplete, extraction rules will evolve, and the main needs are validation, deduplication, basic search, and source-agnostic storage.

The ingestion pipeline will read the existing `collected_jobs` files, validate each external row, normalize the stable fields we already know we need, detect the description language, and upsert into a single MongoDB collection.

## Data Model

Collection: `external_jobs`

Each document should use source-agnostic naming:

```json
{
  "platform": "linkedin",
  "ejib": "4405535832",
  "raw_payload": {
    "id": 4405535832,
    "url": "https://www.linkedin.com/jobs/search/?currentJobId=4405535832...",
    "description": "...",
    "title": "..."
  },
  "normalized": {
    "title": "...",
    "descr": "...",
    "url": "...",
    "description_language": "en",
    "location": null,
    "salary": null,
    "search_term_used": "python engineer",
    "date_collected": "2026-04-29"
  },
  "created_at": "2026-04-30T00:00:00Z",
  "updated_at": "2026-04-30T00:00:00Z"
}
```

Definitions:

- `ejib`: external job ID, stored as text.
- `platform`: third-party source name, stored as data rather than encoded in column names.
- `raw_payload`: the original validated external row.
- `normalized`: current ETL output. This can evolve without migrations.
- `descr`: normalized job description text, copied from source `description`.
- `description_language`: detected from `descr` using the existing language detection ETL component.

## Indexes

Create these MongoDB indexes during app setup or ingestion bootstrap:

```javascript
db.external_jobs.createIndex(
  { platform: 1, ejib: 1 },
  { unique: true }
)

db.external_jobs.createIndex({ "normalized.description_language": 1 })

db.external_jobs.createIndex({ "normalized.search_term_used": 1 })

db.external_jobs.createIndex({
  "normalized.title": "text",
  "normalized.descr": "text"
})
```

Fast access to all external IDs should use the unique compound index:

```javascript
db.external_jobs.find(
  {},
  { platform: 1, ejib: 1, _id: 0 }
)
```

## Ingestion Behavior

Read all files under `collected_jobs/YYYY-MM-DD/*.{json,txt}`.

Support JSONL input: one JSON object per non-empty line.

Validate each source row with Pydantic before storing:

- `id` is required and becomes `ejib`.
- `url` is required and must be a valid URL.
- `description` is required and must be non-empty after trimming.
- `title` is required and must be non-empty after trimming.

Transform validated rows:

- `platform`: derived from URL host. For current data this maps to `linkedin`.
- `ejib`: `str(source.id)`.
- `normalized.title`: source `title`.
- `normalized.descr`: source `description`.
- `normalized.url`: source `url`.
- `normalized.description_language`: language detector result.
- `normalized.search_term_used`: URL query parameter `keywords`, if present.
- `normalized.date_collected`: date from the collected file path.
- `normalized.location`: nullable best-effort job/company location. Fill only from clear source data or obvious description patterns; otherwise `null`.
- `normalized.salary`: nullable text. Fill only from explicit structured source data when present; otherwise `null`.

Upsert by `{ platform, ejib }`:

- Insert new documents with `created_at` and `updated_at`.
- Update duplicate documents with the latest `raw_payload`, `normalized`, and `updated_at`.
- Never create duplicate jobs for the same `{ platform, ejib }`.

## Implementation Steps

1. Add MongoDB to Docker Compose and remove Postgres from the intended ingestion path.
2. Add `pymongo` as the MongoDB client dependency.
3. Add an ETL module for collected job ingestion:
   - parser for collected files
   - Pydantic source validation
   - source-to-normalized transformation
   - MongoDB repository/upsert logic
4. Add a small CLI entrypoint to ingest all collected files.
5. Add tests for parsing, validation, normalization, and dedup behavior.

## Test Plan

Parser tests:

- Parses JSONL files.
- Reports invalid JSON without stopping the whole ingestion run.

Validation tests:

- Accepts valid collected job rows.
- Rejects missing `id`.
- Rejects invalid `url`.
- Rejects empty `description`.
- Rejects empty `title`.

Normalization tests:

- Derives `platform` from URL host.
- Converts source `id` to string `ejib`.
- Extracts `search_term_used` from URL `keywords`.
- Extracts `date_collected` from the collected file path.
- Calls language detection and stores `description_language`.
- Leaves `location` and `salary` as `null` when not reliably present.

Mongo repository tests:

- Upserts a new job.
- Re-ingests the same `{ platform, ejib }` without creating a duplicate.
- Lists all `{ platform, ejib }` pairs using a projection backed by the compound index.

## Assumptions

- MongoDB is the durable store for v1 ingestion.
- Jobs are treated as independent third-party documents.
- We do not model companies, applications, evaluations, or relational workflows yet.
- MongoDB text search is enough for basic search in v1.
- If search ranking becomes a product-quality requirement, add Meilisearch or Typesense later.
- If semantic similarity becomes central, add a vector store later rather than forcing that responsibility into the first database choice.
