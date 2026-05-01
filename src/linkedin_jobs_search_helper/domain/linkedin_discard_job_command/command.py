import logging
from dataclasses import dataclass
from typing import ClassVar

from linkedin_jobs_search_helper.domain.command import Command, CrawlerReceiver
from linkedin_jobs_search_helper.domain.criteria import ICriteria
from linkedin_jobs_search_helper.domain.notifier import Notifier

logger = logging.getLogger(__name__)


@dataclass
class LinkedinDiscardJobCommand(Command):
    criteria: list[ICriteria]
    net_navigator: CrawlerReceiver
    notifier: Notifier
    _action_name: ClassVar[str] = "DISCARD JOB"

    def __str__(self):
        return f"Action: {self._action_name}."

    """
        Isn't possible to manually undo the "discard" action, so the btn only appears after clicking discard.
        However, it can be done by requesting to the proper endpoint.
    """
    def __call__(self):
        logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        # TODO: Will be nice to have track of processed elements in order to repeat the same analysis
        #  over the already processed element thus reducing the time it takes and reqs to openai.
        #  !!!NOT IN THIS FUNCTION.!!!!

        job_descr = self.net_navigator.get_job_description()
        # TODO: "criteria" is used as JobDescriptionOAICriteria.criteria (class and yaml) as the different algs to
        #  to discard (JobDescriptionOAICriteria is ne of them, JobDescriptionOAICriteria). CONFUSING.
        for criteria in self.criteria:
            answer: [bool, None] = criteria.apply(entities=[job_descr])[0]
            if answer is True:
                self.net_navigator.linkedin_discard_job()
                logger.info("DISCARDED")
            elif answer is False:
                logger.info("NOT DISCARDED")
            else:
                # The model is returning an unexpected message.
                logger.info("NOT DISCARDED - Because unexpected answer from OPENAI.")
