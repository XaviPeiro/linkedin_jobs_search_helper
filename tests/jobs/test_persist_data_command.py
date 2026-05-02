from linkedin_jobs_search_helper.jobs.extract.scanners.commands.command import CrawlerReceiver
from linkedin_jobs_search_helper.jobs.extract.scanners.commands.persist_data_command.command import PersistDataCommand


class FakeCrawlerReceiver(CrawlerReceiver):
    def linkedin_discard_job(self):
        pass

    def get_job_description(self) -> str:
        return "A job description"

    def get_job_title(self) -> str:
        return "Python Engineer"

    def get_url(self) -> str:
        return "https://www.linkedin.com/jobs/view/123/"

    def get_job_id(self) -> str:
        return "123"

    def get_extra_data(self) -> dict:
        return {
            "top_card_tertiary_description": (
                "Bucarest, Rumania · Publicado de nuevo hace 1 semana · 47 solicitudes"
            )
        }


class FakePersistence:
    def __init__(self):
        self.jobs = []

    def __call__(self, job):
        self.jobs.append(job)


def test_persist_data_command_includes_extra_data():
    persistence = FakePersistence()
    command = PersistDataCommand(
        net_navigator=FakeCrawlerReceiver(),
        persistence=persistence,
    )

    command()

    assert persistence.jobs[0].extra_data == {
        "top_card_tertiary_description": (
            "Bucarest, Rumania · Publicado de nuevo hace 1 semana · 47 solicitudes"
        )
    }
