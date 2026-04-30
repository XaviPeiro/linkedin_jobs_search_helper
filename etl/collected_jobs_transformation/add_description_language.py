from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from etl.collected_jobs_ingestion.collected_jobs_parser import iter_json_objects
from etl.language_detection import LanguageDetector


class AddDescriptionLanguage:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        language_detector: LanguageDetector | None = None,
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.language_detector = language_detector or LanguageDetector()

    def __call__(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.output_path.open("w") as output_file:
            for input_file in self._iter_input_files():
                for job in iter_json_objects(input_file.read_text()):
                    enriched_job = self._add_description_language(job)
                    output_file.write(json.dumps(enriched_job, ensure_ascii=False))
                    output_file.write("\n")

    def _add_description_language(self, job: dict[str, Any]) -> dict[str, Any]:
        description = str(job.get("description", ""))
        detected_language = self.language_detector.detect(description)

        return job | {"description_language": detected_language.language}

    def _iter_input_files(self):
        if self.input_path.is_file():
            yield self.input_path
            return

        for path in sorted(self.input_path.iterdir()):
            if path.is_file() and path.suffix in {".json", ".txt"}:
                yield path
