from functools import partial

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

import scanners.actions as scanners_actions
from components import notifier_unexpected_openai_response
from domain.command import SeleniumReceiver, LinkedinDiscardJobCommand
from infraestracture.notifications.fs import FileSystemNotificator
from job_url_builder import SalaryCodes, LocationCodes, RemoteCodes
from logger import app_logger
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


# TODO P2: Handle graceful stop
def main():
    # TODO P4: yaml is cacota, change it.
    import yaml
    with open("app_config1.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    chrome: WebDriver = init_bot()

    system_message = "You're helping me to find a remote IT job, help me to screen job offers."
    openai_client = OpenAIClient.init_with_role(secret=config["openai_api"]["secret"], message=system_message)
    job_filter = JobsFilter(
        salary=SalaryCodes.X80K,
        location=LocationCodes.USA,
        remote=[RemoteCodes.REMOTE],
        posted_days_ago=30,
        search_term="Python Backend Engineer"
    )
    app_logger.info("Logging into linkedin.")

    linkedin_scrapper = Linkedin(
        web_driver=chrome,
        user=config["user"],
        password=config["password"],
        jobs_filter=job_filter
    )

    selenium_receiver = SeleniumReceiver(net_navigator=linkedin_scrapper.web_driver)
    discard_jobs = LinkedinDiscardJobCommand(
        net_navigator=selenium_receiver,
        notifier=notifier_unexpected_openai_response,
        # ask_openai_service=partial(
        #     getattr(scanners_actions, "ask_openai"),
        #     openai_client=openai_client
        # ),
        open_ai_client=openai_client,
        criteria=config["discard_job"]["criteria"]
    )
    actions = [
        # getattr(scanners_actions, "print_job_title"),
        discard_jobs
        # partial(
        #     getattr(scanners_actions, "discard_job"),
        #     apply_criteria=partial(
        #         getattr(scanners_actions, "ask_openai"),
        #         openai_client=openai_client
        #     ),
        #     criteria=config["discard_job"]["criteria"],
        #     notifier=notifier_unexpected_openai_response
        # )
    ]
    linkedin_scrapper.set_actions(state=LinkedinStates.ACTIVE_JOB_CARD, actions=actions)
    linkedin_scrapper()


if __name__ == "__main__":
    main()
