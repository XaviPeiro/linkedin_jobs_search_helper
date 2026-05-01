from typing import Optional

from linkedin_jobs_search_helper.jobs.extract.scanners.commands.notifier import Notifier


class FakeNotifierMessageExecutor(Notifier):

    def __init__(self):
        ...

    def notify(self, message: str, keys: Optional[list[str]] = None) -> None:
        if keys is None:
            keys = []
