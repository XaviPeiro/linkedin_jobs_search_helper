from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.jobs.transform_jobs.add_language.conf import ACCEPTED_INPUT_SUFFIX
from linkedin_jobs_search_helper.jobs.transform_jobs.helpers.collected_jobs_parser import (
    iter_collected_job_files,
    iter_json_objects,
)

logger = logging.getLogger(__name__)


@dataclass
class Filter:
    language: str
    workplace_type: str
    location: str

    def evaluate(self) -> bool:
        if self.language not in ("es", "en"):
            return False

        if self.workplace_type.lower() == "remote":
            return True

        location = self.location.lower()
        return any(
            accepted_location in location
            for accepted_location in ("warsaw", "warszawa", "poland")
        )


def main(input_path: Path, output_file_path: Path | None = None) -> None:
    base_of = input_path.parent if input_path.is_file() else input_path
    output_file_path = output_file_path or base_of / "final_jobs_to_evaluate" / "jobs.jsonl"

    if output_file_path.exists():
        raise FileExistsError(f"Output filepath already exists: {output_file_path}")

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    selected_jobs = 0
    processed_jobs = 0

    with output_file_path.open("w") as output_file:
        for input_file in iter_collected_job_files(input_path, ACCEPTED_INPUT_SUFFIX):
            for job in iter_json_objects(input_file.read_text()):
                processed_jobs += 1
                if _job_filter(job).evaluate():
                    selected_jobs += 1
                    output_file.write(json.dumps(job, ensure_ascii=False))
                    output_file.write("\n")

    logger.info(f"Jobs processed: {processed_jobs}")
    logger.info(f"Jobs selected: {selected_jobs}")
    logger.info(f"Find results in: {output_file_path}")


def _job_filter(job: dict[str, Any]) -> Filter:
    return Filter(
        language=str(job.get("description_language", "")),
        workplace_type=str(_get_workplace_type(job) or ""),
        location=str(job.get("location", "")),
    )


def _get_workplace_type(job: dict[str, Any]) -> str | None:
    workplace_type = job.get("workplace_type")
    if workplace_type is not None:
        return str(workplace_type)

    extra_data = job.get("extra_data")
    if isinstance(extra_data, dict):
        workplace_type = extra_data.get("workplace_type")
        if workplace_type is not None:
            return str(workplace_type)

    return None


if __name__ == "__main__":
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    main(input_path=args.input_path, output_file_path=args.output)
