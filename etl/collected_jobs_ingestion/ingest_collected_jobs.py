from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from pymongo.database import Database

from .collected_jobs_parser import iter_collected_job_files, iter_json_objects
from .models import IngestionSummary
from .mongo_repository import ExternalJobsRepository
from .normalizer import normalize_external_job


def ingest_collected_jobs(
    collected_jobs_root: Path,
    database: Database,
) -> IngestionSummary:
    repository = ExternalJobsRepository(database)
    summary = IngestionSummary()

    for path in iter_collected_job_files(collected_jobs_root):
        summary.files_seen += 1
        try:
            raw_jobs = list(iter_json_objects(path.read_text()))
        except (json.JSONDecodeError, ValueError) as exc:
            summary.rejected_rows += 1
            summary.errors.append(f"{path}: {exc}")
            continue

        for raw_job in raw_jobs:
            summary.rows_seen += 1
            try:
                document = normalize_external_job(path, raw_job)
            except ValidationError as exc:
                summary.rejected_rows += 1
                summary.errors.append(f"{path}: {exc}")
                continue

            was_inserted = repository.upsert(document)
            if was_inserted:
                summary.inserted_rows += 1
            else:
                summary.updated_rows += 1

    return summary
