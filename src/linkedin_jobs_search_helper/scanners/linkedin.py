import logging
import sys
import time
from dataclasses import field, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable, Optional

from selenium.common import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from linkedin_jobs_search_helper.elements_paths import LoginElements, JobsElements
from linkedin_jobs_search_helper.job_url_builder import UrlGenerator, SalaryCodes, LocationCodes, RemoteCodes
from linkedin_jobs_search_helper.scanners.utilities import element_exists

logger = logging.getLogger(__name__)


class LinkedinStates(StrEnum):
    ACTIVE_JOB_CARD = "ACTIVE_JOB_CARD"


@dataclass
class JobsFilter:
    salary: SalaryCodes
    location: LocationCodes
    remote: list[RemoteCodes]
    posted_days_ago: int
    search_term: str
    pagination_offset: int = 0


# TODO P2: Ideally the Crawlers should only gather data, and the data processing should be apart and agnostic.
#  However, if an action (changing state) depends on processing data... I have to think about that.
class Linkedin:
    web_driver: WebDriver
    user: str
    password: str
    _actions: dict

    def __init__(self, web_driver: WebDriver, user: str, password: str):
        self.web_driver = self._create_driver()
        self.user = user
        self.password = password
        self._actions = {}

    def set_actions(self, state: LinkedinStates, actions: list[Callable]):
        self._actions[state] = actions

    @staticmethod
    def _create_driver() -> WebDriver:
        profile_dir = Path.home() / ".selenium-profiles" / "linkedin"

        options = Options()
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")

        # Keep it normal-looking and stable
        options.add_argument("--window-size=1400,1000")
        options.add_argument("--lang=en-US")

        # Do NOT use headless for login-heavy sites
        # options.add_argument("--headless=new")
        driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

        return driver

    def __call__(self, job_filters: list[JobsFilter], max_jobs: int = 1):
        self._do_login(email=self.user, pw=self.password)
        for job_filter in job_filters:

            self._iterate_jobs(jobs_filter=job_filter, max_jobs=max_jobs)

    def _do_login(self, email: str, pw: str):
        try:
            # TODO P4: Move URL, no magic strings
            self.web_driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")

            def login_or_account_picker(driver: WebDriver):
                username_inputs = driver.find_elements(By.ID, "username")
                if username_inputs:
                    return "credentials", username_inputs[0]

                email_matches = driver.find_elements(By.XPATH, f"//p[normalize-space()='{email}']")
                if email_matches:
                    return "account_picker", email_matches[0]

                return False

            login_mode, login_target = WebDriverWait(self.web_driver, timeout=300).until(login_or_account_picker)

            if login_mode == "account_picker":
                account_selector = WebDriverWait(self.web_driver, timeout=30).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, f"//p[normalize-space()='{email}']/ancestor::div[@role='button'][1]")
                    )
                )
                self.web_driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    account_selector,
                )
                try:
                    account_selector.click()
                except Exception:
                    self.web_driver.execute_script("arguments[0].click();", account_selector)
            else:
                username_input: WebElement = login_target
                username_input.clear()
                username_input.send_keys(email)

                time.sleep(1)

                self.web_driver.find_element("id", "password").send_keys(pw)
                time.sleep(2.8)
                self.web_driver.find_element("xpath", LoginElements.submit_btn_xpath).click()

            try:
                profile_icon = WebDriverWait(self.web_driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "#job-medium")
                    ),
                )
            except TimeoutException as timeout_exception:
                """
                    The prev element has been awaited it is to ensure the login was successful.
                    Known reasons for failing are:
                        - It is asking for a pin code that it is sent to the users email. It can be entered manually,
                            and it is only requested once (as long as I know).
                """
                # self.web_driver.find_element(By.ID, "input__email_verification_pin")
                input_add_pin = WebDriverWait(self.web_driver, 5).until(
                    expected_conditions.presence_of_element_located((By.ID, "input__email_verification_pin")),
                )
                # If no exception it means it has been found and pin has to be introduced.
                message = """📢📢📢READ ME📢📢📢
                You need to introduce a pin. Run this program enabling the UI web driver and introduce the pin you 
                got in your email in the browser instance, submit it and rerun the program. You have 5 minutes to do it, 
                after those 5 min the program will end. If you got no time, rerun the program and you will get another 
                chance.
                !!IT WILL BE NECESSARY ONLY ONCE!!
                """
                logger.error(message)
                time.sleep(300)
                # TODO: Detect if pin has been introduced in order to keep with the normal execution.
                sys.exit()
        except Exception as e:
            logger.error("Couldn't log in Linkedin! ☠ Check if any intermediate screen appeared and credentials.")
            raise e

    # TODO P2: Split navigation and parse/actions
    # TODO P1: Pass filter attributes
    def _iterate_jobs(self, jobs_filter: JobsFilter, max_jobs: int):
        if max_jobs <= 0:
            return

        url: str = UrlGenerator().generate(
            search_term=jobs_filter.search_term,
            salary=jobs_filter.salary,
            location=jobs_filter.location,
            posted_days_ago=jobs_filter.posted_days_ago,
            remote=jobs_filter.remote,
            start=jobs_filter.pagination_offset
        )
        self.web_driver.get(url)
        time.sleep(3)

        if element_exists(chrome=self.web_driver, find_arguments=(By.CLASS_NAME, JobsElements.no_results_class)):
            # TODO P3: raise a finish Exception
            return

        time.sleep(4.4)

        # TODO: ¿Iterate view items in the commands and just using crawlers to request data?
        job_cards = self.web_driver.find_elements(By.XPATH, JobsElements.all_not_dismissed_job_cards_xpath)
        logger.info(f"scanning {len(job_cards)} elements from page {jobs_filter.pagination_offset // 25 + 1}")
        job_card: WebElement
        for index, job_card in enumerate(reversed(job_cards)):
            # If it is the first element (the last on the document) the click is not fully working on the first click
            # (probably due to it is not fully loaded and requires to scroll). This is a shitty but working solution.
            # Let's keep move and look for something more adequate later.
            job_card.click()
            if index == 0:
                job_card.click()
            time.sleep(3)

            # STATE: Active job
            logger.info("---------------------------------")
            logger.info(f"Job number: {index}")
            logger.info(f"Job URL: {self.web_driver.current_url}")

            WebDriverWait(self.web_driver, timeout=30).until(
                expected_conditions.presence_of_element_located((By.ID, "job-details"))
            )

            # TODO: Actions can alter the webdriver's state, so the outcome of the following actions. Kurwa macz...
            for action in self._actions[LinkedinStates.ACTIVE_JOB_CARD]:
                action()
                # action(element=self.web_driver.find_element(By.CSS_SELECTOR, "div.scaffold-layout__list-detail-inner"))
                logger.info("__ __\n")
            logger.info("----------------------------------\n")
        else:
            # next page
            # Apparently, LinkedIn's jobs per page is fixed to 25, so...
            jobs_number = 25
            # This just works if multiple of 25 (pages), not important rn.
            # if jobs_filter.pagination_offset + jobs_number >= max_jobs:
            #     return None

            # TODO: Deshacer recursive approach

            jobs_filter.pagination_offset += jobs_number
            next_max_jobs = max(max_jobs-jobs_number, 0)
            self._iterate_jobs(jobs_filter=jobs_filter, max_jobs=next_max_jobs)
