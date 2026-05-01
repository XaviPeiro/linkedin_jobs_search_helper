from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from linkedin_jobs_search_helper.jobs.transform_jobs.add_language.conf import ACCEPTED_INPUT_SUFFIX
from linkedin_jobs_search_helper.jobs.transform_jobs.helpers.collected_jobs_parser import (
    iter_collected_job_files,
    iter_json_objects,
)
from linkedin_jobs_search_helper.jobs.transform_jobs.language_detection import LanguageDetector


class AddDescriptionLanguage:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        language_detector: LanguageDetector
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.language_detector = language_detector

    def __call__(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        print("hello2")
        with self.output_path.open("w") as output_file:
            print("hello3")
            for input_file in iter_collected_job_files(self.input_path, ACCEPTED_INPUT_SUFFIX):
                print(input_file)
                print("hello3")
                for job in iter_json_objects(input_file.read_text()):
                    enriched_job = self._add_description_language(job)
                    print(enriched_job)
                    output_file.write(json.dumps(enriched_job, ensure_ascii=False))
                    output_file.write("\n")

    def _add_description_language(self, job: dict[str, Any]) -> dict[str, Any]:
        description = str(job.get("description", ""))
        detected_language = self.language_detector.detect(description)

        return job | {"description_language": detected_language.language}
