from functools import partial

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

import scanners.actions as scanners_actions
from infraestracture.notifications.fs import FileSystemNotificator
from job_url_builder import SalaryCodes, LocationCodes, RemoteCodes
from messaging import print_relevant_info
from openai_api import OpenAIClient
from scanners.linkedin import LinkedinStates, Linkedin, JobsFilter


def init_bot() -> WebDriver:
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("detach", True)
    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def main():
    # TODO P4: yaml is cacota, change it.
    import yaml
    with open("app_config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    chrome: WebDriver = init_bot()
    notificator = FileSystemNotificator(filepath="logs/openai_unexpected_responses.txt")

    system_message = "You're helping me to find a remote IT job. I live in Poland, Europe. "
    openai_client = OpenAIClient.init_with_role(secret=config["openai_api"]["secret"], message=system_message)
    job_filter = JobsFilter(
        salary=SalaryCodes.X80K,
        location=LocationCodes.USA,
        remote=[RemoteCodes.REMOTE],
        posted_days_ago=14
    )
    print_relevant_info("Logging into linkedin.")

    linkedin_scrapper = Linkedin(
        web_driver=chrome,
        user=config["user"],
        password=config["password"],
        jobs_filter=job_filter
    )
    actions = [
        getattr(scanners_actions, "print_job_title"),
        partial(
            getattr(scanners_actions, "discard_job"),
            openai_client=openai_client,
            criteria=config["discard_job"]["criteria"],
            notificator=notificator
        )
    ]
    linkedin_scrapper.set_actions(state=LinkedinStates.ACTIVE_JOB_CARD, actions=actions)
    linkedin_scrapper()


# TODO P1: Use config files
if __name__ == "__main__":
    main()
