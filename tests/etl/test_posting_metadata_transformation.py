import json
from datetime import date
from pathlib import Path
import shutil

from linkedin_jobs_search_helper.jobs.transform_jobs.add_posting_metadata import AddPostingMetadata
from linkedin_jobs_search_helper.jobs.transform_jobs.add_posting_metadata.__main__ import main
from linkedin_jobs_search_helper.jobs.transform_jobs.add_posting_metadata.add_posting_metadata import (
    parse_posting_metadata,
)

RAW_LINKEDIN_JOBS_FIXTURE = Path("tests/test_datasets/linkedin_raw_extra_data_2026-05-02.jsonl")


def test_add_posting_metadata_reads_latest_raw_jobs_and_persists_one_output(tmp_path):
    output_file = tmp_path / "2-posting-metadata-added" / "jobs.json"
    AddPostingMetadata(
        input_path=RAW_LINKEDIN_JOBS_FIXTURE,
        output_path=output_file,
        reference_date=date(2026, 5, 2),
    )()

    transformed_jobs = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]
    transformed_jobs_by_id = {job["id"]: job for job in transformed_jobs}

    assert len(transformed_jobs) == 25
    assert transformed_jobs_by_id[4409802662]["location"] == "Germany"
    assert transformed_jobs_by_id[4409802662]["date_posted"] == "2026-05-02"
    assert transformed_jobs_by_id[4409802662]["applicants"] == 4
    assert transformed_jobs_by_id[4404994547]["location"] == "Letterkenny, County Donegal, Ireland"
    assert transformed_jobs_by_id[4404994547]["date_posted"] == "2026-05-02"
    assert transformed_jobs_by_id[4404994547]["applicants"] == 80
    assert transformed_jobs_by_id[4398194753]["location"] == "Hamburg, Hamburg, Germany"
    assert transformed_jobs_by_id[4398194753]["date_posted"] == "2026-05-02"
    assert transformed_jobs_by_id[4398194753]["applicants"] == 100


def test_add_posting_metadata_main_uses_default_output_with_real_raw_jobs(tmp_path):
    raw_jobs_dir = tmp_path / "collected_jobs" / "2026-05-02" / "raw"
    raw_jobs_dir.mkdir(parents=True)
    shutil.copy(RAW_LINKEDIN_JOBS_FIXTURE, raw_jobs_dir / "execution#0.jsonl")

    main(input_path=raw_jobs_dir)

    output_file = raw_jobs_dir / "2-posting-metadata-added" / "jobs.json"
    transformed_jobs = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]

    assert len(transformed_jobs) == 25
    assert transformed_jobs[0]["location"] == "Germany"
    assert transformed_jobs[0]["applicants"] == 4


def test_parse_posting_metadata_accepts_spanish_relative_date():
    metadata = parse_posting_metadata(
        "Bucarest, Rumania · Publicado de nuevo hace 1 semana · 47 solicitudes",
        reference_date=date(2026, 5, 2),
    )

    assert metadata.location == "Bucarest, Rumania"
    assert metadata.date_posted == date(2026, 4, 25)
    assert metadata.applicants == 47


def test_parse_posting_metadata_returns_null_fields_when_extra_data_is_missing():
    metadata = parse_posting_metadata(None, reference_date=date(2026, 5, 2))

    assert metadata.location is None
    assert metadata.date_posted is None
    assert metadata.applicants is None


def test_parse_posting_metadata_skips_non_numeric_applicant_segments():
    metadata = parse_posting_metadata(
        "Bucharest, Romania · Reposted 1 week ago · Actively reviewing applicants · 47 applicants",
        reference_date=date(2026, 5, 2),
    )

    assert metadata.applicants == 47
