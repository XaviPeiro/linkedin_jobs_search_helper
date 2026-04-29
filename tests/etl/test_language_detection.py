import json
from pathlib import Path

import pytest

from etl.language_detection import LanguageDetector


@pytest.fixture(scope="module")
def collected_jobs(DATASET_PATH ) -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET_PATH.read_text().splitlines()
        if line.strip()
    ]


def job_by_id(collected_jobs: list[dict], linkedin_id: int) -> dict:
    return next(job for job in collected_jobs if job["id"] == linkedin_id)


@pytest.mark.parametrize(
    ("linkedin_id", "expected_language"),
    [
        (4405535832, "en"),
        (4407876913, "en"),
        (4406532643, "en"),
        (4295392081, "en"),
        (4404404150, "pl"),
        (4405544405, "es"),
        (4407403699, "unknown"), # Something using cyrilic
    ],
)
def test_detects_job_description_language_from_collected_jobs(
    collected_jobs: list[dict],
    linkedin_id: int,
    expected_language: str,
):
    detector = LanguageDetector()
    job = job_by_id(collected_jobs, linkedin_id)

    detected_language = detector.detect(job["description"])

    assert detected_language.language == expected_language
    if expected_language == "unknown":
        assert detected_language.confidence == 1.0
    else:
        assert detected_language.confidence > 0


def test_linkedin_spanish_chrome_does_not_override_english_description():
    detector = LanguageDetector()
    description = """
    Acerca del empleo
    We are looking for a backend engineer to join our software engineering team.
    You will build services with Python and work with product teams.
    """

    detected_language = detector.detect(description)

    assert detected_language.language == "en"


def test_unknown_language_for_empty_description():
    detector = LanguageDetector()

    detected_language = detector.detect("")

    assert detected_language.language == "unknown"
    assert detected_language.confidence == 0.0
    assert detected_language.scores == {}
