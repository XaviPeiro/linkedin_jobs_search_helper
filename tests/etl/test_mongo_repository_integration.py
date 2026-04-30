from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from etl.collected_jobs_ingestion.models import ExternalJobDocument, NormalizedJob
from etl.collected_jobs_ingestion.mongo_repository import ExternalJobsRepository, ensure_external_jobs_indexes


MONGO_URI = "mongodb://external_jobs:external_jobs@localhost:27018/external_jobs"


@pytest.fixture()
def mongo_database():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        pytest.skip("MongoDB is not available on localhost:27018")

    database = client["external_jobs"]
    collection_name = f"external_jobs_test_{uuid4().hex}"
    ensure_external_jobs_indexes(database, collection_name=collection_name)

    try:
        yield database, collection_name
    finally:
        database.drop_collection(collection_name)
        client.close()


def make_document(title: str = "Python Engineer") -> ExternalJobDocument:
    now = datetime.now(timezone.utc)
    return ExternalJobDocument(
        platform="linkedin",
        ejib="4405535832",
        raw_payload={
            "id": 4405535832,
            "url": "https://www.linkedin.com/jobs/search/?currentJobId=4405535832",
            "description": "We are looking for a Python Engineer.",
            "title": title,
        },
        normalized=NormalizedJob(
            title=title,
            descr="We are looking for a Python Engineer.",
            url="https://www.linkedin.com/jobs/search/?currentJobId=4405535832",
            description_language="en",
            location=None,
            salary=None,
            search_term_used="python engineer",
            date_collected="2026-04-29",
        ),
        created_at=now,
        updated_at=now,
    )


def test_mongo_repository_upserts_without_duplicate_jobs(mongo_database):
    database, collection_name = mongo_database
    repository = ExternalJobsRepository(database, collection_name=collection_name)

    assert repository.upsert(make_document("Python Engineer")) is True
    assert repository.upsert(make_document("Senior Python Engineer")) is False

    collection = database[collection_name]
    stored_documents = list(collection.find({}, {"_id": 0}))

    assert len(stored_documents) == 1
    assert stored_documents[0]["platform"] == "linkedin"
    assert stored_documents[0]["ejib"] == "4405535832"
    assert stored_documents[0]["normalized"]["title"] == "Senior Python Engineer"


def test_mongo_repository_lists_external_job_ids(mongo_database):
    database, collection_name = mongo_database
    repository = ExternalJobsRepository(database, collection_name=collection_name)
    repository.upsert(make_document())

    external_ids = repository.list_external_job_ids()

    assert external_ids == [{"platform": "linkedin", "ejib": "4405535832"}]


def test_mongo_indexes_are_created(mongo_database):
    database, collection_name = mongo_database
    index_names = set(database[collection_name].index_information())

    assert "external_jobs_platform_ejib_unique" in index_names
    assert "external_jobs_description_language" in index_names
    assert "external_jobs_search_term_used" in index_names
    assert "external_jobs_text_search" in index_names
