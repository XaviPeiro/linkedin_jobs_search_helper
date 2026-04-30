import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from etl.collected_jobs_ingestion.collected_jobs_parser import iter_json_objects
from etl.collected_jobs_ingestion.models import CollectedJobRow
from etl.collected_jobs_ingestion.normalizer import normalize_external_job


def test_iter_json_objects_reads_jsonl_and_concatenated_objects():
    text = (
        '{"id": 1, "url": "https://example.com/1"}\n'
        '{"id": 2, "url": "https://example.com/2"}'
        '{"id": 3, "url": "https://example.com/3"}'
    )

    items = list(iter_json_objects(text))

    assert [item["id"] for item in items] == [1, 2, 3]


@pytest.mark.parametrize(
    "source_payload",
    [
        {},
        {"id": 1, "url": "not a url", "description": "desc", "title": "title"},
        {"id": 1, "url": "https://example.com", "description": "", "title": "title"},
        {"id": 1, "url": "https://example.com", "description": "desc", "title": " "},
    ],
)
def test_collected_job_row_rejects_invalid_external_data(source_payload):
    with pytest.raises(ValidationError):
        CollectedJobRow.model_validate(source_payload)


def test_normalize_external_job_derives_external_document_fields():
    source_path = Path("collected_jobs/2026-04-28/execution#3.json")
    raw_job = {
        "id": 4407185858,
        "url": (
            "https://www.linkedin.com/jobs/search/?"
            "currentJobId=4407185858&keywords=python%20engineer&location=105072130"
        ),
        "description": (
            "Acerca del empleo\n"
            "Location: Warsaw, hybrid (3 days/office)\n"
            "We are looking for a Software Engineer."
        ),
        "title": "Site Reliability Engineer",
    }

    document = normalize_external_job(source_path, raw_job)

    assert document.platform == "linkedin"
    assert document.ejib == "4407185858"
    assert document.raw_payload == {
        "id": 4407185858,
        "url": (
            "https://www.linkedin.com/jobs/search/?"
            "currentJobId=4407185858&keywords=python%20engineer&location=105072130"
        ),
        "description": raw_job["description"],
        "title": "Site Reliability Engineer",
    }
    assert document.normalized.search_term_used == "python engineer"
    assert document.normalized.date_collected.isoformat() == "2026-04-28"
    assert document.normalized.location == "Warsaw, hybrid (3 days/office)"
    assert document.normalized.salary is None
    assert document.normalized.description_language == "en"


def test_fixture_contains_expected_parseable_jobs(DATASET_PATH):
    rows = list(iter_json_objects(DATASET_PATH.read_text()))

    assert len(rows) > 0
    assert {"id", "url", "description", "title"}.issubset(rows[0])
