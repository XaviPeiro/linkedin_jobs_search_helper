from functools import partial

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

import scanners.actions as scanners_actions
from components import notifier_unexpected_openai_response
from domain.command import SeleniumReceiver, LinkedinDiscardJobCommand
from domain.criteria import ICriteria, JobDescriptionOAICriteria
from infraestracture.notifications.fs import FileSystemNotificator
from job_url_builder import SalaryCodes, LocationCodes, RemoteCodes
from logger import app_logger
from openai_api import OpenAIClient
from scanners.linkedin import LinkedinStates, Linkedin, JobsFilter


# TODO P4: yaml is cacota, change it.
import yaml


with open("app_config1.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def config_to_job_filters(file_path: str = "app_config1.yaml") -> list[JobsFilter]:
    with open(file_path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

        # TODO: This return part should be a service on its own, for reusability. However, not necessary for the nonce,
        #  due to this is the only client available.
        return [
            JobsFilter(
                salary=SalaryCodes[c["minimum_salary"]],
                location=LocationCodes[c["location"]],
                search_term=c["search_term"],
                posted_days_ago=c["max_ad_days"],
                remote=[RemoteCodes[c["remote"]]]
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


def init_discard_criteria() -> list[ICriteria]:
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
    chrome: WebDriver = init_bot()

    app_logger.info("Logging into linkedin.")
    linkedin_scrapper = Linkedin(
        web_driver=chrome,
        user=config["user"],
        password=config["password"],
    )
    selenium_receiver = SeleniumReceiver(net_navigator=linkedin_scrapper.web_driver)
    discard_jobs = LinkedinDiscardJobCommand(
        net_navigator=selenium_receiver,
        notifier=notifier_unexpected_openai_response,
        criteria=init_discard_criteria()

    )
    actions = [
        discard_jobs
    ]
    linkedin_scrapper.set_actions(state=LinkedinStates.ACTIVE_JOB_CARD, actions=actions)
    linkedin_scrapper(job_filters=config_to_job_filters(), max_jobs=25)


if __name__ == "__main__":
    main()
