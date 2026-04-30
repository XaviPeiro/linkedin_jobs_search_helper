from __future__ import annotations

from pymongo import ASCENDING, TEXT, ReturnDocument
from pymongo.database import Database

from .models import ExternalJobDocument


COLLECTION_NAME = "external_jobs"


def ensure_external_jobs_indexes(
    database: Database,
    collection_name: str = COLLECTION_NAME,
) -> None:
    collection = database[collection_name]
    collection.create_index(
        [("platform", ASCENDING), ("ejib", ASCENDING)],
        unique=True,
        name="external_jobs_platform_ejib_unique",
    )
    collection.create_index(
        [("normalized.description_language", ASCENDING)],
        name="external_jobs_description_language",
    )
    collection.create_index(
        [("normalized.search_term_used", ASCENDING)],
        name="external_jobs_search_term_used",
    )
    collection.create_index(
        [("normalized.title", TEXT), ("normalized.descr", TEXT)],
        name="external_jobs_text_search",
    )


class ExternalJobsRepository:
    def __init__(
        self,
        database: Database,
        collection_name: str = COLLECTION_NAME,
    ):
        self._collection = database[collection_name]

    def upsert(self, document: ExternalJobDocument) -> bool:
        payload = document.model_dump(mode="json", by_alias=True)
        created_at = payload.pop("created_at")
        updated_at = payload.pop("updated_at")

        result = self._collection.find_one_and_update(
            {"platform": document.platform, "ejib": document.ejib},
            {
                "$set": payload | {"updated_at": updated_at},
                "$setOnInsert": {"created_at": created_at},
            },
            upsert=True,
            return_document=ReturnDocument.BEFORE,
            projection={"_id": 1},
        )

        return result is None

    def list_external_job_ids(self) -> list[dict[str, str]]:
        return list(
            self._collection.find(
                {},
                {"_id": 0, "platform": 1, "ejib": 1},
                sort=[("platform", ASCENDING), ("ejib", ASCENDING)],
            )
        )
