import time
from functools import partial

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from elements_paths import LoginElements, JobsElements
from infraestracture.notifications.fs import FileSystemNotificator
from job_url_builder import UrlGenerator
from messaging import print_error, print_relevant_info
from openai_api import OpenAIClient
from scanners.linkedin import LinkedinStates, Linkedin
from scanners.utilities import element_exists
import scanners.actions as scanners_actions


def init_bot() -> WebDriver:
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("detach", True)
    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def do_login(chrome, email, pw):
    try:
        # TODO P4: Move URL, no magic strings
        chrome.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        chrome.find_element("id", "username").send_keys(email)
        time.sleep(3)
        chrome.find_element("id", "password").send_keys(pw)
        time.sleep(3)
        chrome.find_element("xpath", LoginElements.submit_btn_xpath).click()
    except Exception as e:
        print_error("Couldn't log in Linkedin! ☠ Check if any intermediate screen appeared and credentials.")
        raise e


# TODO P2: Split navigation and parse/actions
# TODO P1: Use config files
def jobs_actions(chrome: WebDriver, start: int = 0):
    url: str = UrlGenerator().generate(start=start)
    chrome.get(url)
    time.sleep(3)

    if element_exists(chrome=chrome, find_arguments=(By.CLASS_NAME, JobsElements.no_results_class)):
        # TODO P3: raise a finish Exception
        return

    time.sleep(4.4)

    job_cards = chrome.find_elements(By.XPATH, JobsElements.all_job_cards_xpath)
    print_relevant_info(f"scanning {len(job_cards)} elements from page {start // 25 + 1}")
    for index, job_card in enumerate(job_cards):
        job_card.click()
        time.sleep(3)
        job_title = job_card.find_element(By.CLASS_NAME, "job-card-list__title")
        print_relevant_info(f"{index} - {job_title.text}")
    else:
        # next page
        jobs_actions(chrome=chrome, start=start+25)


def main():
    # TODO P4: yaml is cacota, change it.
    import yaml
    with open("app_config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    chrome: WebDriver = init_bot()
    notificator = FileSystemNotificator(filepath="logs/openai_unexpected_responses.txt")

    system_message = "You're helping me to find a remote IT job. I live in Poland, Europe. "
    openai_client = OpenAIClient.init_with_role(secret=config["openai_api"]["secret"], message=system_message)
    print_relevant_info("Logging into linkedin.")

    linkedin_scrapper = Linkedin(web_driver=chrome, user=config["user"], password=config["password"])
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

    # do_login(chrome=chrome, email=config["user"], pw=config["password"])
    # jobs_actions(chrome=chrome)


# TODO P1: Use config files
if __name__ == "__main__":
    main()

"""
main
    linkedin(config)
        do_login(config.user, config.psw)
        jobs(config)
            config.jobs_tasks
        
"""