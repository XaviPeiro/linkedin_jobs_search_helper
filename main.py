import time

from selenium.common import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver

from elements_paths import LoginElements, JobsElements
from job_url_builder import UrlGenerator


def element_exists(chrome: WebDriver, find_arguments: tuple) -> bool:
    try:
        chrome.find_element(*find_arguments)
    except NoSuchElementException:
        return False
    return True


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


def print_warning(msg):
    print(f"\033[93m{msg}\033[00m")


def print_error(msg):
    print(f"\033[91m{msg}\033[00m")


def print_relevant_info(msg):
    print(f"\033[92m{msg}\033[00m")


def main():
    # TODO P4: yaml is cacota, change it.
    import yaml
    with open("app_config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    chrome: WebDriver = init_bot()
    print_relevant_info("Logging into linkedin.")
    do_login(chrome=chrome, email=config["user"], pw=config["password"])
    jobs_actions(chrome=chrome)


if __name__ == "__main__":
    main()
