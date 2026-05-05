from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from linkedin_jobs_search_helper.common.openai_batch_client import DEFAULT_JOBS_PER_REQUEST
from linkedin_jobs_search_helper.jobs.transform_jobs.add_language.add_description_language import (
    AddDescriptionLanguage,
)
from linkedin_jobs_search_helper.jobs.transform_jobs.add_posting_metadata import (
    AddPostingMetadata,
)
from linkedin_jobs_search_helper.jobs.transform_jobs.create_batch.create_batch import CreateBatch
from linkedin_jobs_search_helper.jobs.transform_jobs.job_selection.__main__ import (
    main as select_jobs,
)
from linkedin_jobs_search_helper.jobs.transform_jobs.language_detection import LanguageDetector
from linkedin_jobs_search_helper.jobs.transform_jobs.remove_duplicates.__main__ import (
    main as remove_duplicates,
)

logger = logging.getLogger(__name__)


class CanonicalPipeline:
    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        instruction_path: Path,
        model: str,
        sources_path: Path | None = None,
        jobs_per_request: int = DEFAULT_JOBS_PER_REQUEST,
    ):
        self.input_path = input_path
        self.output_dir = output_dir
        self.instruction_path = instruction_path
        self.model = model
        self.sources_path = sources_path
        self.jobs_per_request = jobs_per_request

    def __call__(self) -> Path:
        execution_dir = self.output_dir / datetime.now().strftime("%Y%m%d-%H%M%S")
        no_duplicates_path = execution_dir / "01-no-duplicated" / "jobs.jsonl"
        language_path = execution_dir / "02-description-language-added" / "jobs.jsonl"
        metadata_path = execution_dir / "03-posting-metadata-added" / "jobs.jsonl"
        selected_jobs_path = execution_dir / "04-final-jobs-to-evaluate" / "jobs.jsonl"
        batch_dir = execution_dir / "05-openai-batch"

        logger.info(f"Pipeline execution dir: {execution_dir}")

        remove_duplicates(self.input_path, no_duplicates_path)
        AddDescriptionLanguage(
            input_path=no_duplicates_path,
            output_path=language_path,
            language_detector=LanguageDetector(),
        )()
        AddPostingMetadata(
            input_path=language_path,
            output_path=metadata_path,
        )()
        select_jobs(
            input_path=metadata_path,
            output_file_path=selected_jobs_path,
        )
        CreateBatch(
            input_path=selected_jobs_path,
            output_dir=batch_dir,
            instruction=self.instruction_path.read_text(),
            model=self.model,
            sources_path=self.sources_path,
            jobs_per_request=self.jobs_per_request,
        )()

        logger.info(f"Canonical pipeline completed: {execution_dir}")
        return execution_dir
