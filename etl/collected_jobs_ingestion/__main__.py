from __future__ import annotations

from pathlib import Path

from pymongo import MongoClient

from .ingest_collected_jobs import ingest_collected_jobs
from .mongo_repository import ensure_external_jobs_indexes

# TODO: not harcoded
MONGO_URI = "mongodb://external_jobs:external_jobs@localhost:27018/external_jobs"
DATABASE_NAME = "external_jobs"


def main() -> None:
    with MongoClient(MONGO_URI) as client:
        database = client[DATABASE_NAME]
        ensure_external_jobs_indexes(database)
        summary = ingest_collected_jobs(Path("collected_jobs"), database)

    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
