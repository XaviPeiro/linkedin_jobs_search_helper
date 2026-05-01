import logging
from pathlib import Path
from typing import Any

import yaml
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from linkedin_jobs_search_helper.jobs.extract.scanners.commands.command import SeleniumReceiver, Command
from linkedin_jobs_search_helper.jobs.extract.scanners.commands.criteria import ICriteria, JobDescriptionOAICriteria
from linkedin_jobs_search_helper.jobs.extract.scanners.commands.persist_data_command import PersistDataCommand
from linkedin_jobs_search_helper.jobs.extract.scanners.linkedin.linkedin import JobsFilter, Linkedin, LinkedinStates
import linkedin_jobs_search_helper.jobs.extract.scanners.settings as scanner_settings
from linkedin_jobs_search_helper.jobs.infraestracture.persistance.file_persistance import FilePersistence
from linkedin_jobs_search_helper.jobs.extract.scanners.linkedin.job_url_builder import SalaryCodes, LocationCodes, RemoteCodes
from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.common.openai_api import OpenAIClient
from linkedin_jobs_search_helper.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def load_config(app_config_path: Path) -> dict[str, Any]:
    with app_config_path.open() as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)


def config_to_job_filters(config: dict) -> list[JobsFilter]:
    # TODO: This return part should be a service on its own, for reusability. However, not necessary for the nonce,
    #  due to this is the only client available.
    salary_or_none = lambda d, k: SalaryCodes[d[k]] if k in d else None
    remote_opts = lambda d,k: [RemoteCodes[x] for x in d[k]]
    return [
        JobsFilter(
            salary=salary_or_none(c, "minimum_salary"),
            location=LocationCodes[c["location"]],
            search_term=c["search_term"],
            posted_days_ago=c["max_ad_days"],
            remote=remote_opts(c, "remote"),
            max_jobs=c["max_jobs"],
        ) for c in config["filters"]
    ]


# TODO: Add dependency_injector lib
def init_bot() -> WebDriver:
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("detach", True)
    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def init_discard_criteria(config: dict) -> list[ICriteria]:
    system_message = """
        You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not. 
        Answer exclusively with a "yes" and "no". I do not want you to answer anything else than "yes" or "no", no explanation allowed.
    """
    openai_client = OpenAIClient.init_with_role(secret=config["openai_api"]["secret"], message=system_message)
    return [
        JobDescriptionOAICriteria(open_ai_client=openai_client, criteria=config["discard_job"]["criteria"]),
    ]


# TODO P2: Handle graceful stop
def main():
    settings: Settings = get_settings()
    app_config_path = scanner_settings.SCANNER_ROOT / 'linkedin' / "app_config1.yaml"
    collected_jobs_dir = settings.project_root / "collected_jobs"
    config = load_config(app_config_path)
    configure_logging(log_dir=settings.logs_dir)
    chrome: WebDriver = init_bot()

    logger.info("Logging into linkedin.")
    linkedin_scrapper = Linkedin(
        web_driver=chrome,
        user=config["user"],
        password=config["password"],
    )
    selenium_receiver = SeleniumReceiver(net_navigator=linkedin_scrapper.web_driver)

    persistence_service = FilePersistence(collected_jobs_dir=collected_jobs_dir)
    persist_command = PersistDataCommand(
        net_navigator=selenium_receiver,
        persistence=persistence_service
    )
    actions: list[Command] = [
        persist_command
    ]
    linkedin_scrapper.set_actions(state=LinkedinStates.ACTIVE_JOB_CARD, actions=actions)
    job_filters = config_to_job_filters(config)

    logger.info("""
    ----
    🚀 Starting scrapping:
    ----
    """)
    for jf in job_filters:
        logger.info("############")
        logger.info(jf)
        logger.info("############")

    linkedin_scrapper(job_filters=job_filters)


if __name__ == "__main__":
    main()
