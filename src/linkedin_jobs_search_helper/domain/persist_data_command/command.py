import logging
from dataclasses import dataclass
from typing import ClassVar

from linkedin_jobs_search_helper.domain.command import Command, CrawlerReceiver
from linkedin_jobs_search_helper.infraestracture.persistance.file_persistance import FilePersistence, Job

logger = logging.getLogger(__name__)


@dataclass
class PersistDataCommand(Command):
    net_navigator: CrawlerReceiver
    _action_name: ClassVar[str] = "Persist Jobs"
    persistence: FilePersistence

    def __str__(self):
        return f"Action: {self._action_name}."

    def __call__(self, *args, **kwargs):
        logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        job: Job = Job.model_validate_strings(
            {
                "id": self.net_navigator.get_job_id(),
                "url": self.net_navigator.get_url(),
                "description": self.net_navigator.get_job_description(),
                "title": self.net_navigator.get_job_title(),
            }
        )
        self.persistence(job)
