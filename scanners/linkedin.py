import time
from dataclasses import field, dataclass
from enum import StrEnum
from functools import partial
from typing import Callable

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from elements_paths import LoginElements, JobsElements
from job_url_builder import UrlGenerator
from messaging import print_error, print_relevant_info
from scanners.utilities import element_exists


class LinkedinStates(StrEnum):
    ACTIVE_JOB_CARD = "ACTIVE_JOB_CARD"


@dataclass
class Linkedin:
    web_driver: WebDriver
    user: str
    password: str
    _actions: dict = field(init=False, default_factory=dict)

    # def __init__(self):
    #     ...

    def set_actions(self, state: LinkedinStates, actions: list[Callable]):
        self._actions[state] = actions

    def __call__(self, *args, **kwargs):
        self._do_login(email=self.user, pw=self.password)
        self._iterate_jobs()

    def _do_login(self, email: str, pw: str):
        try:
            # TODO P4: Move URL, no magic strings
            self.web_driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            self.web_driver.find_element("id", "username").send_keys(email)
            time.sleep(3)
            self.web_driver.find_element("id", "password").send_keys(pw)
            time.sleep(3)
            self.web_driver.find_element("xpath", LoginElements.submit_btn_xpath).click()
        except Exception as e:
            print_error("Couldn't log in Linkedin! ☠ Check if any intermediate screen appeared and credentials.")
            raise e

    # TODO P2: Split navigation and parse/actions
    # TODO P1: Pass filter attributes
    def _iterate_jobs(self, start: int = 0):
        url: str = UrlGenerator().generate(start=start)
        self.web_driver.get(url)
        time.sleep(3)

        if element_exists(chrome=self.web_driver, find_arguments=(By.CLASS_NAME, JobsElements.no_results_class)):
            # TODO P3: raise a finish Exception
            return

        time.sleep(4.4)

        job_cards = self.web_driver.find_elements(By.XPATH, JobsElements.all_job_cards_xpath)
        print_relevant_info(f"scanning {len(job_cards)} elements from page {start // 25 + 1}")
        for index, job_card in enumerate(job_cards):
            job_card.click()
            time.sleep(3)
            # STATE: Active job
            print_relevant_info(f"Job number: {index}")
            for action in self._actions[LinkedinStates.ACTIVE_JOB_CARD]:
                if isinstance(action, partial):
                    print_relevant_info(action.func.__name__)
                else:
                    print_relevant_info(f"Action - {action.__name__}")
                action(element=self.web_driver.find_element(By.CSS_SELECTOR, "div.scaffold-layout__list-detail-inner"))
        else:
            # next page
            self._iterate_jobs(start=start + 25)



