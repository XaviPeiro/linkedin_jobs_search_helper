import logging
import os
from datetime import date
from pathlib import Path
from os import PathLike
from typing import Any

from pydantic import BaseModel, AnyHttpUrl, Field

logger = logging.getLogger(__name__)

class Job(BaseModel):
    id: int
    description: str
    title: str
    url: AnyHttpUrl
    extra_data: dict[str, Any] = Field(default_factory=dict)

class FilePersistence:
    persistence_file_path: Path
    collected_jobs_dir: Path
    items_added: int

    _logs_dir: Path

    def __init__(self, collected_jobs_dir: str | PathLike):
        self.items_added = 0
        self._seen_job_ids: set[int] = set()
        self.collected_jobs_dir = Path(collected_jobs_dir)

        day = str(date.today())
        self._logs_dir = self.collected_jobs_dir / day / 'raw'

        number: int = self._get_files_number(self._logs_dir)
        path = self._logs_dir.joinpath(f"execution#{number}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.persistence_file_path = path

    @staticmethod
    def _get_files_number(path: Path) -> int:
        exists = os.path.exists(path)
        if exists:
            files = os.listdir(path)
            return len(files)
        return 0

    def __call__(self, job: Job):
        if job.id in self._seen_job_ids:
            logger.info(f"Skipping duplicated job id in current execution: {job.id}")
            return

        self._seen_job_ids.add(job.id)
        # TODO: Could be nice to not open/close the file over and over
        with open(self.persistence_file_path, 'a+') as file:
            file.write("\n")
            file.write(job.model_dump_json())

        self.items_added+=1
