# Postgres Ingestion Plan

**Summary**
Build a first ingestion pipeline for already collected job data that validates external rows, enriches them with derived metadata, deduplicates by `platform + ejib`, and stores them in Postgres. Add the implementation plan to `ai_intents/README.md` before coding the pipeline.

**Key Changes**
- Add `ai_intents/README.md` describing this ingestion plan, schema, validation rules, and v1 limitations.
- Add `psycopg` as the Postgres client dependency and keep validation in Pydantic.
- Add a small ETL package for third-party jobs, source-agnostic naming throughout:
  - `ejib`: external job ID, stored as text.
  - `platform`: source platform, e.g. `linkedin`, stored as data, not baked into column names.
  - `search_term_used`: parsed from URL query `keywords`.
  - `date_collected`: inferred from collected file path date, e.g. `collected_jobs/2026-04-28/...`.
  - `description_language`: detected from `descr` using the existing `LanguageDetector`.
  - `location`: nullable best-effort job/company location extracted only from clear text patterns like `Location:` or `Based in`; otherwise `NULL`.
  - `salary`: nullable text; fill only from structured source data if present. Current collected files have no structured salary, so this will usually be `NULL`.

**Database Model**
- Create a `jobs` table:
  - `id BIGSERIAL PRIMARY KEY`
  - `platform TEXT NOT NULL`
  - `ejib TEXT NOT NULL`
  - `descr TEXT NOT NULL`
  - `location TEXT NULL`
  - `salary TEXT NULL`
  - `date_collected DATE NOT NULL`
  - `url TEXT NOT NULL`
  - `title TEXT NOT NULL`
  - `description_language TEXT NOT NULL`
  - `search_term_used TEXT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `UNIQUE(platform, ejib)`
- Create a narrow `external_job_ids` table for fast ID reads:
  - `platform TEXT NOT NULL`
  - `ejib TEXT NOT NULL`
  - `job_id BIGINT NOT NULL REFERENCES jobs(id)`
  - `first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `PRIMARY KEY(platform, ejib)`
  - index on `job_id`
- Use plain SQL schema files, not Alembic yet. Keep this simple and runnable against the existing Docker Postgres.

**Ingestion Behavior**
- Read all files under `collected_jobs/YYYY-MM-DD/*.{json,txt}`.
- Support both proper JSONL and older concatenated JSON-object files using `json.JSONDecoder.raw_decode`.
- Validate each source row with Pydantic:
  - required: `id`, `url`, `description`, `title`
  - `url` must be a valid URL
  - `description` and `title` must be non-empty after trimming
  - invalid rows are skipped and reported in an ingestion summary
- Transform source row to normalized job input:
  - `ejib = str(source.id)`
  - `descr = source.description`
  - `platform = parsed URL hostname mapped to a short platform value`, currently `linkedin`
  - `date_collected = folder date`
  - `search_term_used = keywords query param`
  - `description_language = LanguageDetector.detect(description).language`
- Insert with `ON CONFLICT(platform, ejib) DO UPDATE` so duplicates do not create new jobs.
- Upsert `external_job_ids` in the same transaction after the job upsert, updating `last_seen_at`.

**Tests**
- Unit tests for source parsing:
  - JSONL rows parse correctly.
  - Concatenated JSON rows parse correctly.
  - Bad rows are reported, not fatal.
- Unit tests for validation:
  - missing `id`, bad URL, empty title, and empty description fail validation.
  - valid collected rows produce normalized job input.
- Unit tests for derivation:
  - `date_collected` comes from the folder path.
  - `search_term_used` comes from URL `keywords`.
  - `platform` is source-agnostic and stored as a value, not column naming.
  - duplicates share the same `platform + ejib`.
- Integration-style Postgres test if practical:
  - insert a job, ingest duplicate, assert one row in `jobs`.
  - assert `external_job_ids` contains the ID and references the job row.
  - assert fast ID lookup can read from the narrow table.

**Assumptions**
- Use `psycopg` with plain SQL for v1.
- Keep `location` nullable and conservative; no AI extraction in this step.
- Keep `salary` nullable text; no regex salary extraction in this step.
- Use `platform + ejib` as the external uniqueness key.
- The first plan document should be `ai_intents/README.md`.
