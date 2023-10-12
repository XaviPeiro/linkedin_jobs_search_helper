import sys
import time
from dataclasses import field, dataclass
from enum import StrEnum
from functools import partial
from typing import Callable, Optional

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from elements_paths import LoginElements, JobsElements
from job_url_builder import UrlGenerator, SalaryCodes, LocationCodes, RemoteCodes
from logger import app_logger
from scanners.utilities import element_exists


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
@dataclass
class Linkedin:
    web_driver: WebDriver
    user: str
    password: str
    _actions: dict = field(init=False, default_factory=dict)

    def set_actions(self, state: LinkedinStates, actions: list[Callable]):
        self._actions[state] = actions

    def __call__(self, job_filters: list[JobsFilter], max_jobs: Optional[int] = None):
        self._do_login(email=self.user, pw=self.password)
        for job_filter in job_filters:
            self._iterate_jobs(jobs_filter=job_filter, max_jobs=max_jobs)

    def _do_login(self, email: str, pw: str):
        try:
            # TODO P4: Move URL, no magic strings
            self.web_driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            self.web_driver.find_element("id", "username").send_keys(email)
            time.sleep(1)
            self.web_driver.find_element("id", "password").send_keys(pw)
            time.sleep(2.8)
            self.web_driver.find_element("xpath", LoginElements.submit_btn_xpath).click()
            try:
                profile_icon = WebDriverWait(self.web_driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, ".global-nav__me-photo.evi-image.ember-view")
                    ),
                )
            except TimeoutException as timeout_exception:
                """
                    the prev element it has been waited it is to ensure the login was successful.
                    Know reasons for failing are:
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
                app_logger.error(message)
                time.sleep(300)
                # TODO: Detect if pin has been introduced in order to keep with the normal execution.
                sys.exit()
        except Exception as e:
            app_logger.error("Couldn't log in Linkedin! ☠ Check if any intermediate screen appeared and credentials.")
            raise e

    # TODO P2: Split navigation and parse/actions
    # TODO P1: Pass filter attributes
    def _iterate_jobs(self, jobs_filter: JobsFilter, max_jobs: Optional[int] = None):

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
        app_logger.info(f"scanning {len(job_cards)} elements from page {jobs_filter.pagination_offset // 25 + 1}")
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
            app_logger.info("---------------------------------")
            app_logger.info(f"Job number: {index}")
            app_logger.info(f"Job URL: {self.web_driver.current_url}")

            # TODO: Actions can alter the webdriver's state, so the outcome of the following actions. Kurwa macz...
            for action in self._actions[LinkedinStates.ACTIVE_JOB_CARD]:
                action()
                # action(element=self.web_driver.find_element(By.CSS_SELECTOR, "div.scaffold-layout__list-detail-inner"))
                app_logger.info("__ __\n")
            app_logger.info("----------------------------------\n")
        else:
            # next page
            # Apparently, LinkedIn's jobs per page is fixed to 25, so...
            jobs_number = 25
            # TODO: This just works if multiple of 25 (pages), not important rn.
            if jobs_filter.pagination_offset + jobs_number >= max_jobs:
                return None

            jobs_filter.pagination_offset += jobs_number
            self._iterate_jobs(jobs_filter=jobs_filter)



